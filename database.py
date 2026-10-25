"""
Database management for SafeRoute: SQLite storage for user-reported incidents,
crowdsourced safety alerts, and emergency SOS logs.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "saferoute.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Incident reports table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incident_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_type TEXT NOT NULL,
            description TEXT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            hour_of_day INTEGER DEFAULT 20,
            severity INTEGER DEFAULT 5,
            lighting_level INTEGER DEFAULT 2,
            status TEXT DEFAULT 'Verified',
            reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # SOS alerts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sos_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            alert_type TEXT DEFAULT 'CRITICAL_SOS',
            alert_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            status TEXT DEFAULT 'DISPATCHED_TO_EMERGENCY_CONTACTS'
        )
    """)

    conn.commit()

    # Pre-populate a few verified community incident reports if empty
    cursor.execute("SELECT COUNT(*) FROM incident_reports")
    count = cursor.fetchone()[0]
    if count == 0:
        seed_incidents = [
            ("Poor Street Lighting", "Streetlights non-functional for past 2 weeks, pitch dark after 8 PM", 12.9745, 77.5750, 21, 5, 1, 'Verified'),
            ("Eve Teasing / Catcalling", "Group of loiterers near bus stop making women commuters uncomfortable", 12.9320, 77.6180, 22, 7, 2, 'Verified'),
            ("Deserted / Isolated Stretch", "Underpass unlit and without any CCTV or security guard", 12.9140, 77.6410, 23, 6, 1, 'Verified'),
            ("Verbal Harassment", "Unsafe atmosphere reported near vacant lot", 12.9810, 77.6390, 20, 6, 2, 'Verified')
        ]
        cursor.executemany("""
            INSERT INTO incident_reports (incident_type, description, latitude, longitude, hour_of_day, severity, lighting_level, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, seed_incidents)
        conn.commit()

    conn.close()

def add_incident_report(incident_type, description, latitude, longitude, hour_of_day=20, severity=5, lighting_level=2):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO incident_reports (incident_type, description, latitude, longitude, hour_of_day, severity, lighting_level, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Community Reported')
    """, (incident_type, description, float(latitude), float(longitude), int(hour_of_day), int(severity), int(lighting_level)))
    conn.commit()
    report_id = cursor.lastrowid
    conn.close()
    return report_id

def get_all_incident_reports(limit=50):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, incident_type, description, latitude, longitude, hour_of_day, severity, lighting_level, status, reported_at
        FROM incident_reports
        ORDER BY reported_at DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def log_sos_alert(latitude, longitude, notes="Triggered from SafeRoute Web Interface"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sos_alerts (latitude, longitude, notes)
        VALUES (?, ?, ?)
    """, (float(latitude), float(longitude), str(notes)))
    conn.commit()
    alert_id = cursor.lastrowid
    conn.close()
    return alert_id

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
