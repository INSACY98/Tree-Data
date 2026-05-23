const DATA_URL = "assets/trees_map.geojson";

const controls = {
  search: document.getElementById("search"),
  specialty: document.getElementById("specialty"),
  providerType: document.getElementById("providerType"),
  rating: document.getElementById("rating"),
  starOnly: document.getElementById("starOnly"),
  problemOnly: document.getElementById("problemOnly"),
  weekendOnly: document.getElementById("weekendOnly"),
  reset: document.getElementById("reset"),
  status: document.getElementById("status"),
};

const metrics = {
  matches: document.getElementById("metricMatches"),
  rating: document.getElementById("metricRating"),
  review: document.getElementById("metricReview"),
  stars: document.getElementById("metricStars"),
  ratingValue: document.getElementById("ratingValue"),
};

let fullData = null;
let currentData = null;
let updateTimer = null;
let hasFitToData = false;

const map = new maplibregl.Map({
  container: "map",
  center: [-73.94, 40.72],
  zoom: 10.6,
  style: {
    version: 8,
    glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
    sources: {
      osm: {
        type: "raster",
        tiles: [
          "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png",
          "https://b.tile.openstreetmap.org/{z}/{x}/{y}.png",
          "https://c.tile.openstreetmap.org/{z}/{x}/{y}.png",
        ],
        tileSize: 256,
        attribution: "&copy; OpenStreetMap contributors",
      },
    },
    layers: [
      {
        id: "osm",
        type: "raster",
        source: "osm",
      },
    ],
  },
});

map.addControl(new maplibregl.NavigationControl({ visualizePitch: false }), "top-right");

map.on("error", (event) => {
  const message = event?.error?.message || "Unknown map error";
  if (!fullData) {
    controls.status.textContent = `Map error: ${message}`;
  }
  console.error(event.error || event);
});

function emptyCollection() {
  return { type: "FeatureCollection", features: [] };
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;",
    "'": "&#39;",
  }[character]));
}

function optionList(select, values, label) {
  select.textContent = "";
  const all = document.createElement("option");
  all.value = "";
  all.textContent = `All ${label}`;
  select.appendChild(all);

  values.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    select.appendChild(option);
  });
}

function searchText(properties) {
  return [
    properties.provider_id,
    properties.species_common,
    properties.species_scientific,
    properties.medical_specialty,
    properties.provider_type,
    properties.problem_burden_level,
    properties.clinic_name,
    properties.clinic_address,
    properties.clinic_zipcode,
    properties.clinic_city,
    properties.clinic_neighborhood,
    properties.quality_bucket,
  ].join(" ").toLowerCase();
}

function matchesFeature(feature) {
  const properties = feature.properties;
  const query = controls.search.value.trim().toLowerCase();
  const minRating = Number(controls.rating.value);

  if (controls.specialty.value && properties.medical_specialty !== controls.specialty.value) return false;
  if (controls.providerType.value && properties.provider_type !== controls.providerType.value) return false;
  if (properties.care_rating < minRating) return false;
  if (controls.starOnly.checked && !properties.star_doctor) return false;
  if (controls.problemOnly.checked && properties.tree_problem_count < 1) return false;
  if (controls.weekendOnly.checked && !properties.weekend_availability) return false;
  if (query && !searchText(properties).includes(query)) return false;
  return true;
}

function summarize(features) {
  const count = features.length;
  const ratingTotal = features.reduce((sum, feature) => sum + feature.properties.care_rating, 0);
  const reviewCount = features.filter((feature) => feature.properties.quality_bucket === "Needs review").length;
  const starCount = features.filter((feature) => feature.properties.star_doctor).length;

  metrics.matches.textContent = count.toLocaleString();
  metrics.rating.textContent = count ? (ratingTotal / count).toFixed(1) : "0.0";
  metrics.review.textContent = reviewCount.toLocaleString();
  metrics.stars.textContent = starCount.toLocaleString();
  metrics.ratingValue.textContent = Number(controls.rating.value).toFixed(1);
}

function colorExpression() {
  return [
    "match",
    ["get", "quality_bucket"],
    "Needs review", "#b42318",
    "Watchlist", "#d97706",
    "Star quality", "#7c3aed",
    "Looks stable", "#2f7d4f",
    "#64748b",
  ];
}

