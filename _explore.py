from bs4 import BeautifulSoup
import os, glob

# Explore one author page
f = open("Crawled_Data/author_asalpan.html", encoding="utf-8")
soup = BeautifulSoup(f.read(), "html.parser")

# Find author name
h2s = soup.find_all("h2")
print("=== H2 tags ===")
for h in h2s[:3]:
    print(f"  {h.text.strip()[:100]}")

# Find article cards/links
print("\n=== Cards ===")
cards = soup.select(".card")
print(f"  Found {len(cards)} cards")
for c in cards[:3]:
    title = c.select_one(".card-title, h5, h4, h3")
    link = c.select_one("a[href]")
    if title:
        print(f"  Title: {title.text.strip()[:80]}")
    if link:
        print(f"  Link: {link.get('href','')[:100]}")
    print()

# Find all links that look like articles
print("\n=== Article-like links ===")
links = soup.select("a[href]")
for a in links:
    href = a.get("href", "")
    text = a.text.strip()
    if "katmanportal.com" in href and text and len(text) > 20:
        skip = any(x in href for x in ["author", "category", "tag", "page_", "yazarlar", "#", "newsletter", "hakkimizda", "iletisim", "cerez", "gizlilik", "kullanim", "yayin-ilkeleri", "yaziyukle", "abonelik", "yapay-zeka-kullanim", "soylesiler"])
        if not skip:
            print(f"  {text[:80]} -> {href}")

# Now check an actual article page
print("\n\n=== Article page structure ===")
art_files = [f for f in os.listdir("Crawled_Data") if not f.startswith(("author_", "category_", "tag_", "index", "yazarlar", "newsletter", "hakkimizda", "iletisim", "cerez", "gizlilik", "kullanim", "yayin", "yaziyukle", "abonelik", "yapay-zeka-kull", "soylesiler", "tr_", "2026"))]
print(f"  Potential article files: {len(art_files)}")
for af in art_files[:3]:
    print(f"\n  --- {af} ---")
    s2 = BeautifulSoup(open(f"Crawled_Data/{af}", encoding="utf-8").read(), "html.parser")
    h1 = s2.find("h1")
    if h1:
        print(f"  H1: {h1.text.strip()[:100]}")
    author_el = s2.select_one(".author, .meta-author, .entry-author, [rel=author]")
    if author_el:
        print(f"  Author: {author_el.text.strip()[:100]}")
    # Try to find author from meta or links
    author_links = s2.select('a[href*="author"]')
    for al in author_links[:3]:
        print(f"  Author link: {al.text.strip()[:50]} -> {al.get('href','')[:80]}")
