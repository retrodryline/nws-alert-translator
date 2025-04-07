from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import sqlite3
import os
from fastapi.responses import Response
from feedgen.feed import FeedGenerator
from pydantic import BaseModel

app = FastAPI()

class AlertPush(BaseModel):
    id: str
    headline: str
    description: str
    area: str
    severity: str
    effective: str
    expires: str

@app.post("/alerts/push")
def push_alert(alert: AlertPush):
    translated_headline = translate_to_spanish(alert.headline)
    translated_description = translate_to_spanish(alert.description)

    alert_data = {
        "id": alert.id,
        "source": "push",
        "headline": alert.headline,
        "area": alert.area,
        "severity": alert.severity,
        "effective": alert.effective,
        "expires": alert.expires,
        "raw_json": alert.json(),
        "translated_headline": translated_headline,
        "translated_description": translated_description,
        "translated_json": ""
    }

    insert_alert(alert_data)
    return {"status": "ok", "translated_headline": translated_headline}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static folder for widget
app.mount("/static", StaticFiles(directory="static"), name="static")

DB_PATH = os.path.join(os.path.dirname(__file__), "../db/alerts.db")

def fetch_alerts(limit=10):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM alerts ORDER BY effective DESC LIMIT ?", (limit,))
    results = [dict(row) for row in cur.fetchall()]
    conn.close()
    return results

@app.get("/")
def root():
    return {"message": "🌩️ NWS Alert Translator is alive"}

@app.get("/alerts")
def get_all_alerts():
    return fetch_alerts(limit=50)

@app.get("/alerts/latest")
def get_latest_alerts():
    return fetch_alerts(limit=5)

@app.get("/alerts/{alert_id}")
def get_alert_by_id(alert_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else {"error": "Alert not found"}

@app.get("/rss", response_class=Response)
def rss_feed():
    fg = FeedGenerator()
    fg.title("Translated Weather Alerts")
    fg.link(href="https://your-domain.com/rss", rel="alternate")
    fg.description("Live translated weather alerts in Spanish")

    alerts = fetch_alerts(limit=15)
    for a in alerts:
        fe = fg.add_entry()
        fe.id(a["id"])
        fe.title(a["translated_headline"])
        fe.description(a["translated_description"] or "No description provided.")
        fe.link(href=f"https://your-domain.com/alerts/{a['id']}")
        fe.pubDate(a["effective"] or a["expires"] or "")

    return Response(content=fg.rss_str(pretty=True), media_type="application/rss+xml")
