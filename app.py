"""
SafeRoute: AI-Based Safety-Aware Navigation System for Women
Flask Backend Application
"""

import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from database import init_db, add_incident_report, get_all_incident_reports, log_sos_alert
from ml_engine import ml_engine
from routing_engine import compute_alternative_routes

app = Flask(__name__)
app.config['SECRET_KEY'] = 'saferoute-women-safety-secure-key-2026'

# Initialize SQLite database on startup
init_db()

# Predefined demo scenarios for quick testing and evaluation
PRESET_ROUTES = [
    {
        "id": "preset-1",
        "title": "Late Night Commute: Metro Station to Tech Park",
        "category": "Tech Corridor",
        "start_name": "MG Road Metro Station",
        "start_lat": 12.9756,
        "start_lon": 77.6066,
        "end_name": "Indiranagar Tech Hub",
        "end_lat": 12.9784,
        "end_lon": 77.6408,
        "hour_of_day": 22,
        "mode": "driving",
        "scenario_note": "Evaluates night-time safety, avoiding poorly-lit back alleys and choosing well-lit 100ft road corridor near police stations."
    },
    {
        "id": "preset-2",
        "title": "Evening Walk: University Campus to Hostel",
        "category": "Student Route",
        "start_name": "Central University Library",
        "start_lat": 12.9348,
        "start_lon": 77.6050,
        "end_name": "Koramangala Women's Hostel",
        "end_lat": 12.9348,
        "end_lon": 77.6245,
        "hour_of_day": 20,
        "mode": "walking",
        "scenario_note": "Walking mode prioritizing street lighting, active pedestrian movement, and bypassing isolated vacant lots."
    },
    {
        "id": "preset-3",
        "title": "City Transit: Railway Terminal to City Hospital",
        "category": "Emergency Corridor",
        "start_name": "Majestic Central Railway Station",
        "start_lat": 12.9767,
        "start_lon": 77.5713,
        "end_name": "Bowring Hospital & Emergency Care",
        "end_lat": 12.9815,
        "end_lon": 77.6047,
        "hour_of_day": 23,
        "mode": "driving",
        "scenario_note": "Bypasses high-density Majestic underpass crime cluster in favor of the monitored Cubbon Park arterial route."
    },
    {
        "id": "preset-4",
        "title": "Suburban Connect: HSR Sector 1 to Silk Board",
        "category": "Suburban Transit",
        "start_name": "HSR 27th Main Commercial Center",
        "start_lat": 12.9116,
        "start_lon": 77.6389,
        "end_name": "Silk Board Junction Transit",
        "end_lat": 12.9176,
        "end_lon": 77.6233,
        "hour_of_day": 21,
        "mode": "driving",
        "scenario_note": "Demonstrates avoiding dark unlit service roads by staying on main patrolled avenues."
    }
]

@app.route("/")
def index():
    """Render main SafeRoute navigation dashboard."""
    return render_template("index.html")

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "app": "SafeRoute AI Navigation System",
        "version": "1.0.0-gamma",
        "timestamp": datetime.now().isoformat()
    })

@app.route("/api/presets", methods=["GET"])
def get_presets():
    """Return pre-configured test routes for 1-click evaluation."""
    return jsonify(PRESET_ROUTES)