function popupHtml(properties) {
  const rating = Number(properties.care_rating || 0);
  const reviewCount = Number(properties.review_count || 0);
  const problemCount = Number(properties.tree_problem_count || 0);
  const accessScore = Number(properties.care_accessibility_score || 0);
  const sideScore = Number(properties.shade_side_manner_score || 0);
  const rootScore = Number(properties.root_cause_analysis_score || 0);
  const waitDays = Number(properties.next_available_visit_days || 0);
  const hasWeekend = properties.weekend_availability === true || properties.weekend_availability === "true";
  const isStar = properties.star_doctor === true || properties.star_doctor === "true";
  const weekend = hasWeekend ? "Yes" : "Taking a break";
  const star = isStar ? "Star doctor" : properties.popularity_badge;

  return `
    <div class="popup">
      <h2>${escapeHtml(properties.species_common)} #${escapeHtml(properties.provider_id)}</h2>
      <p><strong>${escapeHtml(properties.medical_specialty)}</strong> | ${escapeHtml(properties.provider_type)}</p>
      <p><strong>Rating:</strong> ${rating.toFixed(1)} | <strong>Reviews:</strong> ${reviewCount.toLocaleString()} | <strong>${escapeHtml(star)}</strong></p>
      <p><strong>Problems:</strong> ${problemCount} total, ${escapeHtml(properties.problem_burden_level)} burden</p>
      <p><strong>Scores:</strong> access ${accessScore}, side manner ${sideScore.toFixed(1)}, root-cause ${rootScore.toFixed(1)}</p>
      <p><strong>Wait:</strong> ${waitDays} days | <strong>Weekend:</strong> ${weekend}</p>
      <p><strong>Clinic:</strong> ${escapeHtml(properties.clinic_name)}, ${escapeHtml(properties.clinic_neighborhood)}</p>
      <p><strong>Address:</strong> ${escapeHtml(properties.clinic_address)}, ${escapeHtml(properties.clinic_city)} ${escapeHtml(properties.clinic_zipcode)}</p>
      <p><strong>Services:</strong> ${escapeHtml(properties.primary_care_services)}</p>
      <p><strong>Prescription:</strong> ${escapeHtml(properties.signature_prescription)}</p>
      <p class="quality-note">${escapeHtml(properties.quality_notes)}</p>
    </div>
  `;
}

function updatePointColors() {
  if (!map.getLayer("tree-points")) return;
  map.setPaintProperty("tree-points", "circle-color", colorExpression());
}

function applyFilters() {
  if (!fullData) return;

  const features = fullData.features.filter(matchesFeature);
  currentData = { type: "FeatureCollection", features };
  map.getSource("trees").setData(currentData);
  summarize(features);
  updatePointColors();
  controls.status.textContent = `${features.length.toLocaleString()} of ${fullData.features.length.toLocaleString()} mapped trees shown. Click any point to inspect its record.`;
}

function scheduleFilter() {
  window.clearTimeout(updateTimer);
  updateTimer = window.setTimeout(applyFilters, 90);
}

function addMapLayers() {
  map.addSource("trees", {
    type: "geojson",
    data: emptyCollection(),
  });

  map.addLayer({
    id: "tree-points",
    type: "circle",
    source: "trees",
    paint: {
      "circle-color": colorExpression(),
      "circle-radius": [
        "interpolate",
        ["linear"],
        ["zoom"],
        9, 2.2,
        13, 4.8,
        17, 7.5,
      ],
      "circle-stroke-color": "#ffffff",
      "circle-stroke-width": [
        "case",
        ["==", ["get", "star_doctor"], true],
        2,
        1,
      ],
      "circle-opacity": 0.88,
    },
  });
}

function wireMapEvents() {
  map.on("click", "tree-points", (event) => {
    const feature = event.features[0];
    new maplibregl.Popup({ maxWidth: "380px" })
      .setLngLat(feature.geometry.coordinates)
      .setHTML(popupHtml(feature.properties))
      .addTo(map);
  });

  map.on("mouseenter", "tree-points", () => {
    map.getCanvas().style.cursor = "pointer";
  });
  map.on("mouseleave", "tree-points", () => {
    map.getCanvas().style.cursor = "";
  });
}

function wireControls() {
  ["search", "specialty", "providerType", "rating", "starOnly", "problemOnly", "weekendOnly"].forEach((id) => {
    controls[id].addEventListener("input", scheduleFilter);
    controls[id].addEventListener("change", scheduleFilter);
  });

  controls.reset.addEventListener("click", () => {
    controls.search.value = "";
    controls.specialty.value = "";
    controls.providerType.value = "";
    controls.rating.value = "1.5";
    controls.starOnly.checked = false;
    controls.problemOnly.checked = false;
    controls.weekendOnly.checked = false;
    applyFilters();
    map.easeTo({ center: [-73.94, 40.72], zoom: 10.6 });
  });
}

async function loadData() {
  const response = await fetch(DATA_URL);
  if (!response.ok) throw new Error(`Could not load ${DATA_URL}`);
  controls.status.textContent = "Loaded data file. Drawing tree points...";
  fullData = await response.json();

  optionList(controls.specialty, fullData.metadata.specialties, "specialties");
  optionList(controls.providerType, fullData.metadata.provider_types, "provider types");
  applyFilters();

  if (!hasFitToData && fullData.features.length) {
    const bounds = new maplibregl.LngLatBounds();
    fullData.features.forEach((feature) => bounds.extend(feature.geometry.coordinates));
    map.fitBounds(bounds, { padding: 36, duration: 0, maxZoom: 12 });
    hasFitToData = true;
  }
}

map.on("load", async () => {
  addMapLayers();
  wireMapEvents();
  wireControls();

  try {
    await loadData();
  } catch (error) {
    controls.status.textContent = "Map data did not load. Run python scripts/build_netlify_map_data.py and deploy the local site/ folder with assets/trees_map.geojson.";
    console.error(error);
  }
});
