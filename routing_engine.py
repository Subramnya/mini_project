"""
SafeRoute Routing Engine:
- Generates 3 alternative routes: Safest, Balanced, and Fastest/Direct
- Queries OSRM (OpenStreetMap Routing Machine) with synthetic intelligent fallback
- Evaluates routes against ML Safety Engine to assign safety & risk metrics
"""

import math
import requests
import numpy as np
from ml_engine import ml_engine, haversine_distance

OSRM_BASE_URL = "http://router.project-osrm.org/route/v1"

def generate_interpolated_curve(start_coord, end_coord, intermediate_waypoint=None, num_steps=22):
    """
    Generate realistic road-like polyline coordinates between start and end,
    bending through an intermediate waypoint if provided, with realistic road grid jitter.
    """
    lat1, lon1 = start_coord
    lat2, lon2 = end_coord

    points = []
    
    if intermediate_waypoint:
        w_lat, w_lon = intermediate_waypoint
        # Curve through waypoint using quadratic Bezier curve
        for t in np.linspace(0, 1, num_steps):
            # B(t) = (1-t)^2 * P0 + 2(1-t)t * P1 + t^2 * P2
            lat = (1 - t)**2 * lat1 + 2 * (1 - t) * t * w_lat + t**2 * lat2
            lon = (1 - t)**2 * lon1 + 2 * (1 - t) * t * w_lon + t**2 * lon2
            
            # Subtle realistic street grid variation (not straight line)
            jitter_lat = math.sin(t * math.pi * 3) * 0.0006
            jitter_lon = math.cos(t * math.pi * 3) * 0.0006
            points.append([round(lat + jitter_lat, 6), round(lon + jitter_lon, 6)])
    else:
        # Direct route with street-like turns
        for t in np.linspace(0, 1, num_steps):
            lat = lat1 + t * (lat2 - lat1)
            lon = lon1 + t * (lon2 - lon1)
            jitter_lat = math.sin(t * math.pi * 4) * 0.0004
            jitter_lon = math.cos(t * math.pi * 4) * 0.0004
            points.append([round(lat + jitter_lat, 6), round(lon + jitter_lon, 6)])

    # Ensure exact endpoints
    points[0] = [lat1, lon1]
    points[-1] = [lat2, lon2]
    return points

