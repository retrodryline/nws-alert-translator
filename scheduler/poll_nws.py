import requests
import feedparser
from datetime import datetime
from app.translator import translate_to_spanish
import json
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db.database import init_db, insert_alert, alert_is_unchanged

NWS_API_URL = "https://api.weather.gov/alerts/active"
NWS_CAP_FEED_URL = "https://alerts.weather.gov/cap/us.php?x=1"

def fetch_nws_api_alerts():
    print("\n--- Fetching from NWS API ---")
    try:
        headers = {"User-Agent": "WeatherAlertTranslator/1.0 (your@email.com)"}
        response = requests.get(NWS_API_URL, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        alerts = data.get("features", [])
        if not alerts:
            print("[API] No alerts found.")
            return

        for alert in alerts:  
            props = alert.get("properties", {})
            headline = props.get("headline", "")
            description = props.get("description", "")

            if alert_is_unchanged(props["id"], headline, description):
                print(f"⏩ Unchanged alert: {props['id']}")
                continue

            translated_headline = translate_to_spanish(headline)
            translated_description = translate_to_spanish(description)

            alert_data = {
                "id": props.get("id", ""),
                "source": "api",
                "headline": props.get("headline", ""),
                "area": props.get("areaDesc", ""),
                "severity": props.get("severity", ""),
                "effective": props.get("effective", ""),
                "expires": props.get("expires", ""),
                "raw_json": json.dumps(props),
                "translated_headline": translated_headline,
                "translated_description": translated_description,
                "translated_json": ""                
            }
            print(f"[API] {alert_data['id']}: {alert_data['headline']} - {alert_data['area']}")
            print(f"🔍 Found {len(alerts)} alerts from API")
            print(f"[🌍] Translated: {translated_headline}")
            insert_alert(alert_data)

    except Exception as e:
        print(f"Error fetching NWS API alerts: {e}")


# def fetch_nws_cap_alerts():
#     print("\n--- Fetching from NWS CAP XML Feed ---")
#     try:
#         feed = feedparser.parse(NWS_CAP_FEED_URL)
#         for entry in feed.entries:
#             alert_data = {
#                 "id": entry.id,
#                 "source": "cap",
#                 "headline": entry.title,
#                 "area": entry.get("areaDesc", ""),
#                 "severity": "",  # Not available in CAP feed easily
#                 "effective": entry.published,
#                 "expires": entry.updated,
#                 "raw_json": json.dumps(entry)
#             }
#             insert_alert(alert_data)
#             print(f"[CAP] {entry.id}: {entry.title}")
#     except Exception as e:
#         print(f"Error fetching NWS CAP alerts: {e}")

if __name__ == "__main__":
    print(f"\n🌩️ NWS Alert Poller - {datetime.now()}")
    init_db()
    fetch_nws_api_alerts()
    # fetch_nws_cap_alerts()