"""
Comprehensive unit and integration test suite for SafeRoute
Tests database, ML engine, routing engine, and Flask REST endpoints.
"""

import unittest
import json
from app import app
from database import init_db, add_incident_report, get_all_incident_reports, log_sos_alert
from ml_engine import ml_engine, haversine_distance
from routing_engine import compute_alternative_routes

class SafeRouteTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        init_db()

    def test_health_check(self):
        """Verify API health endpoint returns healthy status."""
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["app"], "SafeRoute AI Navigation System")

    def test_presets_endpoint(self):
        """Verify preset routes are returned for 1-click demos."""
        resp = self.client.get("/api/presets")
        self.assertEqual(resp.status_code, 200)
        presets = resp.get_json()
        self.assertIsInstance(presets, list)
        self.assertGreaterEqual(len(presets), 3)
        self.assertIn("start_lat", presets[0])
        self.assertIn("end_lat", presets[0])

    def test_facilities_endpoint(self):
        """Verify police stations and hospitals are loaded."""
        resp = self.client.get("/api/facilities")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("police_stations", data)
        self.assertIn("hospitals", data)
        self.assertGreater(len(data["police_stations"]), 0)
        self.assertGreater(len(data["hospitals"]), 0)

    def test_hotspots_endpoint(self):
        """Verify K-Means hotspots are calculated and returned."""
        resp = self.client.get("/api/hotspots")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("hotspots", data)
        self.assertGreater(len(data["hotspots"]), 0)
        self.assertIn("risk_level", data["hotspots"][0])

    def test_route_generation(self):
        """Verify generation of 3 alternative routes with safety scores."""
        payload = {
            "start_lat": 12.9756,
            "start_lon": 77.6066,
            "end_lat": 12.9784,
            "end_lon": 77.6408,
            "hour_of_day": 22,
            "travel_mode": "driving"
        }
        resp = self.client.post("/api/routes", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        routes = data["routes"]
        self.assertEqual(len(routes), 3)

        # First route should be safest
        safest = routes[0]
        self.assertEqual(safest["route_bias"], "safest")
        self.assertGreater(safest["safety_score"], routes[2]["safety_score"])
        self.assertGreater(len(safest["coordinates"]), 5)

    def test_incident_reporting_workflow(self):
        """Test submitting a new community incident report and retrieving it."""
        payload = {
            "incident_type": "Poor Street Lighting",
            "description": "Completely dark stretch with no streetlights",
            "latitude": 12.9745,
            "longitude": 77.5750,
            "hour_of_day": 21,
            "severity": 6,
            "lighting_level": 1
        }
        resp = self.client.post("/api/report", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("report_id", data)

        # Retrieve reports
        resp2 = self.client.get("/api/reports")
        self.assertEqual(resp2.status_code, 200)
        reports_data = resp2.get_json()
        self.assertGreater(reports_data["total"], 0)

    def test_sos_alert_dispatch(self):
        """Test simulated SOS distress call."""
        payload = {
            "latitude": 12.9716,
            "longitude": 77.5946,
            "notes": "Unit test SOS trigger"
        }
        resp = self.client.post("/api/sos", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("emergency_contacts", data)
        self.assertIn("alert_id", data)

    def test_ml_metrics_endpoint(self):
        """Test ML metrics and feature importance endpoint."""
        resp = self.client.get("/api/ml-metrics")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("metrics", data)
        self.assertIn("feature_importances", data)
        self.assertGreater(len(data["feature_importances"]), 0)

if __name__ == "__main__":
    unittest.main()
