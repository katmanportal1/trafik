import os
import pandas as pd
from datetime import datetime, timedelta
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest,
    DateRange,
    Dimension,
    Metric,
    FilterExpression,
    Filter,
    FilterExpressionList
)
import json
import time
import pickle
import hashlib

# Set credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "animated-moon-487420-h4-435de0712ac6.json"
PROPERTY_ID = "524822431"

class AnalyticsHelper:
    def __init__(self):
        self.client = BetaAnalyticsDataClient()
        self.property = f"properties/{PROPERTY_ID}"
        self.cache_dir = "data_cache"
        self.data_export_dir = "exported_data"
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        if not os.path.exists(self.data_export_dir):
            os.makedirs(self.data_export_dir)

    def _get_cache_key(self, dimensions, metrics, date_range, dimension_filter, limit):
        """Generate a unique key for the request."""
        filter_str = str(dimension_filter) if dimension_filter else "None"
        key_str = f"{sorted(dimensions)}_{sorted(metrics)}_{date_range.start_date}_{date_range.end_date}_{filter_str}_{limit}"
        return hashlib.md5(key_str.encode('utf-8')).hexdigest()

    def _load_from_cache(self, key):
        """Load dataframe from cache if exists."""
        path = os.path.join(self.cache_dir, key + ".pkl")
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"Warning: Failed to load cache {path}: {e}")
        return None

    def _save_to_cache(self, key, df):
        """Save dataframe to cache."""
        path = os.path.join(self.cache_dir, key + ".pkl")
        try:
            with open(path, "wb") as f:
                pickle.dump(df, f)
        except Exception as e:
            print(f"Warning: Failed to save cache {path}: {e}")

    def save_data(self, df, name):
        """Save dataframe to both Excel and Parquet in exported_data/."""
        try:
            xlsx_path = os.path.join(self.data_export_dir, f"{name}.xlsx")
            parquet_path = os.path.join(self.data_export_dir, f"{name}.parquet")
            df.to_excel(xlsx_path, index=False)
            df.to_parquet(parquet_path, index=False)
            print(f"  [SAVED] {name} -> {len(df)} rows")
        except Exception as e:
            print(f"  [ERROR saving {name}]: {e}")

    def run_report(self, dimensions, metrics, date_range, dimension_filter=None, limit=100000):
        """Generic wrapper for GA4 run_report with Auto-Pagination."""
        cache_key = self._get_cache_key(dimensions, metrics, date_range, dimension_filter, limit)
        cached_df = self._load_from_cache(cache_key)
        if cached_df is not None:
            return cached_df

        all_data = []
        offset = 0
        batch_size = 10000  # GA4 max limit per request

        while True:
            request = RunReportRequest(
                property=self.property,
                dimensions=[Dimension(name=d) for d in dimensions],
                metrics=[Metric(name=m) for m in metrics],
                date_ranges=[date_range],
                dimension_filter=dimension_filter,
                limit=batch_size,
                offset=offset,
                keep_empty_rows=True
            )
            try:
                response = self.client.run_report(request)
            except Exception as e:
                print(f"API Error in run_report (Offset {offset}): {e}")
                break

            if not response.rows:
                break

            for row in response.rows:
                item = {}
                for i, d in enumerate(dimensions):
                    item[d] = row.dimension_values[i].value
                for i, m in enumerate(metrics):
                    val = row.metric_values[i].value
                    try:
                        if '.' in val:
                            item[m] = float(val)
                        else:
                            item[m] = int(val)
                    except ValueError:
                        item[m] = val
                all_data.append(item)

            fetched_count = len(response.rows)
            total_fetched = len(all_data)

            if fetched_count < batch_size:
                break

            if limit and total_fetched >= limit:
                all_data = all_data[:limit]
                break

            offset += batch_size
            time.sleep(0.5)

        df = pd.DataFrame(all_data)
        self._save_to_cache(cache_key, df)
        return df

    def get_daily_traffic(self, start_date="30daysAgo", end_date="today"):
        """Get daily sessions and users."""
        return self.run_report(
            dimensions=["date"],
            metrics=["activeUsers", "sessions", "screenPageViews", "engagementRate", "eventCount"],
            date_range=DateRange(start_date=start_date, end_date=end_date)
        )

    def get_minutely_traffic(self, start_date="today", end_date="today"):
        """Get minute-level sessions and users for a single day."""
        return self.run_report(
            dimensions=["dateHourMinute"],
            metrics=["activeUsers", "sessions", "screenPageViews", "eventCount"],
            date_range=DateRange(start_date=start_date, end_date=end_date)
        )

    def get_top_pages(self, start_date="2020-01-01", end_date="today", limit=50):
        """Get top viewed pages."""
        df = self.run_report(
            dimensions=["pageTitle", "pagePath"],
            metrics=["screenPageViews", "activeUsers"],
            date_range=DateRange(start_date=start_date, end_date=end_date),
            limit=limit
        )
        if not df.empty:
            df = df.sort_values(by="screenPageViews", ascending=False).head(limit)
        return df

    def get_countries(self, start_date="2020-01-01", end_date="today"):
        """Get traffic by country."""
        return self.run_report(
            dimensions=["country"],
            metrics=["activeUsers", "screenPageViews"],
            date_range=DateRange(start_date=start_date, end_date=end_date)
        )

    def get_tr_cities(self, start_date="2020-01-01", end_date="today"):
        """Get traffic by ALL Turkish cities (no limit)."""
        df = self.run_report(
            dimensions=["city", "country"],
            metrics=["activeUsers", "screenPageViews"],
            date_range=DateRange(start_date=start_date, end_date=end_date)
        )
        if not df.empty:
            df = df[df['country'].astype(str).str.lower().isin(['turkey', 'türkiye', 'turkiye'])]
        return df

    def get_traffic_sources(self, start_date="2020-01-01", end_date="today"):
        """Get session traffic sources."""
        return self.run_report(
            dimensions=["sessionDefaultChannelGroup"],
            metrics=["sessions", "activeUsers"],
            date_range=DateRange(start_date=start_date, end_date=end_date)
        )

    def get_global_traffic_sources(self, start_date="2020-01-01", end_date="today", over_time=False):
        """Get global traffic sources, optionally broken down by date."""
        dims = ["sessionDefaultChannelGroup"]
        if over_time:
            dims.append("date")
        return self.run_report(
            dimensions=dims,
            metrics=["sessions", "activeUsers"],
            date_range=DateRange(start_date=start_date, end_date=end_date),
            limit=10000
        )

    def get_grouped_top_pages(self, path_prefix, start_date="2020-01-01", end_date="today", limit=20):
        """Get top pages filtered by a path prefix (e.g. /category/guncel)."""
        path_filter = FilterExpression(
            filter=Filter(
                field_name="pagePath",
                string_filter=Filter.StringFilter(
                    value=path_prefix,
                    match_type=Filter.StringFilter.MatchType.BEGINS_WITH
                )
            )
        )

        df_main = self.run_report(
            dimensions=["pageTitle", "pagePath"],
            metrics=["screenPageViews", "activeUsers", "scrolledUsers"],
            date_range=DateRange(start_date=start_date, end_date=end_date),
            dimension_filter=path_filter,
            limit=limit
        )

        if df_main.empty:
            return pd.DataFrame()

        # Specific Events (click, file_download)
        events_filter = FilterExpression(
            and_group=FilterExpressionList(
                expressions=[
                    path_filter,
                    FilterExpression(
                        filter=Filter(
                            field_name="eventName",
                            in_list_filter=Filter.InListFilter(
                                values=["click", "file_download"],
                                case_sensitive=False
                            )
                        )
                    )
                ]
            )
        )

        df_events = self.run_report(
            dimensions=["pagePath", "eventName"],
            metrics=["eventCount"],
            date_range=DateRange(start_date=start_date, end_date=end_date),
            dimension_filter=events_filter,
            limit=limit * 5
        )

        if not df_events.empty:
            df_pivot = df_events.pivot(index='pagePath', columns='eventName', values='eventCount').fillna(0)
            df_main = df_main.merge(df_pivot, on='pagePath', how='left')
            if 'click' in df_main.columns: df_main['click'] = df_main['click'].fillna(0)
            else: df_main['click'] = 0
            if 'file_download' in df_main.columns: df_main['file_download'] = df_main['file_download'].fillna(0)
            else: df_main['file_download'] = 0
        else:
            df_main['click'] = 0
            df_main['file_download'] = 0

        df_main = df_main.sort_values(by="screenPageViews", ascending=False).head(limit)
        return df_main

    def get_grouped_monthly_pages(self, path_prefix, start_date="2020-01-01", end_date="today"):
        """Get monthly top pages for a specific group."""
        path_filter = FilterExpression(
            filter=Filter(
                field_name="pagePath",
                string_filter=Filter.StringFilter(
                    value=path_prefix,
                    match_type=Filter.StringFilter.MatchType.BEGINS_WITH
                )
            )
        )

        df_main = self.run_report(
            dimensions=["yearMonth", "pageTitle", "pagePath"],
            metrics=["screenPageViews", "activeUsers", "scrolledUsers"],
            date_range=DateRange(start_date=start_date, end_date=end_date),
            dimension_filter=path_filter,
            limit=10000
        )

        if df_main.empty:
            return pd.DataFrame()

        events_filter = FilterExpression(
            and_group=FilterExpressionList(
                expressions=[
                    path_filter,
                    FilterExpression(
                        filter=Filter(
                            field_name="eventName",
                            in_list_filter=Filter.InListFilter(
                                values=["click", "file_download"],
                                case_sensitive=False
                            )
                        )
                    )
                ]
            )
        )

        df_events = self.run_report(
            dimensions=["yearMonth", "pagePath", "eventName"],
            metrics=["eventCount"],
            date_range=DateRange(start_date=start_date, end_date=end_date),
            dimension_filter=events_filter,
            limit=20000
        )

        if not df_events.empty:
            df_pivot = df_events.pivot(index=['yearMonth', 'pagePath'], columns='eventName', values='eventCount').reset_index().fillna(0)
            df_main = df_main.merge(df_pivot, on=['yearMonth', 'pagePath'], how='left')
            if 'click' in df_main.columns: df_main['click'] = df_main['click'].fillna(0)
            else: df_main['click'] = 0
            if 'file_download' in df_main.columns: df_main['file_download'] = df_main['file_download'].fillna(0)
            else: df_main['file_download'] = 0
        else:
            df_main['click'] = 0
            df_main['file_download'] = 0

        df_main = df_main.sort_values(by=["yearMonth", "screenPageViews"], ascending=[False, False])
        return df_main

    def get_grouped_yearly_stats(self, path_prefix, start_date="2020-01-01", end_date="today"):
        """Get total sessions for a group broken down by year."""
        path_filter = FilterExpression(
            filter=Filter(
                field_name="pagePath",
                string_filter=Filter.StringFilter(
                    value=path_prefix,
                    match_type=Filter.StringFilter.MatchType.BEGINS_WITH
                )
            )
        )
        return self.run_report(
            dimensions=["year"],
            metrics=["sessions", "activeUsers", "screenPageViews"],
            date_range=DateRange(start_date=start_date, end_date=end_date),
            dimension_filter=path_filter
        )

    def get_downloads(self, start_date="2020-01-01", end_date="today", limit=50):
        """Get top file downloads."""
        download_filter = FilterExpression(
            filter=Filter(
                field_name="eventName",
                string_filter=Filter.StringFilter(value="file_download")
            )
        )
        return self.run_report(
            dimensions=["fileName", "linkUrl"],
            metrics=["eventCount"],
            date_range=DateRange(start_date=start_date, end_date=end_date),
            dimension_filter=download_filter,
            limit=limit
        )


