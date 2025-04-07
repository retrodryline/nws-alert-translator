import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(__file__), "alerts.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    with open(os.path.join(os.path.dirname(__file__), "schema.sql")) as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()

def insert_alert(alert):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT OR REPLACE INTO alerts
            (id, source, headline, area, severity, effective, expires, raw_json,
            translated_headline, translated_description, translated_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert["id"],
            alert["source"],
            alert["headline"],
            alert["area"],
            alert["severity"],
            alert["effective"],
            alert["expires"],
            alert["raw_json"],
            alert.get("translated_headline", ""),
            alert.get("translated_description", ""),
            alert.get("translated_json", "")
        ))
        conn.commit()
    except Exception as e:
        print(f"DB insert error: {e}")
    finally:
        conn.close() 

def alert_is_unchanged(alert_id, headline, description):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT headline, raw_json FROM alerts WHERE id = ?
    """, (alert_id,))
    row = cur.fetchone()
    conn.close()

    if row is None:
        return False  # not in DB

    existing_headline = row[0] or ""
    existing_json = json.loads(row[1]) if row[1] else {}
    existing_description = existing_json.get("description", "")

    return (headline.strip() == existing_headline.strip() and
            description.strip() == existing_description.strip())