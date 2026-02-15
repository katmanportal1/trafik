"""
Katman Portal Hybrid Crawler
Seeds from sitemap + BFS internal link following
"""
import asyncio
import aiohttp
import pandas as pd
from bs4 import BeautifulSoup
import time
import os
from urllib.parse import urlparse, urljoin, urldefrag
import logging
import xml.etree.ElementTree as ET

BASE_URL = "https://katmanportal.com/"
OUTPUT_DIR = "Crawled_Data"
MAX_PAGES = 2000
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}
SKIP_EXT = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.zip', '.rar', '.mp4', '.svg', '.webp', '.ico', '.css', '.js', '.woff', '.woff2', '.ttf'}

os.makedirs(OUTPUT_DIR, exist_ok=True)
logging.basicConfig(filename='crawler.log', level=logging.INFO, format='%(asctime)s - %(message)s')


def normalize_url(url):
    """Normalize URL to prevent duplicates."""
    parsed = urlparse(url)
    path = parsed.path
    if path and not path.endswith('/') and '.' not in path.split('/')[-1]:
        path += '/'
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def extract_links(html, page_url):
    """Extract normalized internal links from HTML."""
    soup = BeautifulSoup(html, 'html.parser')
    links = set()
    base_host = urlparse(BASE_URL).netloc

    for a in soup.find_all('a', href=True):
        href = a['href']
        full = urljoin(page_url, href)
        full, _ = urldefrag(full)
        p = urlparse(full)
        if p.netloc == base_host:
            ext = os.path.splitext(p.path)[1].lower()
            if ext not in SKIP_EXT:
                links.add(normalize_url(full))
    return links


def extract_meta(html):
    """Extract title, category, author, description from HTML."""
    soup = BeautifulSoup(html, 'html.parser')
    
    title = ""
    t = soup.find('title')
    if t:
        title = t.get_text(strip=True)
    elif soup.find('meta', property='og:title'):
        title = soup.find('meta', property='og:title').get('content', '')

    category = ""
    sec = soup.find('meta', property='article:section')
    if sec:
        category = sec.get('content', '')
    else:
        cats = soup.find_all('a', rel='category tag')
        if cats:
            category = ', '.join(c.get_text(strip=True) for c in cats)

    author = ""
    am = soup.find('meta', attrs={'name': 'author'})
    if am:
        author = am.get('content', '')
    else:
        al = soup.find('a', rel='author')
        if al:
            author = al.get_text(strip=True)

    description = ""
    dm = soup.find('meta', attrs={'name': 'description'})
    if dm:
        description = dm.get('content', '')
    elif soup.find('meta', property='og:description'):
        description = soup.find('meta', property='og:description').get('content', '')

    return title, category, author, description


def url_to_filename(url):
    """Convert URL to a safe filename based on path."""
    path = urlparse(url).path.strip('/')
    if not path:
        return "index.html"
    return path.replace('/', '_') + ".html"


async def get_sitemap_seeds(session):
    """Fetch all URLs from sitemap hierarchy."""
    seeds = set()
    try:
        async with session.get(BASE_URL + "sitemap.xml", timeout=aiohttp.ClientTimeout(total=30)) as resp:
            if resp.status != 200:
                print(f"  Sitemap fetch failed: HTTP {resp.status}")
                return seeds
            xml_text = await resp.text()

        root = ET.fromstring(xml_text)
        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

        # Check for sitemap index
        sub_locs = [s.text for s in root.findall('.//sm:sitemap/sm:loc', ns)]
        if sub_locs:
            print(f"  Sitemap index with {len(sub_locs)} sub-sitemaps")
            for sm_url in sub_locs:
                print(f"    Fetching: {sm_url}")
                try:
                    async with session.get(sm_url, timeout=aiohttp.ClientTimeout(total=30)) as resp2:
                        if resp2.status == 200:
                            sm_xml = await resp2.text()
                            sm_root = ET.fromstring(sm_xml)
                            urls = [u.text for u in sm_root.findall('.//sm:url/sm:loc', ns)]
                            seeds.update(normalize_url(u) for u in urls)
                            print(f"      -> {len(urls)} URLs")
                except Exception as e:
                    print(f"      -> Error: {e}")
                await asyncio.sleep(0.2)
        else:
            # Direct URL list
            urls = [u.text for u in root.findall('.//sm:url/sm:loc', ns)]
            seeds.update(normalize_url(u) for u in urls)

    except Exception as e:
        print(f"  Sitemap error: {e}")
    
    return seeds


async def crawl():
    """Main hybrid crawl: sitemap seeds + BFS link following."""
    print(f"{'='*60}")
    print(f"KATMAN PORTAL HYBRID CRAWLER")
    print(f"{'='*60}")
    print(f"Output: {os.path.abspath(OUTPUT_DIR)}\n")

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        # Phase 1: Sitemap seeds
        print("[Phase 1] Collecting seed URLs from sitemap...")
        seeds = await get_sitemap_seeds(session)
        seeds.add(normalize_url(BASE_URL))
        print(f"  Total seed URLs: {len(seeds)}\n")

        # Phase 2: BFS crawl
        print("[Phase 2] BFS crawl (sitemap seeds + internal links)...")
        visited = set()
        queue = list(seeds)
        results = []

        while queue and len(visited) < MAX_PAGES:
            url = normalize_url(queue.pop(0))
            if url in visited:
                continue

            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=45)) as resp:
                    ct = resp.headers.get('Content-Type', '').lower()
                    if resp.status != 200 or 'text/html' not in ct:
                        visited.add(url)
                        continue
                    html = await resp.text()
            except Exception as e:
                logging.error(f"Fetch error {url}: {e}")
                visited.add(url)
                continue

            visited.add(url)
            idx = len(visited)

            # Save HTML
            fname = url_to_filename(url)
            fpath = os.path.join(OUTPUT_DIR, fname)
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(html)

            # Extract metadata
            title, category, author, desc = extract_meta(html)

            # Extract and queue internal links
            new_links = extract_links(html, url)
            added = 0
            for link in new_links:
                if link not in visited and link not in queue:
                    queue.append(link)
                    added += 1

            results.append({
                'id': idx,
                'url': url,
                'file': fname,
                'title': title,
                'category': category,
                'author': author,
                'description': desc,
                'path': urlparse(url).path,
                'from_sitemap': url in seeds,
                'links_found': len(new_links),
                'new_links_added': added
            })

            print(f"  [{idx}] {fname}  (links: {len(new_links)}, new: {added})")
            await asyncio.sleep(0.5)

    # Save index
    df = pd.DataFrame(results)
    df.to_excel("katman_crawled_index.xlsx", index=False)

    print(f"\n{'='*60}")
    print(f"CRAWL COMPLETE")
    print(f"{'='*60}")
    print(f"  Pages crawled : {len(results)}")
    print(f"  From sitemap  : {df['from_sitemap'].sum() if len(df) else 0}")
    print(f"  From links    : {(~df['from_sitemap']).sum() if len(df) else 0}")
    print(f"  Categories    : {df['category'].nunique() if len(df) else 0}")
    print(f"  Authors       : {df['author'].nunique() if len(df) else 0}")
    print(f"  Queue remain  : {len(queue)}")
    print(f"  Index saved   : katman_crawled_index.xlsx")


if __name__ == "__main__":
    t0 = time.time()
    asyncio.run(crawl())
    print(f"\nTotal time: {time.time()-t0:.1f}s")
