from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import sqlite3
import json
from feedgen.feed import FeedGenerator

from db.database import init_db, fetch_alerts, insert_alert

# 📦 Handle SQLite path
if os.getenv("RENDER"):
    DB_PATH = "/tmp/alerts.db"
else:
    DB_PATH = os.path.join(os.path.dirname(__file__), "../db/alerts.db")

app = FastAPI()

# CORS setup for frontends if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static widget
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
def startup_event():
    # Ensure DB + alerts table exist on startup
    init_db(DB_PATH)

@app.get("/")
def root():
    return {"message": "🌩️ NWS Alert Translator is alive"}

@app.get("/alerts")
def get_all_alerts():
    return fetch_alerts(DB_PATH, limit=50)

@app.get("/alerts/latest")
def get_latest_alerts():
    return fetch_alerts(DB_PATH, limit=5)

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
    fg.link(href="https://nws-alert-translator.onrender.com/rss", rel="alternate")
    fg.description("Live weather alerts translated to Spanish")

    alerts = fetch_alerts(DB_PATH, limit=15)
    for a in alerts:
        fe = fg.add_entry()
        fe.id(a["id"])
        fe.title(a["translated_headline"])
        fe.description(a.get("translated_description") or "")
        fe.link(href=f"https://nws-alert-translator.onrender.com/alerts/{a['id']}")
        fe.pubDate(a["effective"] or a["expires"])

    return Response(content=fg.rss_str(pretty=True), media_type="application/rss+xml")
