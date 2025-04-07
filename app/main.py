from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import sqlite3
import json
from feedgen.feed import FeedGenerator
from db.database import init_db, fetch_alerts, insert_alert
import threading
import time
from scheduler.poll_nws import fetch_nws_api_alerts #, fetch_nws_cap_alerts
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

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


@app.get("/", response_class=HTMLResponse)
def home():
    with open("static/widget.html", "r") as f:
        return HTMLResponse(f.read())

@app.get("/alerts")
def get_all_alerts():
    return fetch_alerts(DB_PATH, limit=50)

@app.get("/alerts/latest")
def get_latest_alerts():
    return fetch_alerts(DB_PATH, limit=5)

@app.get("/rss", response_class=Response)
def rss_feed():
    fg = FeedGenerator()
    fg.title("Translated Weather Alerts - Español")
    fg.link(href="https://nws-alert-translator.onrender.com/rss", rel="self")
    fg.description("Live weather alerts translated to Spanish with severity, timing, and safety instructions.")

    alerts = fetch_alerts(DB_PATH, limit=100)

    for a in alerts:
        props = json.loads(a["raw_json"]) if a["raw_json"] else {}
        event = props.get("event", "Unknown Event")
        effective = props.get("effective", "Unknown Time")
        expires = props.get("expires", "Unknown Time")
        urgency = props.get("urgency", "N/A")
        certainty = props.get("certainty", "N/A")
        sender = props.get("senderName", "N/A")

        title = f"⚠️ [{a['severity']}] {event} - {a['area']} (Until {expires})"

        desc = f"""
📍 **Area:** {a['area'] or 'Unknown'}
📣 **Event:** {event}
⏰ **Effective:** {effective}
⌛ **Expires:** {expires}
⚠️ **Severity:** {a['severity'] or 'N/A'}
❗ **Urgency:** {urgency}
📡 **Certainty:** {certainty}
🗣️ **Sender:** {sender}
🧭 **Instruction:** {a.get('translated_instruction') or 'Sin instrucciones.'}

📝 **Descripción:** {a.get('translated_description') or 'Sin descripción.'}
"""

        fe = fg.add_entry()
        fe.id(a["id"])
        fe.title(title)
        fe.description(desc.strip())
        fe.link(href=f"https://nws-alert-translator.onrender.com/alerts/{a['id']}")
        fe.pubDate(a["effective"] or a["expires"])

    return Response(content=fg.rss_str(pretty=True), media_type="application/rss+xml")


def poll_nws_every(interval=30):  # every 30 sec
    def loop():
        while True:
            print("🔁 Polling NWS alerts...")
            time.sleep(2)
            try:
                fetch_nws_api_alerts(DB_PATH)
                #fetch_nws_cap_alerts()
            except Exception as e:
                print(f"❌ Polling error: {e}")
            time.sleep(interval)
    thread = threading.Thread(target=loop, daemon=True)
    thread.start()

@app.on_event("startup")
def startup_event():
    init_db(DB_PATH)
    # Start polling in a background thread
    poll_nws_every(30)


@app.get("/ping")
def ping():
    return {"status": "alive"}