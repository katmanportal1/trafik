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

class ReportGenerator:
    def __init__(self):
        self.helper = AnalyticsHelper()
        self.output_dir = "dashboard"
        os.makedirs(self.output_dir, exist_ok=True)

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
                                <a href="katman_dashboard_{year}_{month:02d}.html" class="list-group-item list-group-item-action small ps-5">
                                    {month_name}
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
        <div class="row mb-4">
            <div class="col-md-3"><div class="metric-box"><div class="metric-value text-primary">{users:,}</div><div class="metric-label">Toplam Kullanıcı</div></div></div>
            <div class="col-md-3"><div class="metric-box"><div class="metric-value text-success">{sessions:,}</div><div class="metric-label">Toplam Oturum</div></div></div>
            <div class="col-md-3"><div class="metric-box"><div class="metric-value text-info">{views:,}</div><div class="metric-label">Sayfa Görüntüleme</div></div></div>
            <div class="col-md-3"><div class="metric-box"><div class="metric-value text-warning">{events:,}</div><div class="metric-label">Toplam Etkileşim</div></div></div>
        </div>
        """

    # ─── TABLE ──────────────────────────────────────────────
    def _df_to_table(self, df):
        if df.empty:
            return "<p class='text-muted small'>Veri bulunamadı.</p>"

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
        html = "<table class='table table-sm table-striped table-hover table-bordered'><thead class='table-light'><tr>"
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
        html += "</tbody></table>"
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

    # ─── MAIN GENERATOR ────────────────────────────────────
    def generate_all_reports(self):
        sidebar = self._create_sidebar_html()

        # 0. Login page
        print(">>> Login sayfası (index.html)")
        self._generate_login_page(sidebar)

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

    def generate_page(self, start_date, end_date, title, filename, sidebar_html, is_monthly=False):
        filepath = os.path.join(self.output_dir, filename)
        print(f"   [Processing: {filepath}]")

        # ── Fetch & Save Data ───────────────────────────────
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

        # ── Process Daily ───────────────────────────────────
        if not df_daily.empty:
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
        if not df_daily.empty:
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

        # ── Subgroup Analysis ───────────────────────────────
        from google.analytics.data_v1beta.types import FilterExpression, Filter, DateRange

        group_stats = []
        for group in self.groups:
            path_filter = FilterExpression(
                filter=Filter(field_name="pagePath",
                              string_filter=Filter.StringFilter(
                                  match_type=Filter.StringFilter.MatchType.BEGINS_WITH,
                                  value=group['prefix'])))
            df_total = self.helper.run_report(
                dimensions=[], metrics=["sessions", "activeUsers", "screenPageViews"],
                date_range=DateRange(start_date=start_date, end_date=end_date),
                dimension_filter=path_filter)

            sessions = int(df_total['sessions'].iloc[0]) if not df_total.empty else 0
            users = int(df_total['activeUsers'].iloc[0]) if not df_total.empty else 0
            views = int(df_total['screenPageViews'].iloc[0]) if not df_total.empty else 0
            group_stats.append({"Group": group['name'], "Sessions": sessions, "Users": users, "Views": views})

        self.helper.save_data(pd.DataFrame(group_stats), f"groups_{title.replace(' ', '_')}")

        df_gs = pd.DataFrame(group_stats).sort_values("Sessions", ascending=True)
        fig_group_s = px.bar(df_gs, x="Sessions", y="Group", orientation='h', text="Sessions",
                             title="Kategori Toplam Ziyaret", color="Sessions", color_continuous_scale="Blues")
        fig_group_s.update_layout(coloraxis_showscale=False)
        fig_group_u = px.bar(df_gs, x="Users", y="Group", orientation='h', text="Users",
                             title="Kategori Kullanıcı Sayısı", color="Users", color_continuous_scale="Greens")
        fig_group_u.update_layout(coloraxis_showscale=False)

        # ── Category Details ────────────────────────────────
        groups_html = ""
        for i, group in enumerate(self.groups):
            df_top = self.helper.get_grouped_top_pages(path_prefix=group['prefix'], start_date=start_date, end_date=end_date, limit=20)
            if not df_top.empty:
                df_top = df_top[
                    (df_top['pagePath'] != group['prefix']) &
                    (df_top['pagePath'] != group['prefix'] + "/")
                ].head(20)
                if 'click' in df_top.columns and 'file_download' in df_top.columns:
                    df_top['totalInteractions'] = df_top['click'] + df_top['file_download']
                else:
                    df_top['totalInteractions'] = 0

            self.helper.save_data(df_top, f"group_top_{group['name'].replace(' ', '_')}_{title.replace(' ', '_')}")

            gs = group_stats[i]
            group_scorecard = f"""
            <div class="row mb-4">
                <div class="col-md-4"><div class="metric-box border-start border-4 border-primary"><div class="metric-label">Görüntülenme</div><div class="metric-value text-primary">{gs['Views']:,}</div></div></div>
                <div class="col-md-4"><div class="metric-box border-start border-4 border-success"><div class="metric-label">Kullanıcı</div><div class="metric-value text-success">{gs['Users']:,}</div></div></div>
                <div class="col-md-4"><div class="metric-box border-start border-4 border-warning"><div class="metric-label">Oturum</div><div class="metric-value text-warning">{gs['Sessions']:,}</div></div></div>
            </div>
            """

            col_class = "col-md-12" if is_monthly else "col-md-6"
            monthly_html = ""
            if not is_monthly:
                df_monthly = self.helper.get_grouped_monthly_pages(path_prefix=group['prefix'], start_date=start_date, end_date=end_date)
                if not df_monthly.empty:
                    df_monthly = df_monthly[(df_monthly['pagePath'] != group['prefix']) & (df_monthly['pagePath'] != group['prefix'] + "/")]
                    if 'click' in df_monthly.columns and 'file_download' in df_monthly.columns:
                        df_monthly['totalInteractions'] = df_monthly['click'] + df_monthly['file_download']
                    else:
                        df_monthly['totalInteractions'] = 0
                monthly_html = f'<div class="col-md-6"><h5>Aylık En İyiler</h5>{self._monthly_html(df_monthly, top_n=5)}</div>'

            groups_html += f"""
            <div class="card mt-4">
                <div class="card-header bg-primary text-white">{group['name']} Analizi</div>
                <div class="card-body">
                    {group_scorecard}
                    <div class="row">
                        <div class="{col_class}"><h5>En Çok Okunan</h5>{self._df_to_table(df_top)}</div>
                        {monthly_html}
                    </div>
                </div>
            </div>
            """

        # ── Downloads ───────────────────────────────────────
        downloads_html = ""
        if not df_downloads.empty:
            downloads_html = self._df_to_table(df_downloads[['fileName', 'eventCount']])

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
                .container {{ max-width: 1400px; margin-top: 20px; margin-bottom: 50px; }}
                .card {{ margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border: none; border-radius: 12px; }}
                .card-header {{ border-radius: 12px 12px 0 0 !important; }}
                .metric-box {{ background: white; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 2px 6px rgba(0,0,0,0.06); transition: transform 0.2s; }}
                .metric-box:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
                .metric-value {{ font-size: 2em; font-weight: 700; }}
                .metric-label {{ color: #6c757d; font-size: 0.9em; margin-top: 4px; }}
                table {{ font-size: 0.88em; }}
                .navbar-brand {{ font-weight: 700; }}
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
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <button class="btn btn-primary" type="button" data-bs-toggle="offcanvas" data-bs-target="#offcanvasSidebar">
                        ☰ Menü
                    </button>
                    <div class="text-center">
                        <h1 class="h3 fw-bold">Katman Portal: {title}</h1>
                        <p class="text-muted mb-0">Kapsam: {start_date} – {end_date}</p>
                    </div>
                    <span class="badge bg-secondary">{datetime.now().strftime('%d.%m.%Y %H:%M')}</span>
                </div>

                {scorecard}

                <div class="card"><div class="card-body">{fig_trend.to_html(full_html=False, include_plotlyjs='cdn')}</div></div>

                <div class="row">
                    <div class="col-md-6"><div class="card"><div class="card-body">{fig_world.to_html(full_html=False, include_plotlyjs='cdn')}</div></div></div>
                    <div class="col-md-6"><div class="card"><div class="card-body">{fig_cities.to_html(full_html=False, include_plotlyjs='cdn')}</div></div></div>
                </div>

                <div class="row">
                    <div class="col-md-6"><div class="card"><div class="card-body">{fig_group_s.to_html(full_html=False, include_plotlyjs='cdn')}</div></div></div>
                    <div class="col-md-6"><div class="card"><div class="card-body">{fig_group_u.to_html(full_html=False, include_plotlyjs='cdn')}</div></div></div>
                </div>

                <div class="card"><div class="card-body">{legend_table}{fig_source.to_html(full_html=False, include_plotlyjs='cdn')}</div></div>

                <h3 class="mt-5 border-bottom pb-2">Kategori Detayları</h3>
                {groups_html}

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
            if (pw === 'katmanportal') {
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
