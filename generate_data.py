"""
Generate realistic synthetic historical crime and safety data for SafeRoute
Focusing on urban area (Bengaluru metropolitan region) with realistic hotspots,
lighting scores, severity levels, and time-of-day distributions.
"""

import os
import random
import pandas as pd
import numpy as np

def generate_crime_dataset(output_path="data/crime_dataset.csv", n_records=350):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    random.seed(42)
    np.random.seed(42)

    # Known hotspot clusters (latitude, longitude, risk_weight, name)
    hotspot_centers = [
        (12.9760, 77.5720, 0.85, "Majestic Alleys / Underpass"),
        (12.9352, 77.6245, 0.65, "Koramangala 8th Block Outskirts"),
        (12.9121, 77.6446, 0.80, "HSR 27th Main Dark Stretch"),
        (12.9856, 77.6407, 0.60, "Indiranagar 100ft Backroads"),
        (12.8452, 77.6602, 0.75, "Electronic City Phase 2 Isolated Flyover"),
        (13.0358, 77.5970, 0.70, "Hebbal Ring Road Service Lane"),
        (12.9698, 77.7499, 0.70, "Whitefield Outer Roadways"),
        (12.9550, 77.5850, 0.50, "Lalbagh West Gate Peripheral"),
        (13.0033, 77.5644, 0.75, "Yeshwanthpur Industrial Perimeter"),
    ]

    # Incident types with base severity (1-10) and typical lighting quality
    incident_types = [
        {"type": "Poor Street Lighting", "base_sev": 4, "weight": 0.22, "lighting": [1, 2]},
        {"type": "Eve Teasing / Catcalling", "base_sev": 6, "weight": 0.25, "lighting": [1, 2, 3]},
        {"type": "Stalking Incident", "base_sev": 8, "weight": 0.15, "lighting": [1, 2]},
        {"type": "Snatching / Pickpocketing", "base_sev": 6, "weight": 0.15, "lighting": [2, 3, 4]},
        {"type": "Deserted / Isolated Stretch", "base_sev": 5, "weight": 0.12, "lighting": [1, 2]},
        {"type": "Verbal Harassment", "base_sev": 7, "weight": 0.18, "lighting": [1, 2, 3]},
        {"type": "Attempted Robbery", "base_sev": 9, "weight": 0.08, "lighting": [1, 2]},
    ]

    records = []
    
    # 70% clustered around known problem areas, 30% dispersed across city
    for i in range(n_records):
        inc_info = random.choices(
            incident_types,
            weights=[t["weight"] for t in incident_types]
        )[0]
        
        if random.random() < 0.72:
            # Clustered near a hotspot
            center = random.choice(hotspot_centers)
            lat = center[0] + np.random.normal(0, 0.007)
            lon = center[1] + np.random.normal(0, 0.007)
            location_label = center[3]
        else:
            # Dispersed within greater metro bounds
            lat = 12.85 + random.random() * (13.06 - 12.85)
            lon = 77.52 + random.random() * (77.75 - 77.52)
            location_label = "Urban Roadway"

        # Time distribution (more incidents late evening/night 19:00 - 03:00)
        if random.random() < 0.65:
            # Evening / Night hours
            hour = random.choice([19, 20, 21, 22, 23, 0, 1, 2, 3])
        else:
            # Day / Afternoon hours
            hour = random.choice([6, 8, 10, 12, 14, 16, 17, 18])

        is_night = 1 if (hour >= 20 or hour <= 5) else 0
        lighting = random.choice(inc_info["lighting"])
        if is_night and lighting > 2 and random.random() < 0.6:
            lighting = 1

        # Severity with slight variance
        severity = min(10, max(1, inc_info["base_sev"] + random.choice([-1, 0, 1, 2])))
        
        # Calculate approximate distance to nearest emergency (km)
        # Using simple euclidean scaled roughly to km (1 deg ~ 111 km)
        approx_police_dist = round(abs(np.random.normal(1.8, 0.9)), 2)
        approx_hospital_dist = round(abs(np.random.normal(2.2, 1.1)), 2)

        # Risk Score target for ML training (0 to 100)
        # Higher severity, lower lighting, night time, and distance from police increase risk
        base_risk = (severity * 6.5) + (is_night * 15) + ((5 - lighting) * 4) + (approx_police_dist * 2.5)
        risk_score = round(min(100.0, max(5.0, base_risk + np.random.normal(0, 3))), 1)

        records.append({
            "incident_id": f"INC-{1000 + i}",
            "incident_type": inc_info["type"],
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "hour_of_day": hour,
            "is_night": is_night,
            "lighting_quality": lighting,
            "severity": severity,
            "proximity_police_km": approx_police_dist,
            "proximity_hospital_km": approx_hospital_dist,
            "location_desc": location_label,
            "risk_score": risk_score
        })

    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} crime records successfully at {output_path}")
    return df

if __name__ == "__main__":
    generate_crime_dataset()