@app.route("/api/facilities", methods=["GET"])
def get_facilities():
    """Return nearby emergency facilities (police stations and hospitals)."""
    facilities_file = os.path.join(os.path.dirname(__file__), "data", "emergency_facilities.json")
    if os.path.exists(facilities_file):
        with open(facilities_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return jsonify(data)
    return jsonify({"police_stations": [], "hospitals": [], "emergency_helplines": []})

@app.route("/api/hotspots", methods=["GET"])
def get_hotspots():
    """Return AI-derived crime clusters and risk hotspots."""
    return jsonify({
        "hotspots": ml_engine.hotspots,
        "total": len(ml_engine.hotspots)
    })

@app.route("/api/routes", methods=["POST"])
def get_routes():
    """
    Generate and evaluate alternative routes between start and destination coordinates.
    Payload:
      start_lat, start_lon, end_lat, end_lon, hour_of_day, travel_mode
    """
    data = request.get_json() or {}
    try:
        start_lat = float(data.get("start_lat", 12.9756))
        start_lon = float(data.get("start_lon", 77.6066))
        end_lat = float(data.get("end_lat", 12.9784))
        end_lon = float(data.get("end_lon", 77.6408))
        hour_of_day = int(data.get("hour_of_day", 22))
        travel_mode = str(data.get("travel_mode", "driving")).lower()
        if travel_mode not in ["driving", "walking"]:
            travel_mode = "driving"

        routes = compute_alternative_routes(
            start_lat=start_lat,
            start_lon=start_lon,
            end_lat=end_lat,
            end_lon=end_lon,
            hour_of_day=hour_of_day,
            travel_mode=travel_mode
        )

        return jsonify({
            "status": "success",
            "start": {"lat": start_lat, "lon": start_lon},
            "end": {"lat": end_lat, "lon": end_lon},
            "hour_of_day": hour_of_day,
            "travel_mode": travel_mode,
            "routes": routes
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

@app.route("/api/report", methods=["POST"])
def report_incident():
    """Submit a safety incident or hazard (unlit road, harassment, etc.)."""
    data = request.get_json() or {}
    try:
        incident_type = data.get("incident_type", "Safety Concern")
        description = data.get("description", "")
        latitude = float(data.get("latitude"))
        longitude = float(data.get("longitude"))
        hour_of_day = int(data.get("hour_of_day", datetime.now().hour))
        severity = int(data.get("severity", 5))
        lighting_level = int(data.get("lighting_level", 2))

        report_id = add_incident_report(
            incident_type=incident_type,
            description=description,
            latitude=latitude,
            longitude=longitude,
            hour_of_day=hour_of_day,
            severity=severity,
            lighting_level=lighting_level
        )

        return jsonify({
            "status": "success",
            "report_id": report_id,
            "message": "Incident report logged successfully. Safety risk metrics updated.",
            "data": {
                "id": report_id,
                "incident_type": incident_type,
                "description": description,
                "latitude": latitude,
                "longitude": longitude,
                "severity": severity,
                "lighting_level": lighting_level,
                "status": "Community Reported"
            }
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route("/api/reports", methods=["GET"])
def get_reports():
    """Retrieve community-reported safety incidents."""
    reports = get_all_incident_reports(limit=50)
    return jsonify({"reports": reports, "total": len(reports)})

@app.route("/api/sos", methods=["POST"])
def trigger_sos():
    """Simulate instantaneous SOS dispatch with coordinates."""
    data = request.get_json() or {}
    lat = float(data.get("latitude", 12.9716))
    lon = float(data.get("longitude", 77.5946))
    notes = data.get("notes", "Emergency SOS triggered from SafeRoute UI")

    alert_id = log_sos_alert(lat, lon, notes)

    return jsonify({
        "status": "success",
        "alert_id": alert_id,
        "message": "EMERGENCY SOS BROADCAST ACTIVE. Location coordinates dispatched to emergency response contacts.",
        "emergency_contacts": [
            {"service": "National Emergency Service", "dial": "112"},
            {"service": "Women Safety Helpline", "dial": "1091"},
            {"service": "Police Emergency", "dial": "100"},
            {"service": "Ambulance", "dial": "108"}
        ],
        "dispatched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "coordinates": {"lat": lat, "lon": lon}
    })

@app.route("/api/ml-metrics", methods=["GET"])
def get_ml_metrics():
    """Return model performance metrics and feature importances for academic demo."""
    return jsonify({
        "metrics": ml_engine.metrics,
        "feature_importances": ml_engine.feature_importance,
        "algorithm_details": {
            "clustering": "K-Means Unsupervised Clustering (Hotspot identification)",
            "regression": "Random Forest Regressor (Continuous risk score estimation 0-100)",
            "routing_engine": "OSRM / Graph routing with ML safety cost function penalty",
            "citation": "Based on SafeRoute research by Levy et al. & Women Safety Platform 2025"
        }
    })

if __name__ == "__main__":
    print("Starting SafeRoute Application on http://127.0.0.1:5000 ...")
    app.run(debug=True, host="0.0.0.0", port=5000)
