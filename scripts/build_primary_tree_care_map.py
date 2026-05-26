from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "processed" / "primary_tree_care_providers2.csv"
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
    "clinic_neighborhood",
    "clinic_city",
    "clinic_latitude",
    "clinic_longitude",
]


def clean_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def top_species(values: pd.Series) -> str:
    counts = values.fillna("Unknown").value_counts().head(3)
    return ", ".join(f"{name} ({count})" for name, count in counts.items())


def pair_counts(values: pd.Series) -> list[list[object]]:
    counts = values.fillna("Unknown").value_counts()
    return [[str(name), int(count)] for name, count in counts.items()]


def load_map_groups(input_csv: Path) -> list[dict[str, object]]:
    df = pd.read_csv(input_csv, usecols=MAP_FIELDS)
    df = df.dropna(subset=["clinic_latitude", "clinic_longitude"]).copy()

    text_fields = [
        "species_common",
        "medical_specialty",
        "provider_type",
        "clinic_neighborhood",
        "clinic_city",
    ]
    for field in text_fields:
        df[field] = df[field].fillna("Unknown").astype(str)

    numeric_fields = [
        "care_rating",
        "next_available_visit_days",
        "care_accessibility_score",
        "clinic_latitude",
        "clinic_longitude",
    ]
    for field in numeric_fields:
        df[field] = pd.to_numeric(df[field], errors="coerce")

    df["star_doctor"] = df["star_doctor"].map(clean_bool).astype(int)
    df["weekend_availability"] = df["weekend_availability"].map(clean_bool).astype(int)

    location_keys = ["clinic_neighborhood", "clinic_city"]

    base = (
        df.groupby(location_keys, dropna=False)
        .agg(
            tree_count=("provider_id", "size"),
            latitude=("clinic_latitude", "mean"),
            longitude=("clinic_longitude", "mean"),
            avg_rating=("care_rating", "mean"),
            avg_wait_days=("next_available_visit_days", "mean"),
            avg_access=("care_accessibility_score", "mean"),
            star_count=("star_doctor", "sum"),
            weekend_count=("weekend_availability", "sum"),
            top_species=("species_common", top_species),
            specialties=("medical_specialty", pair_counts),
            provider_types=("provider_type", pair_counts),
        )
        .reset_index()
    )

    segment_rows = (
        df.groupby([*location_keys, "medical_specialty", "provider_type"], dropna=False)
        .agg(
            tree_count=("provider_id", "size"),
            avg_rating=("care_rating", "mean"),
            avg_wait_days=("next_available_visit_days", "mean"),
            avg_access=("care_accessibility_score", "mean"),
            star_count=("star_doctor", "sum"),
            weekend_count=("weekend_availability", "sum"),
        )
        .reset_index()
    )

    segments_by_location: dict[tuple[str, str], list[list[object]]] = {}
    for row in segment_rows.itertuples(index=False):
        key = (str(row.clinic_neighborhood), str(row.clinic_city))
        segments_by_location.setdefault(key, []).append(
            [
                str(row.medical_specialty),
                str(row.provider_type),
                int(row.tree_count),
                round(float(row.avg_rating), 2),
                round(float(row.avg_wait_days), 1),
                round(float(row.avg_access), 1),
                int(row.star_count),
                int(row.weekend_count),
            ]
        )

    rows: list[dict[str, object]] = []
    for row in base.itertuples(index=False):
        neighborhood = str(row.clinic_neighborhood)
        city = str(row.clinic_city)
        search_parts = [
            neighborhood,
            city,
            str(row.top_species),
            " ".join(name for name, _count in row.specialties),
            " ".join(name for name, _count in row.provider_types),
        ]
        rows.append(
            {
                "neighborhood": neighborhood,
                "city": city,
                "count": int(row.tree_count),
                "lat": round(float(row.latitude), 6),
                "lng": round(float(row.longitude), 6),
                "rating": round(float(row.avg_rating), 2),
                "wait": round(float(row.avg_wait_days), 1),
                "access": round(float(row.avg_access), 1),
                "stars": int(row.star_count),
                "weekends": int(row.weekend_count),
                "topSpecies": str(row.top_species),
                "specialties": row.specialties,
                "types": row.provider_types,
                "segments": segments_by_location.get((neighborhood, city), []),
                "searchText": " ".join(search_parts).lower(),
            }
        )
    return rows