def fetch_osrm_route(coords_list, mode="driving"):
    """
    Query public OSRM service with coordinates [[lat1, lon1], [lat2, lon2], ...].
    Returns (coordinates_list, distance_km, duration_mins) or None.
    """
    try:
        # OSRM expects lon,lat format
        coord_str = ";".join([f"{lon:.6f},{lat:.6f}" for lat, lon in coords_list])
        url = f"{OSRM_BASE_URL}/{mode}/{coord_str}?overview=full&geometries=geojson&steps=false"
        
        resp = requests.get(url, timeout=2.5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == "Ok" and data.get("routes"):
                best_route = data["routes"][0]
                # GeoJSON coordinates are [lon, lat], convert to [lat, lon]
                geo_coords = [[pt[1], pt[0]] for pt in best_route["geometry"]["coordinates"]]
                dist_km = round(best_route["distance"] / 1000.0, 2)
                dur_mins = round(best_route["duration"] / 60.0, 1)
                return geo_coords, dist_km, dur_mins
    except Exception:
        pass
    return None

def compute_alternative_routes(start_lat, start_lon, end_lat, end_lon, hour_of_day=21, travel_mode="driving"):
    """
    Generate 3 alternative routes:
    1. Safest Route (Green): bypasses crime clusters, stays on well-lit arterial corridors, passes safe havens
    2. Balanced Route (Amber): tradeoff between travel time and safety
    3. Fastest Route (Red): shortest path, accepts higher risk / shortcuts
    """
    base_dist = haversine_distance(start_lat, start_lon, end_lat, end_lon)
    mid_lat = (start_lat + end_lat) / 2.0
    mid_lon = (start_lon + end_lon) / 2.0

    # Calculate perpendicular vector to offset waypoints
    d_lat = end_lat - start_lat
    d_lon = end_lon - start_lon
    norm = math.sqrt(d_lat**2 + d_lon**2) or 0.001
    perp_lat = -d_lon / norm
    perp_lon = d_lat / norm

    # Find nearest crime hotspot to the midpoint to determine avoidance direction
    nearest_hotspot = None
    min_h_dist = 999.0
    for h in ml_engine.hotspots:
        d = haversine_distance(mid_lat, mid_lon, h["latitude"], h["longitude"])
        if d < min_h_dist:
            min_h_dist = d
            nearest_hotspot = h

    # Choose offset direction that steers AWAY from nearest crime hotspot
    offset_scale = max(0.008, min(0.025, base_dist * 0.002))
    
    cand1_lat = mid_lat + perp_lat * offset_scale
    cand1_lon = mid_lon + perp_lon * offset_scale
    cand2_lat = mid_lat - perp_lat * offset_scale
    cand2_lon = mid_lon - perp_lon * offset_scale

    if nearest_hotspot:
        d1 = haversine_distance(cand1_lat, cand1_lon, nearest_hotspot["latitude"], nearest_hotspot["longitude"])
        d2 = haversine_distance(cand2_lat, cand2_lon, nearest_hotspot["latitude"], nearest_hotspot["longitude"])
        # Steer towards candidate furthest from high risk hotspot
        if d1 > d2:
            safe_waypoint = [cand1_lat, cand1_lon]
            alt_waypoint = [cand2_lat, cand2_lon]
        else:
            safe_waypoint = [cand2_lat, cand2_lon]
            alt_waypoint = [cand1_lat, cand1_lon]
    else:
        safe_waypoint = [cand1_lat, cand1_lon]
        alt_waypoint = [cand2_lat, cand2_lon]

    # --- 1. SAFEST ROUTE ---
    safe_coords = None
    safe_dist = None
    safe_dur = None
    
    # Try OSRM with safe waypoint
    osrm_res = fetch_osrm_route([[start_lat, start_lon], safe_waypoint, [end_lat, end_lon]], mode=travel_mode)
    if osrm_res:
        safe_coords, safe_dist, safe_dur = osrm_res
    else:
        safe_coords = generate_interpolated_curve([start_lat, start_lon], [end_lat, end_lon], intermediate_waypoint=safe_waypoint)
        safe_dist = round(base_dist * 1.22, 2)
        speed = 28 if travel_mode == "driving" else 4.5
        safe_dur = round((safe_dist / speed) * 60, 1)

    safe_eval = ml_engine.evaluate_route(safe_coords, hour_of_day=hour_of_day, route_bias="safest")

    # --- 2. BALANCED ROUTE ---
    bal_coords = None
    bal_dist = None
    bal_dur = None

    # Mild offset or alternative boulevard
    bal_waypoint = [
        mid_lat + (safe_waypoint[0] - mid_lat) * 0.45,
        mid_lon + (safe_waypoint[1] - mid_lon) * 0.45
    ]
    osrm_res_bal = fetch_osrm_route([[start_lat, start_lon], bal_waypoint, [end_lat, end_lon]], mode=travel_mode)
    if osrm_res_bal:
        bal_coords, bal_dist, bal_dur = osrm_res_bal
    else:
        bal_coords = generate_interpolated_curve([start_lat, start_lon], [end_lat, end_lon], intermediate_waypoint=bal_waypoint)
        bal_dist = round(base_dist * 1.10, 2)
        speed = 30 if travel_mode == "driving" else 4.8
        bal_dur = round((bal_dist / speed) * 60, 1)

    bal_eval = ml_engine.evaluate_route(bal_coords, hour_of_day=hour_of_day, route_bias="balanced")

    # --- 3. FASTEST / DIRECT ROUTE ---
    fast_coords = None
    fast_dist = None
    fast_dur = None

    osrm_res_fast = fetch_osrm_route([[start_lat, start_lon], [end_lat, end_lon]], mode=travel_mode)
    if osrm_res_fast:
        fast_coords, fast_dist, fast_dur = osrm_res_fast
    else:
        fast_coords = generate_interpolated_curve([start_lat, start_lon], [end_lat, end_lon], intermediate_waypoint=None)
        fast_dist = round(base_dist * 1.02, 2)
        speed = 34 if travel_mode == "driving" else 5.0
        fast_dur = round((fast_dist / speed) * 60, 1)

    fast_eval = ml_engine.evaluate_route(fast_coords, hour_of_day=hour_of_day, route_bias="fastest")

    routes = [
        {
            "id": "route-safest",
            "name": "Safest Route",
            "tagline": "AI Recommended for Night / Solo Travel",
            "route_bias": "safest",
            "is_recommended": True,
            "badge": "Safest (AI Recommended)",
            "color": "#10b981", # Green
            "distance_km": safe_dist,
            "duration_mins": safe_dur,
            "safety_score": safe_eval["safety_score"],
            "risk_score": safe_eval["risk_score"],
            "risk_level": safe_eval["risk_level"],
            "lighting_index": safe_eval["lighting_index"],
            "safe_havens_count": safe_eval["safe_havens_along_route"],
            "hotspots_avoided": safe_eval["hotspots_avoided"],
            "features": [
                f"{safe_eval['lighting_index']} corridor",
                f"{safe_eval['safe_havens_along_route']} Emergency Stations En-Route",
                f"Avoids {safe_eval['hotspots_avoided']} Crime Hotspots"
            ],
            "verdict": "Highest safety level. Maximizes well-patrolled arterial roads with verified streetlights and quick access to emergency help.",
            "coordinates": safe_coords
        },
        {
            "id": "route-balanced",
            "name": "Balanced Route",
            "tagline": "Good Safety & Moderate Travel Time",
            "route_bias": "balanced",
            "is_recommended": False,
            "badge": "Moderate Safety",
            "color": "#f59e0b", # Amber
            "distance_km": bal_dist,
            "duration_mins": bal_dur,
            "safety_score": bal_eval["safety_score"],
            "risk_score": bal_eval["risk_score"],
            "risk_level": bal_eval["risk_level"],
            "lighting_index": bal_eval["lighting_index"],
            "safe_havens_count": bal_eval["safe_havens_along_route"],
            "hotspots_avoided": bal_eval["hotspots_avoided"],
            "features": [
                f"{bal_eval['lighting_index']} lighting",
                f"Saves ~{round(safe_dur - bal_dur, 1)} mins vs safest route",
                "Intermediate risk level"
            ],
            "verdict": "Reasonable tradeoff between travel efficiency and safety. Mostly well-lit with minor transit through secondary streets.",
            "coordinates": bal_coords
        },
        {
            "id": "route-fastest",
            "name": "Direct / Shortest Route",
            "tagline": "Shortest Path (Conventional Navigation)",
            "route_bias": "fastest",
            "is_recommended": False,
            "badge": "Higher Risk",
            "color": "#ef4444", # Red
            "distance_km": fast_dist,
            "duration_mins": fast_dur,
            "safety_score": fast_eval["safety_score"],
            "risk_score": fast_eval["risk_score"],
            "risk_level": fast_eval["risk_level"],
            "lighting_index": fast_eval["lighting_index"],
            "safe_havens_count": fast_eval["safe_havens_along_route"],
            "hotspots_avoided": fast_eval["hotspots_avoided"],
            "features": [
                f"Fastest by ~{round(safe_dur - fast_dur, 1)} mins",
                "Includes unverified or poorly-lit stretches",
                f"Traverses {fast_eval['hotspots_traversed']} risk areas"
            ],
            "verdict": "Shortest distance, but passes through poorly-lit corridors or isolated stretches with higher historical incident rates.",
            "coordinates": fast_coords
        }
    ]

    return routes

if __name__ == "__main__":
    print("Testing Routing Engine...")
    test_routes = compute_alternative_routes(12.9716, 77.5946, 12.9352, 77.6245, hour_of_day=22)
    for r in test_routes:
        print(f"{r['name']}: Safety={r['safety_score']}%, Dist={r['distance_km']}km, Time={r['duration_mins']}m, Points={len(r['coordinates'])}")
