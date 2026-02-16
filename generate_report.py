"""
Katman Portal - GA4 Dashboard Generator
Generates HTML dashboard pages with Plotly charts and Bootstrap UI.
Saves all data to exported_data/ before generating HTML.
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from analytics_helper import AnalyticsHelper
from datetime import datetime, timedelta
import os
import calendar
import glob
from bs4 import BeautifulSoup

class ReportGenerator:
    def __init__(self):
        self.helper = AnalyticsHelper()
        self.output_dir = "dashboard"
        os.makedirs(self.output_dir, exist_ok=True)

        # Load crawled index for author lookup
        self.index_df = None
        index_path = os.path.join(os.path.dirname(__file__), "katman_crawled_index.xlsx")
        if os.path.exists(index_path):
            self.index_df = pd.read_excel(index_path)

        # Katman Portal category groups
        self.groups = [
            {"name": "Güncel", "prefix": "/category/guncel"},
            {"name": "Türkiye", "prefix": "/category/turkiye"},
            {"name": "Dünya", "prefix": "/category/dunya"},
            {"name": "Tarih", "prefix": "/category/tarih"},
            {"name": "Teori", "prefix": "/category/teori"},
            {"name": "Metod", "prefix": "/category/metod"},
            {"name": "Makro Politika", "prefix": "/category/makro-politika"},
            {"name": "Eşitsizlik", "prefix": "/category/esitsizlik"},
            {"name": "Sanayi", "prefix": "/category/sanayi"},
            {"name": "Sosyal Politika", "prefix": "/category/sosyalpolitika"},
        ]

        # Turkey city coordinates for map
        self.city_coords = {
            "Istanbul": {"lat": 41.0082, "lon": 28.9784},
            "Ankara": {"lat": 39.9334, "lon": 32.8597},
            "Izmir": {"lat": 38.4237, "lon": 27.1428},
            "Bursa": {"lat": 40.1828, "lon": 29.0665},
            "Antalya": {"lat": 36.8969, "lon": 30.7133},
            "Adana": {"lat": 37.0000, "lon": 35.3213},
            "Konya": {"lat": 37.8667, "lon": 32.4833},
            "Gaziantep": {"lat": 37.0662, "lon": 37.3833},
            "Mersin": {"lat": 36.8000, "lon": 34.6333},
            "Kayseri": {"lat": 38.7312, "lon": 35.4787},
            "Diyarbakir": {"lat": 37.9144, "lon": 40.2306},
            "Eskisehir": {"lat": 39.7667, "lon": 30.5256},
            "Trabzon": {"lat": 41.0027, "lon": 39.7168},
            "Samsun": {"lat": 41.2867, "lon": 36.33},
            "Denizli": {"lat": 37.7765, "lon": 29.0864},
            "Sanliurfa": {"lat": 37.1591, "lon": 38.7969},
            "Malatya": {"lat": 38.3552, "lon": 38.3095},
            "Kahramanmaras": {"lat": 37.5858, "lon": 36.9371},
            "Van": {"lat": 38.4891, "lon": 43.4089},
            "Erzurum": {"lat": 39.9000, "lon": 41.2700},
            "Kocaeli": {"lat": 40.8533, "lon": 29.8815},
            "Sakarya": {"lat": 40.7569, "lon": 30.3783},
            "Mugla": {"lat": 37.2153, "lon": 28.3636},
            "Hatay": {"lat": 36.4018, "lon": 36.3498},
            "Manisa": {"lat": 38.6191, "lon": 27.4289},
            "Balikesir": {"lat": 39.6484, "lon": 27.8826},
            "Aydin": {"lat": 37.8444, "lon": 27.8458},
            "Tekirdag": {"lat": 40.9833, "lon": 27.5167},
        }

        self.months_map = {
            1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran",
            7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
        }

    # ─── SIDEBAR ────────────────────────────────────────────
    def _create_sidebar_html(self):
        current_year = datetime.now().year
        current_month = datetime.now().month

        head = """
        <style>
            .scroll-to-top { position: fixed; bottom: 20px; right: 20px; display: none; z-index: 1000; }
            .sidebar-link { text-decoration: none; color: #333; display: block; padding: 5px 10px; }
            .sidebar-link:hover { background-color: #f0f0f0; border-radius: 5px; }
            .accordion-button:not(.collapsed) { background-color: #e7f1ff; color: #0c63e4; }
        </style>
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                var btn = document.createElement('button');
                btn.className = 'btn btn-primary rounded-circle scroll-to-top p-3';
                btn.innerHTML = '↑';
                document.body.appendChild(btn);
                window.onscroll = function() {
                    btn.style.display = (document.documentElement.scrollTop > 300) ? 'block' : 'none';
                };
                btn.onclick = function() { window.scrollTo({top: 0, behavior: 'smooth'}); };
            });
        </script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        """

        html = head + """
        <div class="offcanvas offcanvas-start" tabindex="-1" id="offcanvasSidebar">
            <div class="offcanvas-header bg-light border-bottom">
                <h5 class="offcanvas-title fw-bold text-primary">Katman Portal Analiz</h5>
                <button type="button" class="btn-close" data-bs-dismiss="offcanvas"></button>
            </div>
            <div class="offcanvas-body p-0">
                <div class="list-group list-group-flush mb-3">
                    <a href="bugun.html" class="list-group-item list-group-item-action fw-bold text-danger">
                        <i class="fas fa-bolt me-2"></i> Bugün (Canlı)
                    </a>
                    <a href="son30gun.html" class="list-group-item list-group-item-action fw-bold text-primary">
                        <i class="fas fa-chart-line me-2"></i> Son 30 Gün
                    </a>
                    <a href="yazarlar_stats.html" class="list-group-item list-group-item-action fw-bold text-success">
                        <i class="fas fa-users me-2"></i> Yazar İstatistikleri
                    </a>
                </div>
                <h6 class="text-uppercase text-muted fw-bold px-3 mt-3 small">Yıllık Arşivler</h6>
                <div class="accordion accordion-flush" id="accordionSidebar">
        """

        for year in range(current_year, 2025, -1):
            collapse_id = f"collapseYear{year}"
            html += f"""
                <div class="accordion-item">
                    <h2 class="accordion-header">
                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#{collapse_id}">
                            <strong>{year} Genel Bakış</strong>
                        </button>
                    </h2>
                    <div id="{collapse_id}" class="accordion-collapse collapse" data-bs-parent="#accordionSidebar">
                        <div class="accordion-body p-0">
                            <div class="list-group list-group-flush">
                                <a href="katman_dashboard_{year}.html" class="list-group-item list-group-item-action bg-light fw-bold ps-4">
                                    <i class="fas fa-globe me-2"></i> {year} Özeti
                                </a>
            """
            end_month = current_month if year == current_year else 12
            if year > current_year:
                end_month = 0

            for month in range(1, end_month + 1):
                month_name = self.months_map[month]
                html += f"""
                                <a href="katman_dashboard_{year}_{month:02d}.html" class="list-group-item list-group-item-action small ps-5 fw-bold">
                                    {month_name}
                                </a>
                """
                # Daily links under current month
                if year == current_year and month == current_month:
                    today_day = datetime.now().day
                    start_day = 15 if month == 2 and year == 2026 else 1
                    for d in range(start_day, today_day + 1):
                        html += f"""
                                <a href="katman_dashboard_{year}_{month:02d}_{d:02d}.html" class="list-group-item list-group-item-action small ps-5 text-muted" style="font-size:0.85em; padding-left:3.5rem !important;">
                                    &bull; {d} {month_name}
                                </a>
                        """
            html += "</div></div></div></div>"

        html += """
                </div>
                <div class="p-3 text-center text-muted small mt-4">
                    &copy; 2025 Katman Portal<br>Veri Analitiği
                </div>
            </div>
        </div>
        """
        return html

    # ─── SCORECARD ──────────────────────────────────────────
    def _scorecard_html(self, users, sessions, views, events):
        return f"""
        <div class="row mb-4 g-2">
            <div class="col-6 col-md-3"><div class="metric-box"><div class="metric-value text-primary">{users:,}</div><div class="metric-label">Toplam Kullanıcı</div></div></div>
            <div class="col-6 col-md-3"><div class="metric-box"><div class="metric-value text-success">{sessions:,}</div><div class="metric-label">Toplam Oturum</div></div></div>
            <div class="col-6 col-md-3"><div class="metric-box"><div class="metric-value text-info">{views:,}</div><div class="metric-label">Sayfa Görüntüleme</div></div></div>
            <div class="col-6 col-md-3"><div class="metric-box"><div class="metric-value text-warning">{events:,}</div><div class="metric-label">Toplam Etkileşim</div></div></div>
        </div>
        """

    # ─── TABLE ──────────────────────────────────────────────
    def _df_to_table(self, df):
        if df.empty:
            return "<div class='table-responsive'>" + "<p class='text-muted small'>Veri bulunamadı.</p>" + "</div>"

        cols_config = [
            {"col": "pageTitle", "label": "Sayfa", "width": "40%"},
            {"col": "screenPageViews", "label": "Görüntüleme", "width": "12%"},
            {"col": "activeUsers", "label": "Kullanıcı", "width": "10%"},
            {"col": "scrolledUsers", "label": "Scroll", "width": "8%"},
            {"col": "click", "label": "Tık", "width": "8%"},
            {"col": "file_download", "label": "İndirme", "width": "8%"},
            {"col": "totalInteractions", "label": "Etkileşim", "width": "8%"},
            {"col": "fileName", "label": "Dosya Adı", "width": "40%"},
            {"col": "eventCount", "label": "İndirme Sayısı", "width": "15%"},
        ]

        valid = [c for c in cols_config if c['col'] in df.columns]
        html = "<div class='table-responsive'><table class='table table-sm table-striped table-hover table-bordered'><thead class='table-light'><tr>"
        for c in valid:
            html += f"<th style='width:{c['width']}'>{c['label']}</th>"
        html += "</tr></thead><tbody>"

        for _, row in df.iterrows():
            html += "<tr>"
            for c in valid:
                val = row[c['col']]
                if c['col'] in ['screenPageViews', 'activeUsers', 'eventCount', 'sessions', 'scrolledUsers', 'totalInteractions', 'click', 'file_download']:
                    val = f"{int(val):,}" if pd.notnull(val) else "0"
                html += f"<td>{val}</td>"
            html += "</tr>"
        html += "</tbody></table></div>"
        return html

    # ─── MONTHLY BEST ───────────────────────────────────────
    def _monthly_html(self, df, top_n=5):
        if df.empty:
            return "<p>Veri yok.</p>"
        html = "<div style='max-height: 500px; overflow-y: auto;'>"
        for month in sorted(df['yearMonth'].unique(), reverse=True):
            m_df = df[df['yearMonth'] == month].head(top_n)
            if m_df.empty:
                continue
            m_str = str(month)
            html += f"<h6 class='text-primary mt-3 border-start border-4 border-primary ps-2'>{m_str[:4]}-{m_str[4:]}</h6>"
            html += self._df_to_table(m_df)
        html += "</div>"
        return html

    # ─── AUTHOR & ARTICLE EXTRACTION ──────────────────────
    def _extract_authors_articles(self):
        """Extract author names and their articles from crawled HTML."""
        crawled_dir = "Crawled_Data"
        authors = {}  # slug -> {name, articles: [{title, url, slug}]}

        # 1. Parse author pages for names and article links
        for f in glob.glob(os.path.join(crawled_dir, "author_*.html")):
            slug = os.path.basename(f).replace("author_", "").replace(".html", "")
            try:
                soup = BeautifulSoup(open(f, encoding="utf-8").read(), "html.parser")
                h2 = soup.find("h2")
                name = h2.text.strip() if h2 else slug
                # Find article links
                articles = []
                skip_words = ["author", "category", "tag", "page_", "yazarlar", "#",
                              "newsletter", "hakkimizda", "iletisim", "cerez",
                              "gizlilik", "kullanim", "yayin-ilkeleri", "yaziyukle",
                              "abonelik", "yapay-zeka-kullanim", "soylesiler", "tr_newsletter"]
                for a in soup.select("a[href]"):
                    href = a.get("href", "")
                    text = a.text.strip()
                    if "katmanportal.com" in href and text and len(text) > 15:
                        if not any(w in href for w in skip_words):
                            art_slug = href.rstrip("/").split("/")[-1]
                            if art_slug and art_slug not in [ar["slug"] for ar in articles]:
                                articles.append({
                                    "title": text,
                                    "url": href,
                                    "slug": art_slug,
                                    "path": f"/{art_slug}/"
                                })
                authors[slug] = {"name": name, "articles": articles}
            except Exception as e:
                print(f"  [WARN] Error parsing {f}: {e}")

        # 2. Also scan article pages for author attribution
        art_files = [f for f in os.listdir(crawled_dir)
                     if f.endswith(".html") and not f.startswith(("author_", "category_", "tag_",
                     "index", "yazarlar", "newsletter", "hakkimizda", "iletisim", "cerez",
                     "gizlilik", "kullanim", "yayin", "yaziyukle", "abonelik", "yapay-zeka-kull",
                     "soylesiler", "tr_", "2026"))]
        for af in art_files:
            try:
                soup = BeautifulSoup(open(os.path.join(crawled_dir, af), encoding="utf-8").read(), "html.parser")
                h1 = soup.find("h1")
                title = h1.text.strip() if h1 else af.replace(".html", "").replace("-", " ").title()
                art_slug = af.replace(".html", "")
                # Find author from author link
                author_links = soup.select('a[href*="/author/"]')
                for al in author_links:
                    a_slug = al.get("href", "").rstrip("/").split("/")[-1]
                    a_name = al.text.strip()
                    if a_slug and a_name:
                        if a_slug not in authors:
                            authors[a_slug] = {"name": a_name, "articles": []}
                        existing_slugs = [ar["slug"] for ar in authors[a_slug]["articles"]]
                        if art_slug not in existing_slugs:
                            authors[a_slug]["articles"].append({
                                "title": title,
                                "url": f"https://katmanportal.com/{art_slug}/",
                                "slug": art_slug,
                                "path": f"/{art_slug}/"
                            })
                        break
            except Exception as e:
                print(f"  [WARN] Error parsing article {af}: {e}")

        return authors

    def generate_authors_page(self, sidebar_html):
        """Generate author statistics page with per-article read counts."""
        print(">>> Yazar İstatistikleri sayfası")
        authors = self._extract_authors_articles()
        print(f"   {len(authors)} yazar, toplam {sum(len(a['articles']) for a in authors.values())} yazı bulundu")

        # Get all page views from GA4
        df_pages = self.helper.get_top_pages(start_date="2020-01-01", end_date="today", limit=500)
        self.helper.save_data(df_pages, "all_pages_views")

        # Build path -> views mapping
        page_views = {}
        if not df_pages.empty:
            for _, row in df_pages.iterrows():
                path = row.get("pagePath", "")
                views = int(row.get("screenPageViews", 0))
                page_views[path] = views

        # Build author stats
        author_stats = []
        for slug, info in authors.items():
            total_views = 0
            articles_with_views = []
            for art in info["articles"]:
                v = page_views.get(art["path"], 0)
                # Try with trailing slash variants
                if v == 0:
                    v = page_views.get(art["path"].rstrip("/"), 0)
                if v == 0:
                    v = page_views.get("/" + art["slug"], 0)
                total_views += v
                articles_with_views.append({**art, "views": v})
            articles_with_views.sort(key=lambda x: x["views"], reverse=True)
            author_stats.append({
                "slug": slug,
                "name": info["name"],
                "article_count": len(info["articles"]),
                "total_views": total_views,
                "articles": articles_with_views
            })
        author_stats.sort(key=lambda x: x["total_views"], reverse=True)

        # ── Charts ──
        plotly_static = {'responsive': True, 'scrollZoom': False, 'doubleClick': False, 'displayModeBar': False}

        df_authors = pd.DataFrame([{"Yazar": a["name"], "Yazı Sayısı": a["article_count"],
                                     "Toplam Görüntüleme": a["total_views"]} for a in author_stats])

        # Author by views chart
        fig_views = px.bar(df_authors.sort_values("Toplam Görüntüleme"), x="Toplam Görüntüleme", y="Yazar",
                           orientation="h", title="Yazarlara Göre Toplam Görüntüleme", text="Toplam Görüntüleme")
        fig_views.update_traces(textposition="outside", marker_color="#6f42c1")
        fig_views.update_layout(yaxis_title=None, height=max(500, len(author_stats) * 30), showlegend=False)

        # Author by article count
        fig_count = px.bar(df_authors.sort_values("Yazı Sayısı"), x="Yazı Sayısı", y="Yazar",
                           orientation="h", title="Yazarlara Göre Yazı Sayısı", text="Yazı Sayısı")
        fig_count.update_traces(textposition="outside", marker_color="#17a2b8")
        fig_count.update_layout(yaxis_title=None, height=max(500, len(author_stats) * 30), showlegend=False)

        views_html = fig_views.to_html(full_html=False, include_plotlyjs='cdn', config=plotly_static)
        count_html = fig_count.to_html(full_html=False, include_plotlyjs='cdn', config=plotly_static)

        # ── Author detail tables ──
        author_details = ""
        for a in author_stats:
            rows = ""
            for i, art in enumerate(a["articles"], 1):
                rows += f"""<tr>
                    <td>{i}</td>
                    <td><a href="yazi_{art['slug']}.html" class="text-decoration-none">{art['title']}</a></td>
                    <td class="text-end fw-bold">{art['views']:,}</td>
                </tr>"""
            author_details += f"""
            <div class="card mt-3">
                <div class="card-header bg-light d-flex justify-content-between align-items-center">
                    <a href="yazar_{a['slug']}.html" class="text-decoration-none"><h6 class="mb-0 fw-bold">{a['name']}</h6></a>
                    <span class="badge bg-primary">{a['article_count']} yazı · {a['total_views']:,} görüntüleme</span>
                </div>
                <div class="card-body p-0">
                    <div class="table-responsive">
                    <table class="table table-hover table-sm mb-0">
                        <thead class="table-light">
                            <tr><th>#</th><th>Yazı</th><th class="text-end">Görüntüleme</th></tr>
                        </thead>
                        <tbody>{rows if rows else '<tr><td colspan="3" class="text-muted text-center">Henüz veri yok</td></tr>'}</tbody>
                    </table>
                    </div>
                </div>
            </div>"""

        # ── Summary stats ──
        total_authors = len(author_stats)
        total_articles = sum(a["article_count"] for a in author_stats)
        total_all_views = sum(a["total_views"] for a in author_stats)

        # ── All articles table ──
        all_articles = []
        for a in author_stats:
            for art in a["articles"]:
                all_articles.append({"Yazar": a["name"], "Yazı": art["title"], "Görüntüleme": art["views"], "url": art["url"]})
        all_articles.sort(key=lambda x: x["Görüntüleme"], reverse=True)

        all_art_rows = ""
        for i, art in enumerate(all_articles[:50], 1):
            art_slug = art['url'].rstrip('/').split('/')[-1]
            all_art_rows += f"""<tr>
                <td>{i}</td>
                <td><a href="yazi_{art_slug}.html" class="text-decoration-none">{art['Yazı']}</a></td>
                <td>{art['Yazar']}</td>
                <td class="text-end fw-bold">{art['Görüntüleme']:,}</td>
            </tr>"""

        # ── Generate HTML ──
        head = """<!DOCTYPE html>
        <html lang="tr"><head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Yazar İstatistikleri - Katman Portal</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            body { background: #f8f9fa; }
            @media (max-width: 576px) { .card h4 { font-size: 1.2rem; } }
        </style>
        </head><body>"""
        filepath = os.path.join(self.output_dir, "yazarlar_stats.html")

        html = f"""{head}
        <div class="offcanvas offcanvas-start" tabindex="-1" id="offcanvasSidebar">
            <div class="offcanvas-header bg-light border-bottom">
                <h5 class="offcanvas-title fw-bold text-primary">Katman Portal Analiz</h5>
                <button type="button" class="btn-close" data-bs-dismiss="offcanvas"></button>
            </div>
            <div class="offcanvas-body p-0">{sidebar_html}</div>
        </div>
        <div class="container-fluid py-4 px-3 px-md-5" style="max-width:1400px">
            <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap">
                <div class="d-flex align-items-center gap-3">
                    <button class="btn btn-outline-primary" type="button" data-bs-toggle="offcanvas" data-bs-target="#offcanvasSidebar">
                        <i class="fas fa-bars"></i>
                    </button>
                    <h3 class="fw-bold mb-0 text-primary">Yazar İstatistikleri</h3>
                </div>
            </div>

            <div class="row text-center mb-4">
                <div class="col-md-4"><div class="card p-3"><h4 class="text-primary fw-bold">{total_authors}</h4><small class="text-muted">Toplam Yazar</small></div></div>
                <div class="col-md-4"><div class="card p-3"><h4 class="text-success fw-bold">{total_articles}</h4><small class="text-muted">Toplam Yazı</small></div></div>
                <div class="col-md-4"><div class="card p-3"><h4 class="text-info fw-bold">{total_all_views:,}</h4><small class="text-muted">Toplam Görüntüleme</small></div></div>
            </div>

            <div class="card mb-4">
                <div class="card-header bg-primary text-white">En Çok Okunan Yazılar</div>
                <div class="card-body p-0">
                    <div class="table-responsive">
                    <table class="table table-hover table-sm mb-0">
                        <thead class="table-light">
                            <tr><th>#</th><th>Yazı</th><th>Yazar</th><th class="text-end">Görüntüleme</th></tr>
                        </thead>
                        <tbody>{all_art_rows}</tbody>
                    </table>
                    </div>
                </div>
            </div>

            <div class="card mb-4">
                <div class="card-body">{views_html}</div>
            </div>

            <div class="card mb-4">
                <div class="card-body">{count_html}</div>
            </div>

            <h4 class="fw-bold text-primary mt-4 mb-3">Yazar Detayları</h4>
            {author_details}
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        </body></html>"""

        with open(filepath, "w", encoding="utf-8") as fh:
            fh.write(html)
        print(f"   [SAVED] {filepath}")

        # ── Generate individual article detail pages ──
        for a in author_stats:
            for art in a["articles"]:
                art_filename = f"yazi_{art['slug']}.html"
                print(f"     → Yazı: {art['title'][:50]}...")
                self._generate_detail_page(
                    title=art["title"],
                    paths=art["path"],
                    filename=art_filename,
                    sidebar_html=sidebar_html,
                    subtitle=f"Yazar: {a['name']}"
                )

        # ── Generate individual author detail pages ──
        for a in author_stats:
            if not a["articles"]:
                continue
            author_paths = [art["path"] for art in a["articles"]]
            author_filename = f"yazar_{a['slug']}.html"
            print(f"     → Yazar: {a['name']}")
            self._generate_detail_page(
                title=f"{a['name']} - Tüm Yazılar",
                paths=author_paths,
                filename=author_filename,
                sidebar_html=sidebar_html,
                subtitle=f"{a['article_count']} yazı"
            )

        # ── Update article links in author page to point to detail pages ──
        # (links already set in the table above)

    def _generate_detail_page(self, title, paths, filename, sidebar_html, subtitle=""):
        """Generate a detail page for an article or author with traffic, sources, geography."""
        filepath = os.path.join(self.output_dir, filename)
        plotly_static = {'responsive': True, 'scrollZoom': False, 'doubleClick': False, 'displayModeBar': False}

        from google.analytics.data_v1beta.types import FilterExpression, Filter, DateRange

        # Build path filter
        pf = self.helper._make_path_filter(paths)

        # ── Aggregate totals (all-time) ──
        df_totals = self.helper.run_report(
            dimensions=[],
            metrics=["screenPageViews", "activeUsers", "sessions"],
            date_range=DateRange(start_date="2020-01-01", end_date="today"),
            dimension_filter=pf
        )
        total_views = int(df_totals['screenPageViews'].iloc[0]) if not df_totals.empty else 0
        total_users = int(df_totals['activeUsers'].iloc[0]) if not df_totals.empty else 0
        total_sessions = int(df_totals['sessions'].iloc[0]) if not df_totals.empty else 0

        # ── Minutely traffic chart (10-min resample, like bugun.html) ──
        df_minutely = self.helper.get_page_minutely(paths)
        minutely_html = ""
        if not df_minutely.empty:
            df_minutely['time'] = pd.to_datetime(df_minutely['dateHourMinute'], format='%Y%m%d%H%M')
            df_minutely = df_minutely.sort_values('time')
            for col in ['activeUsers', 'sessions', 'screenPageViews', 'eventCount']:
                df_minutely[col] = df_minutely[col].astype(int)
            df_minutely = df_minutely.set_index('time').resample('10min').sum(numeric_only=True).reset_index()
            df_minutely['activeUsers_hourly'] = df_minutely['activeUsers'].rolling(window=6, min_periods=1).sum()
            df_minutely['sessions_hourly'] = df_minutely['sessions'].rolling(window=6, min_periods=1).sum()

            fig_min = go.Figure()
            fig_min.add_trace(go.Scatter(x=df_minutely['time'], y=df_minutely['activeUsers'],
                                         name='Kullanıcı (10dk)', line=dict(color='#00CC96')))
            fig_min.add_trace(go.Scatter(x=df_minutely['time'], y=df_minutely['sessions'],
                                         name='Oturum (10dk)', line=dict(color='#636EFA')))
            fig_min.add_trace(go.Scatter(x=df_minutely['time'], y=df_minutely['activeUsers_hourly'],
                                         name='Kullanıcı (Saatlik Toplam)', line=dict(color='#00CC96', dash='dot')))
            fig_min.add_trace(go.Scatter(x=df_minutely['time'], y=df_minutely['sessions_hourly'],
                                         name='Oturum (Saatlik Toplam)', line=dict(color='#636EFA', dash='dot')))
            fig_min.update_layout(title=f"Trafik ({title[:40]}) — 10 Dakikalık",
                                  xaxis_title="Saat", yaxis_title="Sayı",
                                  hovermode="x unified", xaxis=dict(tickformat='%H:%M'))
            minutely_html = fig_min.to_html(full_html=False, include_plotlyjs='cdn', config=plotly_static)

        # Fetch remaining data
        df_sources = self.helper.get_page_sources(paths)
        df_countries = self.helper.get_page_countries(paths)
        df_cities = self.helper.get_page_cities(paths)


        # ── Sources pie chart ──
        sources_html = ""
        if not df_sources.empty:
            df_sources['screenPageViews'] = df_sources['screenPageViews'].astype(int)
            fig_src = px.pie(df_sources, values='screenPageViews', names='sessionDefaultChannelGroup',
                             title="Trafik Kaynakları")
            fig_src.update_layout(height=400)
            sources_html = fig_src.to_html(full_html=False, include_plotlyjs='cdn', config=plotly_static)

        # ── Countries bar chart ──
        countries_html = ""
        if not df_countries.empty:
            df_countries['screenPageViews'] = df_countries['screenPageViews'].astype(int)
            df_countries = df_countries.sort_values('screenPageViews', ascending=True)
            fig_country = px.bar(df_countries, x='screenPageViews', y='country', orientation='h',
                                  title="Ülkelere Göre Görüntüleme", text='screenPageViews')
            fig_country.update_traces(textposition='outside', marker_color='#28a745')
            fig_country.update_layout(yaxis_title=None, height=max(300, len(df_countries) * 30), showlegend=False)
            countries_html = fig_country.to_html(full_html=False, include_plotlyjs='cdn', config=plotly_static)

        # ── Cities bar chart ──
        cities_html = ""
        if not df_cities.empty:
            df_cities['screenPageViews'] = df_cities['screenPageViews'].astype(int)
            df_cities = df_cities.sort_values('screenPageViews', ascending=True).tail(15)
            fig_city = px.bar(df_cities, x='screenPageViews', y='city', orientation='h',
                               title="Şehirlere Göre Görüntüleme", text='screenPageViews')
            fig_city.update_traces(textposition='outside', marker_color='#fd7e14')
            fig_city.update_layout(yaxis_title=None, height=max(300, len(df_cities) * 30), showlegend=False)
            cities_html = fig_city.to_html(full_html=False, include_plotlyjs='cdn', config=plotly_static)

        head = """<!DOCTYPE html>
        <html lang="tr"><head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
        <title>""" + title[:60] + """ - Katman Portal</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>body { background: #f8f9fa; } @media (max-width: 576px) { .card h4 { font-size: 1.1rem; } }</style>
        </head><body>"""

        html = f"""{head}
        <div class="offcanvas offcanvas-start" tabindex="-1" id="offcanvasSidebar">
            <div class="offcanvas-header bg-light border-bottom">
                <h5 class="offcanvas-title fw-bold text-primary">Katman Portal Analiz</h5>
                <button type="button" class="btn-close" data-bs-dismiss="offcanvas"></button>
            </div>
            <div class="offcanvas-body p-0">{sidebar_html}</div>
        </div>
        <div class="container-fluid py-4 px-3 px-md-5" style="max-width:1400px">
            <div class="d-flex align-items-center gap-3 mb-2">
                <button class="btn btn-outline-primary" type="button" data-bs-toggle="offcanvas" data-bs-target="#offcanvasSidebar">
                    <i class="fas fa-bars"></i>
                </button>
                <div>
                    <h4 class="fw-bold mb-0 text-primary">{title}</h4>
                    <small class="text-muted">{subtitle}</small>
                </div>
            </div>
            <a href="yazarlar_stats.html" class="btn btn-sm btn-outline-secondary mb-3">
                <i class="fas fa-arrow-left"></i> Yazar İstatistiklerine Dön
            </a>

            <div class="row text-center mb-4">
                <div class="col-4"><div class="card p-3"><h4 class="text-primary fw-bold">{total_views:,}</h4><small class="text-muted">Görüntüleme</small></div></div>
                <div class="col-4"><div class="card p-3"><h4 class="text-success fw-bold">{total_users:,}</h4><small class="text-muted">Kullanıcı</small></div></div>
                <div class="col-4"><div class="card p-3"><h4 class="text-info fw-bold">{total_sessions:,}</h4><small class="text-muted">Oturum</small></div></div>
            </div>

            {"<div class='card mb-4'><div class='card-body'>" + minutely_html + "</div></div>" if minutely_html else "<div class='alert alert-info'>Dakikalık veri bulunamadı.</div>"}

            <div class="row">
                <div class="col-md-6">
                    {"<div class='card mb-4'><div class='card-body'>" + sources_html + "</div></div>" if sources_html else ""}
                </div>
                <div class="col-md-6">
                    {"<div class='card mb-4'><div class='card-body'>" + countries_html + "</div></div>" if countries_html else ""}
                </div>
            </div>

            {"<div class='card mb-4'><div class='card-body'>" + cities_html + "</div></div>" if cities_html else ""}
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        </body></html>"""

        with open(filepath, "w", encoding="utf-8") as fh:
            fh.write(html)
        print(f"   [SAVED] {filepath}")

    # ─── MAIN GENERATOR ────────────────────────────────────
    def generate_all_reports(self):
        # Clear all cache to force fresh API calls
        self.helper.clear_cache()

        sidebar = self._create_sidebar_html()

        # 0. Login page
        print(">>> Login sayfası (index.html)")
        self._generate_login_page(sidebar)

        # 0.5. Author Statistics Page
        self.generate_authors_page(sidebar)

        # 1. Bugün (Today - Live Traffic)
        today_str = datetime.now().strftime('%Y-%m-%d')
        print(f">>> Bugün ({today_str}) - Canlı Trafik")
        self.generate_page(today_str, "today", "Bugün (Canlı)", "bugun.html", sidebar, is_monthly=True)

        # 2. Son 30 Gün

        print(">>> Son 30 Gün (son30gun.html)")
        start_30 = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        self.generate_page(start_30, "today", "Son 30 Gün", "son30gun.html", sidebar, is_monthly=True)

        # 3. Yearly & Monthly - start from 2026 (GA4 tracking installed in 2026)
        current_year = datetime.now().year
        current_month = datetime.now().month
        start_year = 2026  # GA4 tracking start year

        for year in range(start_year, current_year + 1):
            year_start = f"{year}-01-01"
            year_end = f"{year}-12-31"

            print(f">>> {year} Yılı")
            self.generate_page(year_start, year_end, f"{year} Yılı", f"katman_dashboard_{year}.html", sidebar)

            end_m = current_month if year == current_year else 12
            for m in range(1, end_m + 1):
                _, last_day = calendar.monthrange(year, m)
                m_start = f"{year}-{m:02d}-01"
                m_end = f"{year}-{m:02d}-{last_day}"
                month_name = self.months_map[m]
                print(f"    - {month_name} {year}")
                self.generate_page(m_start, m_end, f"{month_name} {year}",
                                   f"katman_dashboard_{year}_{m:02d}.html", sidebar, is_monthly=True)

                # Daily pages for current month
                if year == current_year and m == current_month:
                    today_day = datetime.now().day
                    start_day = 15 if m == 2 and year == 2026 else 1
                    for d in range(start_day, today_day + 1):
                        d_date = f"{year}-{m:02d}-{d:02d}"
                        print(f"      * {d} {month_name} {year}")
                        self.generate_page(d_date, d_date, f"{d} {month_name} {year}",
                                           f"katman_dashboard_{year}_{m:02d}_{d:02d}.html", sidebar, is_monthly=True)

    def generate_page(self, start_date, end_date, title, filename, sidebar_html, is_monthly=False):
        filepath = os.path.join(self.output_dir, filename)
        print(f"   [Processing: {filepath}]")

        # ── Fetch & Save Data ───────────────────────────────
        # Detect if this is a single-day page
        is_single_day = (start_date == end_date) or end_date == "today"

        if is_single_day:
            # Minute-level data for single day
            df_daily = self.helper.get_minutely_traffic(start_date=start_date, end_date=end_date)
            self.helper.save_data(df_daily, f"minutely_{title.replace(' ', '_')}")
        else:
            # Buffer for rolling averages
            fetch_start = start_date
            try:
                dt = datetime.strptime(start_date, "%Y-%m-%d")
                fetch_start = (dt - timedelta(days=30)).strftime("%Y-%m-%d")
            except:
                pass
            df_daily = self.helper.get_daily_traffic(start_date=fetch_start, end_date=end_date)
            self.helper.save_data(df_daily, f"daily_{title.replace(' ', '_')}")

        df_countries = self.helper.get_countries(start_date=start_date, end_date=end_date)
        self.helper.save_data(df_countries, f"countries_{title.replace(' ', '_')}")

        df_cities = self.helper.get_tr_cities(start_date=start_date, end_date=end_date)
        self.helper.save_data(df_cities, f"cities_{title.replace(' ', '_')}")

        df_sources = self.helper.get_global_traffic_sources(start_date=start_date, end_date=end_date, over_time=True)
        self.helper.save_data(df_sources, f"sources_{title.replace(' ', '_')}")

        df_downloads = self.helper.get_downloads(start_date=start_date, end_date=end_date, limit=100)
        self.helper.save_data(df_downloads, f"downloads_{title.replace(' ', '_')}")

        df_top_pages = self.helper.get_top_pages(start_date=start_date, end_date=end_date, limit=20)
        self.helper.save_data(df_top_pages, f"top_pages_{title.replace(' ', '_')}")

        # ── Process Traffic Data ───────────────────────────────
        if is_single_day and not df_daily.empty:
            # Parse dateHourMinute (format: YYYYMMDDHHmm)
            df_daily['time'] = pd.to_datetime(df_daily['dateHourMinute'], format='%Y%m%d%H%M')
            df_daily = df_daily.sort_values('time')
            for col in ['activeUsers', 'sessions', 'screenPageViews', 'eventCount']:
                df_daily[col] = df_daily[col].astype(int)
            # Resample to 10-minute intervals
            df_daily = df_daily.set_index('time').resample('10min').sum(numeric_only=True).reset_index()
            # Hourly rolling sum (6 x 10min = 1 hour)
            df_daily['activeUsers_hourly'] = df_daily['activeUsers'].rolling(window=6, min_periods=1).sum()
            df_daily['sessions_hourly'] = df_daily['sessions'].rolling(window=6, min_periods=1).sum()
        elif not df_daily.empty:
            df_daily['date'] = pd.to_datetime(df_daily['date'])
            df_daily = df_daily.sort_values('date')
            df_daily['activeUsers_rolling'] = df_daily['activeUsers'].rolling(window=30, min_periods=1).sum()
            df_daily['sessions_rolling'] = df_daily['sessions'].rolling(window=30, min_periods=1).sum()
            df_daily = df_daily[df_daily['date'] >= pd.to_datetime(start_date)]

        total_users = int(df_daily['activeUsers'].sum()) if not df_daily.empty else 0
        total_sessions = int(df_daily['sessions'].sum()) if not df_daily.empty else 0
        total_views = int(df_daily['screenPageViews'].astype(int).sum()) if not df_daily.empty else 0
        total_events = int(df_daily['eventCount'].astype(int).sum()) if not df_daily.empty else 0

        scorecard = self._scorecard_html(total_users, total_sessions, total_views, total_events)

        # ── Trend Chart ─────────────────────────────────────
        fig_trend = go.Figure()
        if is_single_day and not df_daily.empty:
            x_col = 'time'
            fig_trend.add_trace(go.Scatter(x=df_daily[x_col], y=df_daily['activeUsers'], name='Kullanıcı (10dk)', line=dict(color='#00CC96')))
            fig_trend.add_trace(go.Scatter(x=df_daily[x_col], y=df_daily['sessions'], name='Oturum (10dk)', line=dict(color='#636EFA')))
            fig_trend.add_trace(go.Scatter(x=df_daily[x_col], y=df_daily['activeUsers_hourly'], name='Kullanıcı (Saatlik Toplam)', line=dict(color='#00CC96', dash='dot')))
            fig_trend.add_trace(go.Scatter(x=df_daily[x_col], y=df_daily['sessions_hourly'], name='Oturum (Saatlik Toplam)', line=dict(color='#636EFA', dash='dot')))
            fig_trend.update_layout(
                title=f"Trafik ({title}) — 10 Dakikalık", xaxis_title="Saat", yaxis_title="Sayı",
                hovermode="x unified",
                xaxis=dict(tickformat='%H:%M')
            )
        elif not df_daily.empty:
            fig_trend.add_trace(go.Scatter(x=df_daily['date'], y=df_daily['activeUsers'], name='Kullanıcı (Günlük)', line=dict(color='#00CC96')))
            fig_trend.add_trace(go.Scatter(x=df_daily['date'], y=df_daily['sessions'], name='Oturum (Günlük)', line=dict(color='#636EFA')))
            fig_trend.add_trace(go.Scatter(x=df_daily['date'], y=df_daily['activeUsers_rolling'], name='Kullanıcı (30G)', line=dict(color='#00CC96', dash='dot'), visible=False))
            fig_trend.add_trace(go.Scatter(x=df_daily['date'], y=df_daily['sessions_rolling'], name='Oturum (30G)', line=dict(color='#636EFA', dash='dot'), visible=False))
            fig_trend.update_layout(
                title=f"Trafik Eğilimi ({title})", xaxis_title="Tarih", yaxis_title="Sayı",
                hovermode="x unified",
                updatemenus=[dict(type="buttons", direction="left", buttons=[
                    dict(args=[{"visible": [True, True, False, False]}], label="Günlük", method="update"),
                    dict(args=[{"visible": [False, False, True, True]}], label="30 Günlük", method="update"),
                ], x=0, y=1.15, showactive=True)]
            )

        # ── World Map ───────────────────────────────────────
        if not df_countries.empty:
            df_countries['country'] = df_countries['country'].replace({'Türkiye': 'Turkey', 'Turkiye': 'Turkey'})
            df_countries['activeUsers'] = df_countries['activeUsers'].astype(int)
            fig_world = px.choropleth(df_countries, locations="country", locationmode="country names",
                                      color="activeUsers", hover_name="country",
                                      color_continuous_scale=px.colors.sequential.Plasma,
                                      title=f"Dünya Geneli Kullanıcı Dağılımı ({title})")
            fig_world.update_geos(projection_type="natural earth", fitbounds="locations")
            fig_world.update_layout(height=600)
        else:
            fig_world = go.Figure()

        # ── Turkey Cities (ALL cities) ──────────────────────
        if not df_cities.empty:
            df_cities['city'] = df_cities['city'].str.title()
            df_city_agg = df_cities.groupby('city')['activeUsers'].sum().reset_index()
            df_city_agg['activeUsers'] = df_city_agg['activeUsers'].astype(int)
            df_city_agg = df_city_agg.sort_values(by='activeUsers', ascending=True)

            fig_cities = px.bar(
                df_city_agg, x='activeUsers', y='city', orientation='h',
                title=f"Türkiye - Tüm Şehirler ({title})",
                text='activeUsers', color='activeUsers', color_continuous_scale="Viridis"
            )
            fig_cities.update_traces(textposition='outside')
            fig_cities.update_layout(
                yaxis_title=None, xaxis_title="Kullanıcı Sayısı",
                showlegend=False, height=max(400, len(df_city_agg) * 25),
                coloraxis_showscale=False
            )
        else:
            fig_cities = go.Figure()

        # ── Traffic Sources ─────────────────────────────────
        if not df_sources.empty and 'sessionDefaultChannelGroup' in df_sources.columns:
            src_agg = df_sources.groupby('sessionDefaultChannelGroup')['activeUsers'].sum().reset_index().sort_values('activeUsers', ascending=True)
            fig_source = px.bar(src_agg, x="activeUsers", y="sessionDefaultChannelGroup", orientation='h',
                                title="Trafik Kaynakları", text="activeUsers",
                                color="sessionDefaultChannelGroup", color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_source.update_traces(textposition='auto')
            fig_source.update_layout(yaxis_title=None, xaxis_title="Kullanıcı Sayısı", showlegend=False)
        else:
            fig_source = go.Figure()

        legend_table = "<div class='mb-3'><small class='text-muted'>Organic Search (Arama), Direct (Doğrudan), Social (Sosyal), Referral (Link).</small></div>"



        # ── Downloads ───────────────────────────────────────
        downloads_html = ""
        if not df_downloads.empty:
            downloads_html = self._df_to_table(df_downloads[['fileName', 'eventCount']])

        # ── Pre-render config ──
        plotly_cfg = {'responsive': True}
        plotly_static = {'responsive': True, 'scrollZoom': False, 'doubleClick': False, 'displayModeBar': False}

        # ── Top Pages Chart ─────────────────────────────────
        if not df_top_pages.empty:
            df_top_display = df_top_pages.head(15).sort_values('screenPageViews', ascending=True)
            fig_top_pages = px.bar(
                df_top_display, x='screenPageViews', y='pageTitle', orientation='h',
                title=f"En Çok Ziyaret Edilen Sayfalar ({title})",
                text='screenPageViews'
            )
            fig_top_pages.update_traces(textposition='outside', marker_color='#17a2b8')
            fig_top_pages.update_layout(
                yaxis_title=None, xaxis_title="Sayfa Görüntüleme",
                showlegend=False, height=max(400, len(df_top_display) * 35)
            )
        else:
            fig_top_pages = go.Figure()

        top_pages_chart_html = fig_top_pages.to_html(full_html=False, include_plotlyjs='cdn', config=plotly_static)
        # ── Enriched Top Pages Table ─────────────────────────
        if not df_top_pages.empty and 'pagePath' in df_top_pages.columns:
            # Build author lookup from crawled index
            author_map = {}
            if self.index_df is not None and 'path' in self.index_df.columns and 'author' in self.index_df.columns:
                for _, r in self.index_df.dropna(subset=['author']).iterrows():
                    p = str(r['path']).strip().rstrip('/')
                    author_map[p] = r['author']

            rows_html = ""
            for i, (_, row) in enumerate(df_top_pages.iterrows(), 1):
                page_title = str(row.get('pageTitle', ''))
                clean_title = page_title.replace(' - Katman Portal', '').replace(' – Katman Portal', '').strip()
                page_path = str(row.get('pagePath', '')).strip().rstrip('/')
                views = int(row['screenPageViews']) if pd.notnull(row['screenPageViews']) else 0

                # Find author
                author = author_map.get(page_path, '')

                # Build slug link
                slug = page_path.strip('/').split('/')[-1] if page_path else ''
                link_html = f'<a href="yazi_{slug}.html" class="text-decoration-none">{clean_title}</a>' if slug and author else clean_title

                rows_html += f"""<tr>
                    <td>{i}</td>
                    <td>{link_html}</td>
                    <td>{author}</td>
                    <td class="text-end fw-bold">{views:,}</td>
                </tr>"""

            top_pages_table_html = f"""<div class="table-responsive">
            <table class="table table-hover table-sm mb-0">
                <thead class="table-light">
                    <tr><th>#</th><th>Yazı</th><th>Yazar</th><th class="text-end">Görüntüleme</th></tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table></div>"""
        else:
            top_pages_table_html = "<p class='text-muted'>Veri yok.</p>"

        # ── Pre-render other Plotly charts ──
        trend_html = fig_trend.to_html(full_html=False, include_plotlyjs='cdn', config=plotly_static)
        world_html = fig_world.to_html(full_html=False, include_plotlyjs='cdn', config=plotly_cfg)  # Map stays interactive
        cities_html_chart = fig_cities.to_html(full_html=False, include_plotlyjs='cdn', config=plotly_static)

        source_html = fig_source.to_html(full_html=False, include_plotlyjs='cdn', config=plotly_static)

        # ── HTML Assembly ───────────────────────────────────
        html = f"""
        <!DOCTYPE html>
        <html lang="tr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Katman Portal - {title}</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
            <style>
                body {{ font-family: 'Inter', sans-serif; background-color: #f0f2f5; }}
                .container {{ max-width: 1400px; margin-top: 20px; margin-bottom: 50px; padding: 0 15px; }}
                .card {{ margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border: none; border-radius: 12px; overflow: hidden; }}
                .card-header {{ border-radius: 12px 12px 0 0 !important; }}
                .card-body {{ overflow-x: auto; }}
                .metric-box {{ background: white; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 2px 6px rgba(0,0,0,0.06); transition: transform 0.2s; margin-bottom: 10px; }}
                .metric-box:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
                .metric-value {{ font-size: 2em; font-weight: 700; }}
                .metric-label {{ color: #6c757d; font-size: 0.9em; margin-top: 4px; }}
                table {{ font-size: 0.88em; }}
                .table-responsive {{ overflow-x: auto; -webkit-overflow-scrolling: touch; }}
                .navbar-brand {{ font-weight: 700; }}
                .plotly-graph-div {{ width: 100% !important; }}
                .js-plotly-plot {{ width: 100% !important; }}

                /* Mobilde grafikleri dokunmatik yapma (harita haric) */
                @media (max-width: 992px) {{
                    .chart-static .plotly-graph-div {{ pointer-events: none; }}
                }}

                /* Mobile */
                @media (max-width: 576px) {{
                    .container {{ padding: 0 8px; margin-top: 10px; }}
                    .metric-value {{ font-size: 1.4em; }}
                    .metric-box {{ padding: 12px 8px; }}
                    .metric-label {{ font-size: 0.75em; }}
                    h1.h3 {{ font-size: 1.1em !important; }}
                    .card-body {{ padding: 10px; }}
                    table {{ font-size: 0.75em; }}
                    .header-bar {{ flex-direction: column; gap: 8px; text-align: center; }}
                }}

                /* Tablet */
                @media (min-width: 577px) and (max-width: 992px) {{
                    .metric-value {{ font-size: 1.6em; }}
                    h1.h3 {{ font-size: 1.3em !important; }}
                    table {{ font-size: 0.82em; }}
                }}
            </style>
        </head>
        <body>
            <script>
                if (sessionStorage.getItem('katman_auth') !== 'true') {{
                    window.location.href = 'index.html';
                }}
            </script>
            {sidebar_html}

            <div class="container">
                <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2 header-bar">
                    <button class="btn btn-primary" type="button" data-bs-toggle="offcanvas" data-bs-target="#offcanvasSidebar">
                        ☰ Menü
                    </button>
                    <div class="text-center flex-grow-1">
                        <h1 class="h3 fw-bold mb-1">{title}</h1>
                        <p class="text-muted mb-0 small">{start_date} – {end_date}</p>
                    </div>
                    <span class="badge bg-secondary">{datetime.now().strftime('%d.%m.%Y %H:%M')}</span>
                </div>

                {scorecard}

                <div class="card chart-static"><div class="card-body">{trend_html}</div></div>

                <div class="row g-2">
                    <div class="col-12 col-md-6"><div class="card"><div class="card-body">{world_html}</div></div></div>
                    <div class="col-12 col-md-6"><div class="card chart-static"><div class="card-body">{cities_html_chart}</div></div></div>
                </div>



                <div class="card chart-static"><div class="card-body">{legend_table}{source_html}</div></div>

                <div class="card mt-4 chart-static">
                    <div class="card-header bg-info text-white"><i class="fas fa-fire me-2"></i>En Çok Ziyaret Edilen Sayfalar</div>
                    <div class="card-body">
                        {top_pages_chart_html}
                        <h6 class="mt-3">Detaylı Tablo</h6>
                        {top_pages_table_html}
                    </div>
                </div>



                <div class="card mt-4">
                    <div class="card-header bg-dark text-white">Dosya İndirmeleri</div>
                    <div class="card-body">{downloads_html}</div>
                </div>
            </div>

            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        """

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"   [SAVED] {filepath}")

    def _generate_login_page(self, sidebar_html):
        """Generate a password-protected login page as index.html."""
        filepath = os.path.join(self.output_dir, "index.html")
        html = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Katman Portal - Giriş</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0c1445 0%, #1a237e 50%, #283593 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-card {
            background: rgba(255,255,255,0.95);
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 50px 40px;
            max-width: 420px;
            width: 100%;
            text-align: center;
            backdrop-filter: blur(10px);
        }
        .login-card h1 {
            font-size: 1.8em;
            font-weight: 700;
            color: #1a237e;
            margin-bottom: 8px;
        }
        .login-card p {
            color: #6c757d;
            margin-bottom: 30px;
        }
        .form-control {
            border-radius: 12px;
            padding: 14px 20px;
            font-size: 1em;
            border: 2px solid #e0e0e0;
            transition: border-color 0.3s;
        }
        .form-control:focus {
            border-color: #1a237e;
            box-shadow: 0 0 0 3px rgba(26,35,126,0.15);
        }
        .btn-login {
            background: linear-gradient(135deg, #1a237e, #283593);
            border: none;
            border-radius: 12px;
            padding: 14px;
            font-size: 1.05em;
            font-weight: 600;
            color: white;
            width: 100%;
            margin-top: 15px;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .btn-login:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(26,35,126,0.3);
            color: white;
        }
        .error-msg {
            color: #dc3545;
            font-size: 0.9em;
            margin-top: 10px;
            display: none;
        }
        .logo-icon {
            font-size: 3em;
            color: #1a237e;
            margin-bottom: 15px;
        }
    </style>
</head>
<body>
    <div class="login-card">
        <div class="logo-icon"><i class="fas fa-chart-pie"></i></div>
        <h1>Katman Portal</h1>
        <p>Veri Analitiği Dashboard</p>
        <form id="loginForm">
            <input type="password" class="form-control" id="passwordInput"
                   placeholder="Şifrenizi girin..." autofocus>
            <button type="submit" class="btn btn-login">
                <i class="fas fa-sign-in-alt me-2"></i>Giriş Yap
            </button>
            <div class="error-msg" id="errorMsg">
                <i class="fas fa-exclamation-circle me-1"></i> Yanlış şifre. Tekrar deneyin.
            </div>
        </form>
    </div>
    <script>
        // If already authenticated, redirect
        if (sessionStorage.getItem('katman_auth') === 'true') {
            window.location.href = 'bugun.html';
        }
        document.getElementById('loginForm').addEventListener('submit', function(e) {
            e.preventDefault();
            var pw = document.getElementById('passwordInput').value;
            if (pw === 'patman kortal') {
                sessionStorage.setItem('katman_auth', 'true');
                window.location.href = 'bugun.html';
            } else {
                document.getElementById('errorMsg').style.display = 'block';
                document.getElementById('passwordInput').value = '';
                document.getElementById('passwordInput').focus();
            }
        });
    </script>
</body>
</html>
        """
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"   [SAVED] {filepath}")


if __name__ == "__main__":
    gen = ReportGenerator()
    gen.generate_all_reports()
