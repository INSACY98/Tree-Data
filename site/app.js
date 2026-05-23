const DATA_URL = "assets/trees_map.geojson";
const QUALITY_COLORS = {
  "Needs review": "#b42318",
  Watchlist: "#d97706",
  "Star quality": "#7c3aed",
  "Looks stable": "#2f7d4f",
};

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

controls.status.textContent = "App loaded. Checking Leaflet map library...";

if (typeof L === "undefined") {
  controls.status.textContent = "Leaflet map library did not load. Check the network connection or CDN access.";
  throw new Error("Leaflet did not load.");
}

const metrics = {
  matches: document.getElementById("metricMatches"),
  rating: document.getElementById("metricRating"),
  review: document.getElementById("metricReview"),
  stars: document.getElementById("metricStars"),
  ratingValue: document.getElementById("ratingValue"),
};

let fullData = null;
let currentFeatures = [];
let updateTimer = null;
let drawFrame = null;
let hasFitToData = false;
let controlsReady = false;
let map = null;
let canvas = null;
let context = null;

try {
  map = L.map("map", {
    preferCanvas: true,
    zoomControl: true,
  }).setView([40.72, -73.94], 11);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);

  canvas = L.DomUtil.create("canvas", "tree-canvas");
  context = canvas.getContext("2d");
  canvas.style.position = "absolute";
  canvas.style.pointerEvents = "none";
  map.getPanes().overlayPane.appendChild(canvas);
} catch (error) {
  controls.status.textContent = `Leaflet map could not start: ${error.message}`;
  throw error;
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

function prepareFeature(feature) {
  feature._lng = feature.geometry.coordinates[0];
  feature._lat = feature.geometry.coordinates[1];
  feature._search = searchText(feature.properties);
  return feature;
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
  if (query && !feature._search.includes(query)) return false;
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

function pointRadius(zoom, isStar) {
  if (zoom < 12) return isStar ? 3.8 : 2.3;
  if (zoom < 15) return isStar ? 5.8 : 4.1;
  return isStar ? 8.8 : 6.2;
}

function colorFor(properties) {
  return QUALITY_COLORS[properties.quality_bucket] || "#64748b";
}

function resizeCanvas() {
  const size = map.getSize();
  const topLeft = map.containerPointToLayerPoint([0, 0]);
  const ratio = window.devicePixelRatio || 1;

  L.DomUtil.setPosition(canvas, topLeft);
  canvas.width = size.x * ratio;
  canvas.height = size.y * ratio;
  canvas.style.width = `${size.x}px`;
  canvas.style.height = `${size.y}px`;
  context.setTransform(ratio, 0, 0, ratio, 0, 0);
}

function drawTrees() {
  drawFrame = null;
  resizeCanvas();

  const size = map.getSize();
  context.clearRect(0, 0, size.x, size.y);

  const bounds = map.getBounds().pad(0.08);
  const zoom = map.getZoom();

  currentFeatures.forEach((feature) => {
    if (!bounds.contains([feature._lat, feature._lng])) return;

    const point = map.latLngToContainerPoint([feature._lat, feature._lng]);
    const radius = pointRadius(zoom, feature.properties.star_doctor);

    context.beginPath();
    context.arc(point.x, point.y, radius, 0, Math.PI * 2);
    context.fillStyle = colorFor(feature.properties);
    context.globalAlpha = 0.88;
    context.fill();

    context.globalAlpha = 1;
    context.lineWidth = feature.properties.star_doctor ? 2 : 1;
    context.strokeStyle = feature.properties.star_doctor ? "#111827" : "#ffffff";
    context.stroke();
  });
}

function scheduleDraw() {
  if (drawFrame) return;
  drawFrame = window.requestAnimationFrame(drawTrees);
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

function nearestFeature(clickPoint) {
  const bounds = map.getBounds().pad(0.08);
  const zoom = map.getZoom();
  let closest = null;
  let closestDistance = Infinity;

  currentFeatures.forEach((feature) => {
    if (!bounds.contains([feature._lat, feature._lng])) return;

    const point = map.latLngToContainerPoint([feature._lat, feature._lng]);
    const dx = point.x - clickPoint.x;
    const dy = point.y - clickPoint.y;
    const distance = Math.sqrt(dx * dx + dy * dy);
    const hitRadius = Math.max(10, pointRadius(zoom, feature.properties.star_doctor) + 4);

    if (distance <= hitRadius && distance < closestDistance) {
      closest = feature;
      closestDistance = distance;
    }
  });

  return closest;
}

function applyFilters() {
  if (!fullData) return;

  currentFeatures = fullData.features.filter(matchesFeature);
  summarize(currentFeatures);
  scheduleDraw();
  controls.status.textContent = `${currentFeatures.length.toLocaleString()} of ${fullData.features.length.toLocaleString()} mapped trees shown. Click any point to inspect its record.`;
}

function scheduleFilter() {
  window.clearTimeout(updateTimer);
  updateTimer = window.setTimeout(applyFilters, 90);
}

function wireControls() {
  if (controlsReady) return;

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
    map.setView([40.72, -73.94], 11);
  });

  controlsReady = true;
}

function fitToData() {
  if (hasFitToData || !fullData.features.length) return;

  const bounds = L.latLngBounds(fullData.features.map((feature) => [feature._lat, feature._lng]));
  map.fitBounds(bounds, { padding: [36, 36], maxZoom: 12, animate: false });
  hasFitToData = true;
}

async function loadData() {
  controls.status.textContent = "Fetching tree data...";
  const response = await fetch(DATA_URL, { cache: "no-store" });
  if (!response.ok) throw new Error(`Could not load ${DATA_URL}: HTTP ${response.status}`);

  const text = await response.text();
  controls.status.textContent = `Downloaded tree data (${(text.length / 1024 / 1024).toFixed(1)} MB). Parsing...`;
  fullData = JSON.parse(text);
  fullData.features = fullData.features.map(prepareFeature);

  optionList(controls.specialty, fullData.metadata.specialties, "specialties");
  optionList(controls.providerType, fullData.metadata.provider_types, "provider types");
  wireControls();
  applyFilters();
  fitToData();
  scheduleDraw();
}

map.on("move zoom resize", scheduleDraw);
map.on("click", (event) => {
  const feature = nearestFeature(event.containerPoint);
  if (!feature) return;

  L.popup({ maxWidth: 380 })
    .setLatLng([feature._lat, feature._lng])
    .setContent(popupHtml(feature.properties))
    .openOn(map);
});

loadData().catch((error) => {
  controls.status.textContent = `Map data did not load: ${error.message}. Confirm assets/trees_map.geojson is available.`;
  console.error(error);
});
