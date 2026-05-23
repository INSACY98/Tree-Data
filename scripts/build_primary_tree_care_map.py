from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "processed" / "primary_tree_care_providers.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "primary_tree_care_map.html"


MAP_FIELDS = [
    "provider_id",
    "species_common",
    "medical_specialty",
    "provider_type",
    "care_rating",
    "star_doctor",
    "weekend_availability",
    "next_available_visit_days",
    "care_accessibility_score",
    "clinic_address",
    "clinic_neighborhood",
    "clinic_latitude",
    "clinic_longitude",
    "signature_prescription",
    "waiting_room_feature",
]


def clean_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def load_map_rows(input_csv: Path) -> list[dict[str, object]]:
    df = pd.read_csv(input_csv, usecols=MAP_FIELDS)
    df = df.dropna(subset=["clinic_latitude", "clinic_longitude"]).copy()

    rows: list[dict[str, object]] = []
    for row in df.itertuples(index=False):
        item = row._asdict()
        rows.append(
            {
                "id": int(item["provider_id"]),
                "species": str(item["species_common"]),
                "specialty": str(item["medical_specialty"]),
                "type": str(item["provider_type"]),
                "rating": float(item["care_rating"]),
                "star": int(item["star_doctor"]),
                "weekend": clean_bool(item["weekend_availability"]),
                "wait": int(item["next_available_visit_days"]),
                "access": int(item["care_accessibility_score"]),
                "address": str(item["clinic_address"]),
                "neighborhood": str(item["clinic_neighborhood"]),
                "lat": round(float(item["clinic_latitude"]), 6),
                "lng": round(float(item["clinic_longitude"]), 6),
                "prescription": str(item["signature_prescription"]),
                "waiting": str(item["waiting_room_feature"]),
            }
        )
    return rows


def render_html(rows: list[dict[str, object]]) -> str:
    specialties = sorted({str(row["specialty"]) for row in rows})
    provider_types = sorted({str(row["type"]) for row in rows})
    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    specialties_json = json.dumps(specialties)
    provider_types_json = json.dumps(provider_types)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Primary Tree Care Map</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <style>
    :root {{
      --ink: #20312a;
      --muted: #66736d;
      --line: #d9e1dc;
      --panel: #fbfdfb;
      --green: #2f7d4f;
    }}
    html, body {{
      height: 100%;
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: #edf4ef;
    }}
    #app {{
      display: grid;
      grid-template-columns: minmax(280px, 360px) 1fr;
      height: 100%;
      min-height: 720px;
    }}
    aside {{
      background: var(--panel);
      border-right: 1px solid var(--line);
      padding: 18px;
      overflow: auto;
      box-shadow: 0 12px 32px rgba(17, 45, 32, 0.12);
      z-index: 500;
    }}
    h1 {{
      font-size: 22px;
      line-height: 1.15;
      margin: 0 0 8px;
    }}
    .subtitle, .legend {{
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
    }}
    .subtitle {{
      margin-bottom: 16px;
    }}
    .metric-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin: 14px 0 16px;
    }}
    .metric {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      background: white;
    }}
    .metric strong {{
      display: block;
      font-size: 20px;
      line-height: 1;
      color: var(--green);
    }}
    .metric span {{
      color: var(--muted);
      font-size: 12px;
    }}
    label {{
      display: block;
      font-size: 12px;
      font-weight: 700;
      margin: 12px 0 5px;
    }}
    select, input[type="search"], input[type="range"] {{
      width: 100%;
      box-sizing: border-box;
    }}
    select, input[type="search"] {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 9px 10px;
      background: white;
      color: var(--ink);
      font-size: 14px;
    }}
    .checks {{
      display: grid;
      gap: 8px;
      margin-top: 10px;
    }}
    .checks label {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 0;
      font-weight: 600;
      color: var(--ink);
    }}
    button {{
      width: 100%;
      margin-top: 14px;
      border: 0;
      border-radius: 8px;
      padding: 10px 12px;
      background: var(--green);
      color: white;
      font-weight: 800;
      cursor: pointer;
    }}
    #map {{
      width: 100%;
      height: 100%;
      min-height: 720px;
    }}
    .legend {{
      margin-top: 16px;
      border-top: 1px solid var(--line);
      padding-top: 12px;
    }}
    .popup h2 {{
      font-size: 16px;
      margin: 0 0 6px;
    }}
    .popup p {{
      margin: 5px 0;
    }}
    @media (max-width: 820px) {{
      #app {{
        display: block;
      }}
      aside {{
        border-right: 0;
        border-bottom: 1px solid var(--line);
        max-height: 46vh;
      }}
      #map {{
        height: 70vh;
        min-height: 520px;
      }}
    }}
  </style>
