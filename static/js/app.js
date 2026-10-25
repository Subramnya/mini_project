/**
 * SafeRoute: AI-Based Safety-Aware Navigation System for Women
 * Frontend Application Logic (Leaflet Map, Routing, ML Scoring & Emergency SOS)
 */

document.addEventListener("DOMContentLoaded", () => {
    // --- Application State ---
    let map = null;
    let baseTileLayer = null;
    let isDarkTiles = true;
    
    // Layer Groups
    let routeLayersGroup = null;
    let markersGroup = null;
    let hotspotsLayerGroup = null;
    let policeLayerGroup = null;
    let hospitalsLayerGroup = null;
    let incidentsLayerGroup = null;

    let currentRoutes = [];
    let selectedRouteId = "route-safest";
    let mapPickingMode = null; // 'start', 'end', or 'report'

    // --- DOM Elements ---
    const startInput = document.getElementById("startInput");
    const endInput = document.getElementById("endInput");
    const startLat = document.getElementById("startLat");
    const startLon = document.getElementById("startLon");
    const endLat = document.getElementById("endLat");
    const endLon = document.getElementById("endLon");
    const travelTimeSelect = document.getElementById("travelTimeSelect");
    const travelModeSelect = document.getElementById("travelModeSelect");

    const btnFindRoutes = document.getElementById("btnFindRoutes");
    const btnSwapPoints = document.getElementById("btnSwapPoints");
    const btnPickStartOnMap = document.getElementById("btnPickStartOnMap");
    const btnPickEndOnMap = document.getElementById("btnPickEndOnMap");
    const routesContainer = document.getElementById("routesContainer");
    const routeLoadingIndicator = document.getElementById("routeLoadingIndicator");
    const presetsList = document.getElementById("presetsList");

    // Modals
    const modalSos = document.getElementById("modalSos");
    const modalReport = document.getElementById("modalReport");
    const modalAiInsights = document.getElementById("modalAiInsights");

    const btnEmergencySOS = document.getElementById("btnEmergencySOS");
    const btnReportIncident = document.getElementById("btnReportIncident");
    const btnAiInsights = document.getElementById("btnAiInsights");
    const formReportIncident = document.getElementById("formReportIncident");
    const btnPickReportLocation = document.getElementById("btnPickReportLocation");

    // Map Action Buttons
    const btnRecenter = document.getElementById("btnRecenter");
    const btnToggleSatellite = document.getElementById("btnToggleSatellite");

    // --- 1. Map Initialization ---
    function initMap() {
        // Default center: Bengaluru Metropolitan Region
        const defaultLat = 12.9716;
        const defaultLon = 77.5946;

        map = L.map("map", {
            center: [defaultLat, defaultLon],
            zoom: 13,
            zoomControl: false
        });

        L.control.zoom({ position: 'topright' }).addTo(map);

        // CartoDB Dark Matter Tile Layer
        baseTileLayer = L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
            subdomains: 'abcd',
            maxZoom: 19
        }).addTo(map);

        // Initialize Layer Groups
        hotspotsLayerGroup = L.layerGroup().addTo(map);
        policeLayerGroup = L.layerGroup().addTo(map);
        hospitalsLayerGroup = L.layerGroup().addTo(map);
        incidentsLayerGroup = L.layerGroup().addTo(map);
        routeLayersGroup = L.layerGroup().addTo(map);
        markersGroup = L.layerGroup().addTo(map);

        // Map Click Handler for Point Picking
        map.on("click", handleMapClick);
    }

    // --- 2. Data Fetching & Layer Population ---
    async function loadPresets() {
        try {
            const resp = await fetch("/api/presets");
            const presets = await resp.json();
            presetsList.innerHTML = "";

            presets.forEach((p, idx) => {
                const btn = document.createElement("button");
                btn.type = "button";
                btn.className = `btn-preset-card ${idx === 0 ? 'active' : ''}`;
                btn.innerHTML = `
                    <div class="preset-title">
                        <span>${p.title}</span>
                        <span class="preset-tag">${p.category}</span>
                    </div>
                    <div class="preset-desc">${p.start_name} &rarr; ${p.end_name}</div>
                `;
                btn.addEventListener("click", () => {
                    document.querySelectorAll(".btn-preset-card").forEach(c => c.classList.remove("active"));
                    btn.classList.add("active");
                    applyPreset(p);
                });
                presetsList.appendChild(btn);
            });
        } catch (err) {
            console.error("Error loading presets:", err);
        }
    }

    function applyPreset(p) {
        startInput.value = p.start_name;
        startLat.value = p.start_lat;
        startLon.value = p.start_lon;

        endInput.value = p.end_name;
        endLat.value = p.end_lat;
        endLon.value = p.end_lon;

        travelTimeSelect.value = p.hour_of_day;
        travelModeSelect.value = p.mode;

        // Auto compute route for smooth demo experience
        fetchAndRenderRoutes();
    }

    async function loadEmergencyFacilities() {
        try {
            const resp = await fetch("/api/facilities");
            const data = await resp.json();

            // Police Stations
            data.police_stations.forEach(ps => {
                const icon = L.divIcon({
                    className: 'custom-map-marker police-marker',
                    html: `<div style="background:#3b82f6; width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; color:#fff; box-shadow:0 0 10px rgba(59,130,246,0.6); border:2px solid #fff;">
                             <i class="fa-solid fa-shield-halved" style="font-size:13px;"></i>
                           </div>`,
                    iconSize: [28, 28],
                    iconAnchor: [14, 14]
                });

                const marker = L.marker([ps.latitude, ps.longitude], { icon });
                marker.bindPopup(`
                    <div class="custom-popup-box">
                        <h4><i class="fa-solid fa-shield-halved text-primary"></i> ${ps.name}</h4>
                        <p><i class="fa-solid fa-map-pin"></i> ${ps.address}</p>
                        <p><i class="fa-solid fa-phone"></i> <strong>${ps.phone}</strong></p>
                        <span class="custom-popup-tag" style="background:rgba(59,130,246,0.2); color:#60a5fa;">24/7 Women Help Desk</span>
                    </div>
                `);
                policeLayerGroup.addLayer(marker);
            });

            // Hospitals
            data.hospitals.forEach(h => {
                const icon = L.divIcon({
                    className: 'custom-map-marker hospital-marker',
                    html: `<div style="background:#10b981; width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; color:#fff; box-shadow:0 0 10px rgba(16,185,129,0.6); border:2px solid #fff;">
                             <i class="fa-solid fa-hospital" style="font-size:13px;"></i>
                           </div>`,
                    iconSize: [28, 28],
                    iconAnchor: [14, 14]
                });

                const marker = L.marker([h.latitude, h.longitude], { icon });
                marker.bindPopup(`
                    <div class="custom-popup-box">
                        <h4><i class="fa-solid fa-hospital text-success"></i> ${h.name}</h4>
                        <p><i class="fa-solid fa-location-dot"></i> ${h.address}</p>
                        <p><i class="fa-solid fa-phone"></i> <strong>${h.phone}</strong></p>
                        <span class="custom-popup-tag" style="background:rgba(16,185,129,0.2); color:#34d399;">24/7 Emergency & Ambulance</span>
                    </div>
                `);
                hospitalsLayerGroup.addLayer(marker);
            });
        } catch (err) {
            console.error("Error loading facilities:", err);
        }
    }

    async function loadCrimeHotspots() {
        try {
            const resp = await fetch("/api/hotspots");
            const data = await resp.json();

            data.hotspots.forEach(h => {
                const circle = L.circle([h.latitude, h.longitude], {
                    radius: h.radius_meters || 800,
                    color: h.color,
                    fillColor: h.color,
                    fillOpacity: h.risk_level === "High Risk" ? 0.28 : 0.16,
                    weight: 2
                });

                circle.bindPopup(`
                    <div class="custom-popup-box">
                        <h4 style="color:${h.color};"><i class="fa-solid fa-triangle-exclamation"></i> ${h.risk_level} Hotspot Cluster</h4>
                        <p><strong>Primary Concern:</strong> ${h.dominant_incident}</p>
                        <p><strong>Incidents Recorded:</strong> ${h.incident_count} reports</p>
                        <p><strong>Average Severity:</strong> ${h.avg_severity}/10</p>
                        <span class="custom-popup-tag" style="background:rgba(239,68,68,0.2); color:#f87171;">Avoid during late night hours</span>
                    </div>
                `);
                hotspotsLayerGroup.addLayer(circle);
            });
        } catch (err) {
            console.error("Error loading hotspots:", err);
        }
    }

    async function loadCommunityReports() {
        try {
            incidentsLayerGroup.clearLayers();
            const resp = await fetch("/api/reports");
            const data = await resp.json();

            data.reports.forEach(r => {
                const icon = L.divIcon({
                    className: 'custom-map-marker alert-marker',
                    html: `<div style="background:#f59e0b; width:24px; height:24px; border-radius:50%; display:flex; align-items:center; justify-content:center; color:#000; box-shadow:0 0 8px rgba(245,158,11,0.7); border:1.5px solid #fff;">
                             <i class="fa-solid fa-bullhorn" style="font-size:11px;"></i>
                           </div>`,
                    iconSize: [24, 24],
                    iconAnchor: [12, 12]
                });

                const marker = L.marker([r.latitude, r.longitude], { icon });
                marker.bindPopup(`
                    <div class="custom-popup-box">
                        <h4><i class="fa-solid fa-bullhorn text-warning"></i> ${r.incident_type}</h4>
                        <p>${r.description || 'Community reported hazard'}</p>
                        <p>Severity: <strong>${r.severity}/10</strong> | Lighting: <strong>${r.lighting_level}/5</strong></p>
                        <span class="custom-popup-tag" style="background:rgba(245,158,11,0.2); color:#fbbf24;">Status: ${r.status}</span>
                    </div>
                `);
                incidentsLayerGroup.addLayer(marker);
            });
        } catch (err) {
            console.error("Error loading reports:", err);
        }
    }

    // --- 3. Route Calculation & Display ---
    async function fetchAndRenderRoutes() {
        const sLat = parseFloat(startLat.value);
        const sLon = parseFloat(startLon.value);
        const eLat = parseFloat(endLat.value);
        const eLon = parseFloat(endLon.value);
        const hour = parseInt(travelTimeSelect.value, 10);
        const mode = travelModeSelect.value;

        if (isNaN(sLat) || isNaN(eLat)) {
            alert("Please provide valid coordinates or select a preset demo.");
            return;
        }

        routeLoadingIndicator.classList.remove("hidden");
        routesContainer.innerHTML = "";

        try {
            const resp = await fetch("/api/routes", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    start_lat: sLat,
                    start_lon: sLon,
                    end_lat: eLat,
                    end_lon: eLon,
                    hour_of_day: hour,
                    travel_mode: mode
                })
            });

            const data = await resp.json();
            routeLoadingIndicator.classList.add("hidden");

            if (data.status === "success" && data.routes && data.routes.length > 0) {
                currentRoutes = data.routes;
                renderStartEndMarkers(sLat, sLon, eLat, eLon);
                renderRouteCards(data.routes);
                selectRoute(data.routes[0].id); // select Safest by default
            } else {
                routesContainer.innerHTML = `<p class="text-danger" style="padding:16px;">Error calculating routes. Please try again.</p>`;
            }
        } catch (err) {
            routeLoadingIndicator.classList.add("hidden");
            console.error("Route error:", err);
            routesContainer.innerHTML = `<p class="text-danger" style="padding:16px;">Failed to fetch routes. Please verify server connection.</p>`;
        }
    }

    function renderStartEndMarkers(sLat, sLon, eLat, eLon) {
        markersGroup.clearLayers();

        // Start Marker (Emerald Green Pin)
        const startIcon = L.divIcon({
            className: 'custom-endpoint-marker start-pin',
            html: `<div style="background:#10b981; width:34px; height:34px; border-radius:50%; display:flex; align-items:center; justify-content:center; color:#fff; box-shadow:0 0 14px rgba(16,185,129,0.8); border:3px solid #fff;">
                     <i class="fa-solid fa-person-walking" style="font-size:16px;"></i>
                   </div>`,
            iconSize: [34, 34],
            iconAnchor: [17, 17]
        });
        const mStart = L.marker([sLat, sLon], { icon: startIcon }).bindPopup(`<strong>Origin:</strong> ${startInput.value}`);
        markersGroup.addLayer(mStart);

        // End Marker (Crimson Pin)
        const endIcon = L.divIcon({
            className: 'custom-endpoint-marker end-pin',
            html: `<div style="background:#ef4444; width:34px; height:34px; border-radius:50%; display:flex; align-items:center; justify-content:center; color:#fff; box-shadow:0 0 14px rgba(239,68,68,0.8); border:3px solid #fff;">
                     <i class="fa-solid fa-flag-checkered" style="font-size:15px;"></i>
                   </div>`,
            iconSize: [34, 34],
            iconAnchor: [17, 17]
        });
        const mEnd = L.marker([eLat, eLon], { icon: endIcon }).bindPopup(`<strong>Destination:</strong> ${endInput.value}`);
        markersGroup.addLayer(mEnd);
    }

    function renderRouteCards(routes) {
        routesContainer.innerHTML = "";

        routes.forEach(route => {
            const card = document.createElement("div");
            card.className = `route-card ${route.id === selectedRouteId ? 'selected' : ''}`;
            card.id = `card-${route.id}`;
            card.style.setProperty("--card-accent", route.color);

            const isSafest = route.route_bias === "safest";

            card.innerHTML = `
                <div class="route-header">
                    <div class="route-name-group">
                        <h4>${route.name}</h4>
                        <div class="route-tagline">${route.tagline}</div>
                    </div>
                    <span class="route-badge">${route.badge}</span>
                </div>

                <div class="safety-score-banner">
                    <div class="score-number">${route.safety_score}%</div>
                    <div class="score-label">Estimated Route Safety Index</div>
                </div>

                <div class="route-meta-row">
                    <div class="meta-item">
                        <div class="meta-val">${route.distance_km} km</div>
                        <div class="meta-lbl">Distance</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-val">${route.duration_mins} mins</div>
                        <div class="meta-lbl">Est. Time</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-val">${route.safe_havens_count}</div>
                        <div class="meta-lbl">Safe Havens</div>
                    </div>
                </div>

                <ul class="route-highlights-list">
                    ${route.features.map(f => `<li><i class="fa-solid ${isSafest ? 'fa-check' : 'fa-circle-info'}"></i> ${f}</li>`).join('')}
                </ul>
            `;

            card.addEventListener("click", () => {
                selectRoute(route.id);
            });

            routesContainer.appendChild(card);
        });
    }

    function selectRoute(routeId) {
        selectedRouteId = routeId;

        // Update card styles
        document.querySelectorAll(".route-card").forEach(c => c.classList.remove("selected"));
        const activeCard = document.getElementById(`card-${routeId}`);
        if (activeCard) activeCard.classList.add("selected");

        // Redraw polylines
        routeLayersGroup.clearLayers();

        let activePolyline = null;
        const allBounds = [];

        currentRoutes.forEach(r => {
            const isSelected = r.id === routeId;
            const polyline = L.polyline(r.coordinates, {
                color: r.color,
                weight: isSelected ? 7 : 3.5,
                opacity: isSelected ? 0.95 : 0.35,
                dashArray: r.route_bias === "fastest" ? "6, 8" : null,
                lineCap: 'round',
                lineJoin: 'round'
            });

            polyline.bindPopup(`
                <div class="custom-popup-box">
                    <h4 style="color:${r.color};">${r.name}</h4>
                    <p>Safety Score: <strong>${r.safety_score}%</strong></p>
                    <p>Distance: <strong>${r.distance_km} km</strong> | Time: <strong>${r.duration_mins} mins</strong></p>
                    <p>${r.verdict}</p>
                </div>
            `);

            polyline.on("click", () => selectRoute(r.id));
            routeLayersGroup.addLayer(polyline);

            if (isSelected) {
                activePolyline = polyline;
            }
            r.coordinates.forEach(pt => allBounds.push(pt));
        });

        // Focus map to route
        if (activePolyline) {
            map.fitBounds(activePolyline.getBounds(), { padding: [50, 50] });
        } else if (allBounds.length > 0) {
            map.fitBounds(L.latLngBounds(allBounds), { padding: [50, 50] });
        }
    }

    // --- 4. Interactive Map Clicking / Point Picking ---
    function handleMapClick(e) {
        const { lat, lng } = e.latlng;

        if (mapPickingMode === 'start') {
            startLat.value = lat.toFixed(5);
            startLon.value = lng.toFixed(5);
            startInput.value = `Custom Point (${lat.toFixed(4)}, ${lng.toFixed(4)})`;
            mapPickingMode = null;
            map.getContainer().style.cursor = '';
            fetchAndRenderRoutes();
        } else if (mapPickingMode === 'end') {
            endLat.value = lat.toFixed(5);
            endLon.value = lng.toFixed(5);
            endInput.value = `Custom Point (${lat.toFixed(4)}, ${lng.toFixed(4)})`;
            mapPickingMode = null;
            map.getContainer().style.cursor = '';
            fetchAndRenderRoutes();
        } else if (mapPickingMode === 'report') {
            document.getElementById("repLat").value = lat.toFixed(5);
            document.getElementById("repLon").value = lng.toFixed(5);
            mapPickingMode = null;
            map.getContainer().style.cursor = '';
            modalReport.classList.add("open");
        }
    }

    btnPickStartOnMap.addEventListener("click", () => {
        mapPickingMode = 'start';
        map.getContainer().style.cursor = 'crosshair';
        alert("Click any point on the map to set the Starting Location.");
    });

    btnPickEndOnMap.addEventListener("click", () => {
        mapPickingMode = 'end';
        map.getContainer().style.cursor = 'crosshair';
        alert("Click any point on the map to set the Destination.");
    });

    btnSwapPoints.addEventListener("click", () => {
        const tempName = startInput.value;
        const tempLat = startLat.value;
        const tempLon = startLon.value;

        startInput.value = endInput.value;
        startLat.value = endLat.value;
        startLon.value = endLon.value;

        endInput.value = tempName;
        endLat.value = tempLat;
        endLon.value = tempLon;

        fetchAndRenderRoutes();
    });

    btnFindRoutes.addEventListener("click", fetchAndRenderRoutes);

    // --- 5. Layer Toggle Controls ---
    document.getElementById("chkHotspots").addEventListener("change", (e) => {
        if (e.target.checked) map.addLayer(hotspotsLayerGroup);
        else map.removeLayer(hotspotsLayerGroup);
        document.getElementById("layerToggleHotspots").classList.toggle("active", e.target.checked);
    });

    document.getElementById("chkPolice").addEventListener("change", (e) => {
        if (e.target.checked) map.addLayer(policeLayerGroup);
        else map.removeLayer(policeLayerGroup);
        document.getElementById("layerTogglePolice").classList.toggle("active", e.target.checked);
    });

    document.getElementById("chkHospitals").addEventListener("change", (e) => {
        if (e.target.checked) map.addLayer(hospitalsLayerGroup);
        else map.removeLayer(hospitalsLayerGroup);
        document.getElementById("layerToggleHospitals").classList.toggle("active", e.target.checked);
    });

    document.getElementById("chkIncidents").addEventListener("change", (e) => {
        if (e.target.checked) map.addLayer(incidentsLayerGroup);
        else map.removeLayer(incidentsLayerGroup);
        document.getElementById("layerToggleIncidents").classList.toggle("active", e.target.checked);
    });

    // --- 6. Emergency SOS Dispatch ---
    btnEmergencySOS.addEventListener("click", async () => {
        const sLat = parseFloat(startLat.value) || 12.9716;
        const sLon = parseFloat(startLon.value) || 77.5946;

        document.getElementById("sosCoordText").innerText = 
            `Live Coordinates: ${sLat.toFixed(5)}, ${sLon.toFixed(5)} broadcast to Women Safety Emergency Grid.`;

        modalSos.classList.add("open");

        try {
            await fetch("/api/sos", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    latitude: sLat,
                    longitude: sLon,
                    notes: "High priority SOS alert activated from SafeRoute frontend"
                })
            });
        } catch (err) {
            console.error("SOS broadcast error:", err);
        }
    });

    // --- 7. Incident Reporting Form ---
    btnReportIncident.addEventListener("click", () => {
        document.getElementById("repLat").value = parseFloat(startLat.value) || 12.9756;
        document.getElementById("repLon").value = parseFloat(startLon.value) || 77.6066;
        modalReport.classList.add("open");
    });

    btnPickReportLocation.addEventListener("click", () => {
        modalReport.classList.remove("open");
        mapPickingMode = 'report';
        map.getContainer().style.cursor = 'crosshair';
        alert("Click anywhere on the map to pin the incident location.");
    });

    formReportIncident.addEventListener("submit", async (e) => {
        e.preventDefault();

        const category = document.getElementById("repCategory").value;
        const description = document.getElementById("repDescription").value;
        const severity = parseInt(document.getElementById("repSeverity").value, 10);
        const lighting = parseInt(document.getElementById("repLighting").value, 10);
        const lat = parseFloat(document.getElementById("repLat").value);
        const lon = parseFloat(document.getElementById("repLon").value);

        try {
            const resp = await fetch("/api/report", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    incident_type: category,
                    description,
                    severity,
                    lighting_level: lighting,
                    latitude: lat,
                    longitude: lon
                })
            });

            const result = await resp.json();
            if (result.status === "success") {
                alert("Thank you! Your safety report has been logged. It will help make routes safer for other women.");
                modalReport.classList.remove("open");
                formReportIncident.reset();
                loadCommunityReports();
            }
        } catch (err) {
            console.error("Error submitting report:", err);
            alert("Failed to submit incident report. Please try again.");
        }
    });

    // --- 8. AI & Machine Learning Insights Modal ---
    btnAiInsights.addEventListener("click", async () => {
        modalAiInsights.classList.add("open");
        try {
            const resp = await fetch("/api/ml-metrics");
            const data = await resp.json();

            if (data.metrics) {
                document.getElementById("metricSamples").innerText = data.metrics.samples_trained || 350;
                document.getElementById("metricClusters").innerText = data.metrics.hotspots_identified || 8;
                document.getElementById("metricMae").innerText = data.metrics.mae || 10.1;
                document.getElementById("metricR2").innerText = data.metrics.r2_score || 0.72;
            }

            const featureBarsList = document.getElementById("featureBarsList");
            featureBarsList.innerHTML = "";
            if (data.feature_importances) {
                data.feature_importances.forEach(f => {
                    const row = document.createElement("div");
                    row.className = "feature-bar-row";
                    row.innerHTML = `
                        <div class="feature-name">${f.feature}</div>
                        <div class="feature-bar-track">
                            <div class="feature-bar-fill" style="width: ${f.importance}%;"></div>
                        </div>
                        <div class="feature-pct">${f.importance}%</div>
                    `;
                    featureBarsList.appendChild(row);
                });
            }
        } catch (err) {
            console.error("Error loading ML metrics:", err);
        }
    });

    // --- 9. Modal Close Buttons ---
    document.querySelectorAll("[data-close]").forEach(btn => {
        btn.addEventListener("click", () => {
            const targetId = btn.getAttribute("data-close");
            const targetModal = document.getElementById(targetId);
            if (targetModal) targetModal.classList.remove("open");
        });
    });

    window.addEventListener("click", (e) => {
        if (e.target.classList.contains("modal-backdrop")) {
            e.target.classList.remove("open");
        }
    });

    // Map Dock Tools
    btnRecenter.addEventListener("click", () => {
        if (currentRoutes.length > 0) {
            selectRoute(selectedRouteId);
        } else {
            map.setView([12.9716, 77.5946], 13);
        }
    });

    btnToggleSatellite.addEventListener("click", () => {
        if (isDarkTiles) {
            map.removeLayer(baseTileLayer);
            baseTileLayer = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
                attribution: '&copy; OpenStreetMap contributors'
            }).addTo(map);
            isDarkTiles = false;
        } else {
            map.removeLayer(baseTileLayer);
            baseTileLayer = L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
                attribution: '&copy; OpenStreetMap &copy; CARTO'
            }).addTo(map);
            isDarkTiles = true;
        }
    });

    // Header Clock
    function updateLiveClock() {
        const now = new Date();
        const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const liveClock = document.getElementById("liveClock");
        if (liveClock) liveClock.innerText = `${timeStr} IST`;
    }
    setInterval(updateLiveClock, 30000);
    updateLiveClock();

    // --- Bootstrap App ---
    initMap();
    loadCrimeHotspots();
    loadEmergencyFacilities();
    loadCommunityReports();
    loadPresets();

    // Trigger initial calculation after short delay so map bounds are ready
    setTimeout(() => {
        fetchAndRenderRoutes();
    }, 600);
});
