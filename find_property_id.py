import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "animated-moon-487420-h4-435de0712ac6.json"

from google.analytics.admin import AnalyticsAdminServiceClient

client = AnalyticsAdminServiceClient()
accounts = list(client.list_account_summaries())

if not accounts:
    print("Hicbir hesap bulunamadi!")
else:
    for account in accounts:
        print(f"Hesap: {account.display_name} ({account.account})")
        for prop in account.property_summaries:
            prop_id = prop.property.split("/")[-1]
            print(f"  Property: {prop.display_name} -> ID: {prop_id}")