def render_html(rows: list[dict[str, object]]) -> str:
    specialties = sorted({segment[0] for row in rows for segment in row["segments"]})
    provider_types = sorted({segment[1] for row in rows for segment in row["segments"]})
    payload = json.dumps(rows, ensure_ascii=True, separators=(",", ":"))
    specialties_json = json.dumps(specialties, ensure_ascii=True)
    provider_types_json = json.dumps(provider_types, ensure_ascii=True)

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
      <div class="subtitle">Neighborhood-level map of NYC trees reimagined as public primary-care providers. Filters update each neighborhood total without drawing one marker per tree.</div>

      <div class="metric-grid">
        <div class="metric"><strong id="treeCount">0</strong><span>matching trees</span></div>
        <div class="metric"><strong id="groupCount">0</strong><span>neighborhoods</span></div>
        <div class="metric"><strong id="avgRating">0.0</strong><span>weighted avg rating</span></div>
        <div class="metric"><strong id="starCount">0</strong><span>star doctors</span></div>
      </div>

      <label for="specialty">Specialty</label>
      <select id="specialty"></select>

      <label for="providerType">Provider Type</label>
      <select id="providerType"></select>

      <label for="search">Search Neighborhood, City, Species</label>
      <input id="search" type="search" placeholder="Ridgewood, ginkgo, pediatrics" />

      <label for="rating">Minimum Average Rating: <span id="ratingValue">1.5</span></label>
      <input id="rating" type="range" min="1.5" max="5" step="0.1" value="1.5" />

      <div class="checks">
        <label><input id="starOnly" type="checkbox" /> Groups with star doctors</label>
        <label><input id="weekendOnly" type="checkbox" /> Weekend availability</label>
      </div>

      <button id="reset">Reset Filters</button>

      <div class="legend">
        Circles are neighborhoods. Larger circles mean more matching tree providers.
      </div>
    </aside>
    <main id="map"></main>
  </div>

  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    const groups = {payload};
    const specialties = {specialties_json};
    const providerTypes = {provider_types_json};
    const specialtyColors = {{
      "Allergy and Immunology": "#d97706",
      "Cardiology": "#dc2626",
      "Dermatology": "#f97316",
      "Emergency Medicine": "#b91c1c",
      "Endocrinology": "#9333ea",
      "ENT / Otolaryngology": "#0f766e",
      "Family Medicine": "#16a34a",
      "Gastroenterology": "#a16207",
      "Geriatrics": "#64748b",
      "Hematology": "#be123c",
      "Infectious Disease": "#ca8a04",
      "Internal Medicine": "#2563eb",
      "Nephrology": "#0284c7",
      "Neurology": "#7c3aed",
      "Nutrition and Weight Management": "#84cc16",
      "Occupational Medicine": "#475569",
      "Oncology": "#6d28d9",
      "Ophthalmology": "#0891b2",
      "Orthopedics": "#92400e",
      "Pain Management": "#c2410c",
      "Pediatrics": "#db2777",
      "Preventive Medicine": "#059669",
      "Psychiatry": "#0891b2",
      "Pulmonology": "#0d9488",
      "Rheumatology": "#a855f7",
      "Sleep Medicine": "#4f46e5",
      "Sports Medicine": "#65a30d",
      "Urology": "#0369a1",
      "Vascular Medicine": "#991b1b",
      "Women's Health": "#e11d48"
    }};

    const controls = {{
      specialty: document.getElementById("specialty"),
      providerType: document.getElementById("providerType"),
      search: document.getElementById("search"),
      rating: document.getElementById("rating"),
      starOnly: document.getElementById("starOnly"),
      weekendOnly: document.getElementById("weekendOnly")
    }};

    const map = L.map("map", {{ preferCanvas: true }}).setView([40.72, -73.94], 11);
    const canvasRenderer = L.canvas({{ padding: 0.5 }});
    L.tileLayer("https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png", {{
      maxZoom: 19,
      attribution: "&copy; OpenStreetMap contributors"
    }}).addTo(map);

    const layer = L.layerGroup().addTo(map);

    function escapeHtml(value) {{
      return String(value).replace(/[&<>"']/g, character => ({{
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
      }}[character]));
    }}

    function optionList(select, values, label) {{
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

    optionList(controls.specialty, specialties, "specialties");
    optionList(controls.providerType, providerTypes, "provider types");

    function sortPairs(map) {{
      return Array.from(map.entries()).sort((a, b) => b[1] - a[1]);
    }}

    function pairSummary(pairs, limit) {{
      return pairs.slice(0, limit).map(pair => escapeHtml(pair[0]) + " (" + pair[1].toLocaleString() + ")").join(", ");
    }}

    function filteredStats(group) {{
      const specialty = controls.specialty.value;
      const type = controls.providerType.value;
      if (!specialty && !type) {{
        return {{
          count: group.count,
          rating: group.rating,
          wait: group.wait,
          access: group.access,
          stars: group.stars,
          weekends: group.weekends,
          specialties: group.specialties,
          types: group.types
        }};
      }}

      let count = 0;
      let ratingTotal = 0;
      let waitTotal = 0;
      let accessTotal = 0;
      let stars = 0;
      let weekends = 0;
      const specialtyMap = new Map();
      const typeMap = new Map();

      group.segments.forEach(segment => {{
        const segmentSpecialty = segment[0];
        const segmentType = segment[1];
        const segmentCount = segment[2];
        if (specialty && segmentSpecialty !== specialty) return;
        if (type && segmentType !== type) return;

        count += segmentCount;
        ratingTotal += segment[3] * segmentCount;
        waitTotal += segment[4] * segmentCount;
        accessTotal += segment[5] * segmentCount;
        stars += segment[6];
        weekends += segment[7];
        specialtyMap.set(segmentSpecialty, (specialtyMap.get(segmentSpecialty) || 0) + segmentCount);
        typeMap.set(segmentType, (typeMap.get(segmentType) || 0) + segmentCount);
      }});

      return {{
        count,
        rating: count ? ratingTotal / count : 0,
        wait: count ? waitTotal / count : 0,
        access: count ? accessTotal / count : 0,
        stars,
        weekends,
        specialties: sortPairs(specialtyMap),
        types: sortPairs(typeMap)
      }};
    }}

    function currentPairs() {{
      const query = controls.search.value.trim().toLowerCase();
      const minRating = Number(controls.rating.value);
      const starOnly = controls.starOnly.checked;
      const weekendOnly = controls.weekendOnly.checked;

      return groups
        .map(group => ({{ group, stats: filteredStats(group) }}))
        .filter(pair => {{
          if (!pair.stats.count) return false;
          if (pair.stats.rating < minRating) return false;
          if (starOnly && pair.stats.stars < 1) return false;
          if (weekendOnly && pair.stats.weekends < 1) return false;
          if (query && !pair.group.searchText.includes(query)) return false;
          return true;
        }});
    }}

    function radius(stats) {{
      return Math.min(32, 6 + Math.sqrt(stats.count) * 0.65);
    }}

    function popup(pair) {{
      const group = pair.group;
      const stats = pair.stats;
      const weekendShare = stats.count ? Math.round(stats.weekends / stats.count * 100) : 0;
      return '<div class="popup">' +
        '<h2>' + escapeHtml(group.neighborhood) + '</h2>' +
        '<p><strong>Trees:</strong> ' + stats.count.toLocaleString() + ' | <strong>Avg rating:</strong> ' + stats.rating.toFixed(1) + '</p>' +
        '<p><strong>Avg wait:</strong> ' + stats.wait.toFixed(1) + ' days | <strong>Avg access:</strong> ' + stats.access.toFixed(1) + '</p>' +
        '<p><strong>Star doctors:</strong> ' + stats.stars.toLocaleString() + ' | <strong>Weekend:</strong> ' + weekendShare + '%</p>' +
        '<p><strong>Top specialties:</strong> ' + pairSummary(stats.specialties, 3) + '</p>' +
        '<p><strong>Provider types:</strong> ' + pairSummary(stats.types, 3) + '</p>' +
        '<p><strong>Top species:</strong> ' + escapeHtml(group.topSpecies) + '</p>' +
      '</div>';
    }}

    function marker(pair) {{
      const dominantSpecialty = pair.stats.specialties.length ? pair.stats.specialties[0][0] : "";
      const color = controls.specialty.value
        ? (specialtyColors[controls.specialty.value] || "#2f7d4f")
        : (specialtyColors[dominantSpecialty] || "#2f7d4f");
      const marker = L.circleMarker([pair.group.lat, pair.group.lng], {{
        renderer: canvasRenderer,
        radius: radius(pair.stats),
        color: pair.stats.stars ? "#111827" : color,
        weight: pair.stats.stars ? 2.5 : 1.2,
        fillColor: color,
        fillOpacity: 0.72
      }});
      marker.bindPopup(popup(pair), {{ maxWidth: 380 }});
      return marker;
    }}

    function updateMap() {{
      layer.clearLayers();
      const visible = currentPairs();
      visible.forEach(pair => layer.addLayer(marker(pair)));

      const trees = visible.reduce((sum, pair) => sum + pair.stats.count, 0);
      const rating = trees ? visible.reduce((sum, pair) => sum + pair.stats.rating * pair.stats.count, 0) / trees : 0;
      const stars = visible.reduce((sum, pair) => sum + pair.stats.stars, 0);

      document.getElementById("treeCount").textContent = trees.toLocaleString();
      document.getElementById("groupCount").textContent = visible.length.toLocaleString();
      document.getElementById("avgRating").textContent = rating.toFixed(1);
      document.getElementById("starCount").textContent = stars.toLocaleString();
      document.getElementById("ratingValue").textContent = Number(controls.rating.value).toFixed(1);
    }}

    ["specialty", "providerType", "search", "rating", "starOnly", "weekendOnly"].forEach(id => {{
      document.getElementById(id).addEventListener("input", updateMap);
      document.getElementById(id).addEventListener("change", updateMap);
    }});

    document.getElementById("reset").addEventListener("click", () => {{
      controls.specialty.value = "";
      controls.providerType.value = "";
      controls.search.value = "";
      controls.rating.value = "1.5";
      controls.starOnly.checked = false;
      controls.weekendOnly.checked = false;
      updateMap();
      map.setView([40.72, -73.94], 11);
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

    rows = load_map_groups(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_html(rows), encoding="utf-8")
    tree_count = sum(int(row["count"]) for row in rows)
    print(f"Wrote {args.output} with {len(rows):,} neighborhood groups covering {tree_count:,} trees")
    print(f"Open directly: {args.output.resolve().as_uri()}")
    print("Or from the project root run: python3 -m http.server 8000")
    print("Then open: http://localhost:8000/docs/primary_tree_care_map.html")


if __name__ == "__main__":
    main()