</head>
<body>
  <div id="app">
    <aside>
      <h1>Primary Tree Care Map</h1>
      <div class="subtitle">Clustered local map of NYC trees reimagined as public primary-care providers. Zoom in or filter to see individual trees.</div>

      <div class="metric-grid">
        <div class="metric"><strong id="matchCount">0</strong><span>matching trees</span></div>
        <div class="metric"><strong id="drawnCount">0</strong><span>drawn map items</span></div>
        <div class="metric"><strong id="avgRating">0.0</strong><span>avg care rating</span></div>
        <div class="metric"><strong id="starCount">0</strong><span>star doctors</span></div>
      </div>

      <label for="specialty">Specialty</label>
      <select id="specialty"></select>

      <label for="providerType">Provider Type</label>
      <select id="providerType"></select>

      <label for="search">Search Species, Neighborhood, ID</label>
      <input id="search" type="search" placeholder="ginkgo, Ridgewood, 208201" />

      <label for="rating">Minimum Care Rating: <span id="ratingValue">1.5</span></label>
      <input id="rating" type="range" min="1.5" max="5" step="0.1" value="1.5" />

      <div class="checks">
        <label><input id="starOnly" type="checkbox" /> Star doctors only</label>
        <label><input id="weekendOnly" type="checkbox" /> Weekend availability only</label>
      </div>

      <button id="reset">Reset Filters</button>

      <div class="legend">
        Large result sets are clustered for browser stability. Individual tree markers appear when you zoom in or narrow the filters.
      </div>
    </aside>
    <main id="map"></main>
  </div>

  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    const rows = {payload};
    const specialties = {specialties_json};
    const providerTypes = {provider_types_json};
    const maxIndividualMarkers = 1200;
    const specialtyColors = {{
      "Allergy/Immunology": "#d97706",
      "Cardiology": "#dc2626",
      "Dermatology": "#f97316",
      "Endocrinology": "#9333ea",
      "Family Medicine": "#16a34a",
      "Gastroenterology": "#a16207",
      "Geriatrics": "#64748b",
      "Internal Medicine": "#2563eb",
      "Neurology": "#7c3aed",
      "Pediatrics": "#db2777",
      "Preventive Medicine": "#059669",
      "Psychiatry": "#0891b2",
      "Pulmonology": "#0d9488",
      "Sports Medicine": "#65a30d",
      "Women's Health": "#e11d48"
    }};

    const map = L.map("map", {{ preferCanvas: true }}).setView([40.72, -73.94], 11);
    L.tileLayer("https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png", {{
      maxZoom: 19,
      attribution: "&copy; OpenStreetMap contributors"
    }}).addTo(map);

    const itemLayer = L.layerGroup().addTo(map);

    function optionList(select, values, label) {{
      select.innerHTML = "";
      const all = document.createElement("option");
      all.value = "";
      all.textContent = "All " + label;
      select.appendChild(all);
      values.forEach(value => {{
        const option = document.createElement("option");
        option.value = value;
        option.textContent = value;
        select.appendChild(option);
      }});
    }}

    optionList(document.getElementById("specialty"), specialties, "specialties");
    optionList(document.getElementById("providerType"), providerTypes, "provider types");

    function markerRadius(row) {{
      const base = 4 + Math.max(0, row.rating - 3) * 1.4;
      return row.star ? base + 3 : base;
    }}

    function treePopup(row) {{
      return '<div class="popup">' +
        '<h2>' + row.species + ' #' + row.id + '</h2>' +
        '<p><strong>' + row.specialty + '</strong> · ' + row.type + '</p>' +
        '<p><strong>Rating:</strong> ' + row.rating.toFixed(1) + ' · <strong>Access:</strong> ' + row.access + ' · <strong>Wait:</strong> ' + row.wait + ' days</p>' +
        '<p><strong>Weekend:</strong> ' + (row.weekend ? 'Yes' : 'Taking a break') + '</p>' +
        '<p><strong>Location:</strong> ' + row.address + ', ' + row.neighborhood + '</p>' +
        '<p><strong>Prescription:</strong> ' + row.prescription + '</p>' +
        '<p><strong>Waiting room:</strong> ' + row.waiting + '</p>' +
      '</div>';
    }}

    function clusterPopup(cluster) {{
      return '<div class="popup">' +
        '<h2>' + cluster.count.toLocaleString() + ' care trees</h2>' +
        '<p><strong>Dominant specialty:</strong> ' + cluster.specialty + '</p>' +
        '<p><strong>Avg rating:</strong> ' + cluster.avgRating.toFixed(1) + '</p>' +
        '<p><strong>Star doctors:</strong> ' + cluster.stars.toLocaleString() + '</p>' +
        '<p>Zoom in to inspect individual tree providers.</p>' +
      '</div>';
    }}

    function makeTreeMarker(row) {{
      const marker = L.circleMarker([row.lat, row.lng], {{
        renderer: L.canvas(),
        radius: markerRadius(row),
        color: row.star ? "#111827" : specialtyColors[row.specialty] || "#334155",
        weight: row.star ? 2.5 : 1,
        fillColor: specialtyColors[row.specialty] || "#334155",
        fillOpacity: row.star ? 0.92 : 0.68
      }});
      marker.bindPopup(treePopup(row), {{ maxWidth: 360 }});
      return marker;
    }}

    function makeClusterMarker(cluster) {{
      const radius = Math.min(28, 7 + Math.sqrt(cluster.count) * 1.7);
      const marker = L.circleMarker([cluster.lat, cluster.lng], {{
        renderer: L.canvas(),
        radius,
        color: "#18392b",
        weight: 1.5,
        fillColor: specialtyColors[cluster.specialty] || "#2f7d4f",
        fillOpacity: 0.72
      }});
      marker.bindTooltip(cluster.count.toLocaleString(), {{ permanent: true, direction: "center", className: "cluster-count" }});
      marker.bindPopup(clusterPopup(cluster), {{ maxWidth: 320 }});
      return marker;
    }}

    function matches(row) {{
      const specialty = document.getElementById("specialty").value;
      const type = document.getElementById("providerType").value;
      const query = document.getElementById("search").value.trim().toLowerCase();
      const minRating = Number(document.getElementById("rating").value);
      const starOnly = document.getElementById("starOnly").checked;
      const weekendOnly = document.getElementById("weekendOnly").checked;

      if (specialty && row.specialty !== specialty) return false;
      if (type && row.type !== type) return false;
      if (row.rating < minRating) return false;
      if (starOnly && !row.star) return false;
      if (weekendOnly && !row.weekend) return false;
      if (query) {{
        const haystack = (row.id + ' ' + row.species + ' ' + row.specialty + ' ' + row.type + ' ' + row.neighborhood).toLowerCase();
        if (!haystack.includes(query)) return false;
      }}
      return true;
    }}

    function inCurrentBounds(row) {{
      return map.getBounds().pad(0.08).contains([row.lat, row.lng]);
    }}

    function gridSizeForZoom(zoom) {{
      if (zoom <= 10) return 70;
      if (zoom <= 12) return 55;
      if (zoom <= 14) return 42;
      return 32;
    }}

    function buildClusters(items) {{
      const gridSize = gridSizeForZoom(map.getZoom());
      const buckets = new Map();
      items.forEach(row => {{
        const point = map.latLngToLayerPoint([row.lat, row.lng]);
        const key = Math.floor(point.x / gridSize) + ':' + Math.floor(point.y / gridSize);
        if (!buckets.has(key)) {{
          buckets.set(key, {{
            count: 0,
            latSum: 0,
            lngSum: 0,
            ratingSum: 0,
            stars: 0,
            specialties: {{}}
          }});
        }}
        const bucket = buckets.get(key);
        bucket.count += 1;
        bucket.latSum += row.lat;
        bucket.lngSum += row.lng;
        bucket.ratingSum += row.rating;
        bucket.stars += row.star ? 1 : 0;
        bucket.specialties[row.specialty] = (bucket.specialties[row.specialty] || 0) + 1;
      }});

      return Array.from(buckets.values()).map(bucket => {{
        let specialty = "Mixed";
        let specialtyCount = -1;
        Object.entries(bucket.specialties).forEach(([name, count]) => {{
          if (count > specialtyCount) {{
            specialty = name;
            specialtyCount = count;
          }}
        }});
        return {{
          count: bucket.count,
          lat: bucket.latSum / bucket.count,
          lng: bucket.lngSum / bucket.count,
          avgRating: bucket.ratingSum / bucket.count,
          stars: bucket.stars,
          specialty
        }};
      }});
    }}

    function updateMap() {{
      itemLayer.clearLayers();
      const filtered = rows.filter(matches);
      const inBounds = filtered.filter(inCurrentBounds);
      const showIndividuals = map.getZoom() >= 16 || inBounds.length <= maxIndividualMarkers;
      const drawn = showIndividuals ? inBounds : buildClusters(inBounds);

      drawn.forEach(item => {{
        itemLayer.addLayer(showIndividuals ? makeTreeMarker(item) : makeClusterMarker(item));
      }});

      const count = filtered.length;
      const rating = count ? filtered.reduce((sum, row) => sum + row.rating, 0) / count : 0;
      const stars = filtered.filter(row => row.star).length;

      document.getElementById("matchCount").textContent = count.toLocaleString();
      document.getElementById("drawnCount").textContent = drawn.length.toLocaleString();
      document.getElementById("avgRating").textContent = rating.toFixed(1);
      document.getElementById("starCount").textContent = stars.toLocaleString();
      document.getElementById("ratingValue").textContent = Number(document.getElementById("rating").value).toFixed(1);
    }}

    let updateTimer = null;
    function scheduleUpdate() {{
      clearTimeout(updateTimer);
      updateTimer = setTimeout(updateMap, 40);
    }}

    ["specialty", "providerType", "search", "rating", "starOnly", "weekendOnly"].forEach(id => {{
      document.getElementById(id).addEventListener("input", scheduleUpdate);
      document.getElementById(id).addEventListener("change", scheduleUpdate);
    }});
    map.on("moveend zoomend", scheduleUpdate);

    document.getElementById("reset").addEventListener("click", () => {{
      document.getElementById("specialty").value = "";
      document.getElementById("providerType").value = "";
      document.getElementById("search").value = "";
      document.getElementById("rating").value = "1.5";
      document.getElementById("starOnly").checked = false;
      document.getElementById("weekendOnly").checked = false;
      map.setView([40.72, -73.94], 11);
      updateMap();
    }});

    updateMap();
  </script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the local interactive Primary Tree Care map.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Input provider CSV.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output HTML map.")
    args = parser.parse_args()

    rows = load_map_rows(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_html(rows), encoding="utf-8")
    print(f"Wrote {args.output} with {len(rows):,} mapped trees")
    print(f"Open directly: {args.output.resolve().as_uri()}")
    print("Or from the project root run: python3 -m http.server 8000")
    print("Then open: http://localhost:8000/docs/primary_tree_care_map.html")


if __name__ == "__main__":
    main()
