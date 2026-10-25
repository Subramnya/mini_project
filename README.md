# SafeRoute: AI-Based Safety-Aware Navigation System for Women

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask%203.x-lightgrey.svg)](https://flask.palletsprojects.com/)
[![Machine Learning](https://img.shields.io/badge/ML-Scikit--Learn-orange.svg)](https://scikit-learn.org/)
[![Mapping](https://img.shields.io/badge/Maps-OpenStreetMap%20%7C%20Leaflet.js-green.svg)](https://leafletjs.com/)
[![License](https://img.shields.io/badge/Status-Base%20Model%20(Gamma)-purple.svg)](#)

---

## 1. Project Title
**SafeRoute: AI-Based Safety-Aware Navigation System for Women**

---

## 2. Introduction
Conventional navigation systems primarily suggest routes based on distance, travel time, and traffic, without considering safety-related factors. As a result, the shortest or fastest route may pass through poorly-lit corridors, isolated stretches, or areas with a higher history of reported crimes and safety concerns.

**SafeRoute** is an AI-based safety-aware navigation system designed to estimate the relative risk of different road segments by analyzing historical crime data, geographical locations, lighting indices, safe haven proximity, and time-related patterns. It compares available routes based on **safety, distance, and travel time**, and presents their safety levels on an interactive map.

The concept builds upon research in safety-aware routing, notably the **SafeRoute research by Levy et al.** and recent advances in women safety navigation platforms.

---

## 3. Problem Statement
Existing navigation platforms prioritize route minimization (distance and time) and rarely integrate historical incident data or infrastructure safety factors (such as street lighting and proximity to emergency support) as primary routing criteria.

Consequently, users—especially women traveling alone or late at night—may be directed through higher-risk areas. SafeRoute addresses this critical gap by computing an estimated safety/risk score for alternative routes, empowering users to make informed travel choices.

---

## 4. Key Objectives
- **Safety-Aware Route Comparison**: Generate and compare alternative routes between any origin and destination based on estimated safety risk, distance, and travel time.
- **Historical Data & Crime Hotspot Analysis**: Identify geographical crime concentrations using **K-Means clustering** (Low, Medium, High risk clusters).
- **Machine Learning Risk Estimation**: Apply **Random Forest Regressor** to predict risk levels for road segments based on coordinates, hour of day, lighting, and proximity to police stations/hospitals.
- **Interactive Map Visualization**: Display routes with color-coded safety indices (Safest: Green, Balanced: Amber, Direct: Red) using Leaflet.js and OpenStreetMap.
- **Emergency Infrastructure Layer**: Display nearby police stations (with women's help desks) and 24/7 hospitals.
- **Emergency SOS & Crowdsourcing**: Provide 1-click simulated SOS emergency broadcast and a community incident reporting portal.

---

## 5. System Architecture & Methodology

```
+-----------------------------------------------------------------------------------+
|                                SafeRoute Frontend                                 |
|  (Interactive Leaflet.js Map | Route Cards | SOS Modal | Incident Reporting Form) |
+------------------------------------------+----------------------------------------+
                                           | HTTP REST API
+------------------------------------------v----------------------------------------+
|                               Flask Application (app.py)                          |
+-------------------+----------------------+--------------------+-------------------+
                    |                      |                    |
+-------------------v----+   +-------------v------+   +---------v-------------------+
|  ML Engine             |   | Routing Engine     |   | SQLite Database             |
|  - K-Means Hotspots    |   | - OSRM Routing API |   | (saferoute.db)              |
|  - Random Forest Risk  |   | - Fallback Graph   |   | - Community Incident Logs   |
|  - Segment Evaluator   |   | - Waypoint Offset  |   | - Emergency SOS History     |
+------------------------+   +--------------------+   +-----------------------------+
```

### Proposed Methodology Breakdown
1. **User Input & Travel Conditions**:
   - Source & destination selection (via address search, 1-click presets, or clicking directly on the interactive map).
   - Travel time specification (Daytime, Dusk, Night, Late Night, Midnight) and mode (Walking or Driving).
2. **Data Processing & Hotspot Detection**:
   - Historical crime dataset (`data/crime_dataset.csv`) cleaned and vectorized with features: `[latitude, longitude, hour_of_day, is_night, lighting_quality, proximity_police_km, proximity_hospital_km]`.
   - **K-Means Unsupervised Clustering** discovers incident centroids and danger radii.
3. **ML Risk Scoring**:
   - **Random Forest Regressor** predicts risk scores (0 to 100).
   - Penalties applied when a segment intersects a high-density crime cluster.
4. **Multi-Route Generation**:
   - **Safest Route (Green)**: Steers through well-lit, highly patrolled corridors; bypasses crime hotspots.
   - **Balanced Route (Amber)**: Tradeoff between travel duration and safety score.
   - **Fastest / Direct Route (Red)**: Shortest path, but potentially higher risk.
5. **Emergency & Incident Support**:
   - Real-time emergency helpline quick-dials: **112** (National Emergency), **1091** (Women Helpline), **100** (Police), **108** (Ambulance).
   - Crowdsourced hazard submission persists to SQLite and immediately refreshes the active map.

---

## 6. Project Structure

```
mini_project/
├── app.py                      # Flask backend & REST API endpoints
├── ml_engine.py                # K-Means clustering & Random Forest risk scorer
├── routing_engine.py           # Multi-route generator with OSRM & safety scoring
├── database.py                 # SQLite database manager for incidents & SOS
├── generate_data.py            # Dataset generator for historical incidents
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore rules
├── README.md                   # Complete project documentation
├── data/
│   ├── crime_dataset.csv       # Preprocessed crime incidents dataset
│   └── emergency_facilities.json # Police stations and 24/7 hospitals
├── templates/
│   └── index.html              # Responsive web application interface
├── static/
│   ├── css/
│   │   └── style.css           # Premium dark theme design system
│   └── js/
│       └── app.js              # Leaflet map, polyline renderer, SOS & events
└── tests/
    └── test_app.py             # Automated unit & integration tests
```

---

## 7. Quick Start & Installation

### Prerequisites
- Python 3.10 or higher
- Git

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Subramnya/mini_project.git
   cd mini_project
   ```

2. **(Optional) Create a virtual environment:**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   ```

3. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize database & generate sample dataset (if not already present):**
   ```bash
   python generate_data.py
   python database.py
   ```

5. **Run the Automated Tests:**
   ```bash
   python -m unittest tests/test_app.py
   ```

6. **Start the SafeRoute Web Application:**
   ```bash
   python app.py
   ```

7. **Open in your browser:**
   ```
   http://127.0.0.1:5000
   ```

---

## 8. Interactive Features in the Base Model

- **1-Click Demo Scenarios**:
  - *Late Night Commute*: Metro Station to Tech Park (bypasses dark alleys in favor of 100ft road).
  - *Evening Walk*: University Campus to Women's Hostel (prioritizes well-lit pedestrian corridors).
  - *Emergency Transit*: Railway Station to Hospital (steers clear of dense underpasses).
  - *Suburban Transit*: HSR Layout to Silk Board.
- **Interactive Leaflet Map**:
  - Click any point on the map to set origin, destination, or pinpoint incident locations.
  - Interactive layer toggles for **Crime Hotspots**, **Police Booths**, **Hospitals**, and **Community Reports**.
  - Polyline inspection with safety scores, travel time, and distance.
- **Emergency SOS Dispatcher**:
  - Displays instant GPS coordinates broadcast.
  - Direct links to national helplines: 112, 1091, 100, 108.
- **AI Insights Inspector**:
  - Live inspection modal displaying Random Forest MAE, $R^2$ score, cluster counts, and feature importance rankings.

---

## 9. References & Literature
- **Levy et al.**: SafeRoute navigation combining safety risk metrics and route efficiency.
- **Women Safe Route Navigation (2025)**: Spatiotemporal crime clustering, lighting indices, and route risk evaluation.
- **OpenStreetMap & OSRM**: Open source routing machine for spatial geometry and graph queries.

---

## 10. License & Disclaimer
This is an academic research prototype developed as a mini-project. The system calculates estimated relative risk based on available historical data and does not guarantee absolute safety.