if __name__ == "__main__":
    # Quick Test
    helper = AnalyticsHelper()

    print("=== GA4 Bağlantı Testi: Katman Portal ===")
    print(f"Property ID: {PROPERTY_ID}\n")

    print("--- Günlük Trafik (Son 30 Gün) ---")
    df_daily = helper.get_daily_traffic(start_date="30daysAgo", end_date="today")
    if not df_daily.empty:
        print(f"  {len(df_daily)} gün veri bulundu")
        print(df_daily.head())
        helper.save_data(df_daily, "test_daily_traffic")
    else:
        print("  Veri bulunamadı!")

    print("\n--- Top Ülkeler ---")
    df_countries = helper.get_countries(start_date="2020-01-01")
    if not df_countries.empty:
        print(df_countries.sort_values(by="activeUsers", ascending=False).head(10))
        helper.save_data(df_countries, "test_countries")

    print("\n--- Tüm TR Şehirleri ---")
    df_cities = helper.get_tr_cities(start_date="2020-01-01")
    if not df_cities.empty:
        print(f"  {len(df_cities)} şehir bulundu")
        print(df_cities.sort_values(by="activeUsers", ascending=False).head(10))
        helper.save_data(df_cities, "test_tr_cities")

    print("\n=== Test Tamamlandı ===")
