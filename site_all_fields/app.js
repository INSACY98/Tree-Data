const DATA_URL = "assets/trees_map_all_fields.json";

const controls = {
  search: document.getElementById("search"),
  specialty: document.getElementById("specialty"),
  providerType: document.getElementById("providerType"),
  city: document.getElementById("city"),
  rating: document.getElementById("rating"),
  starOnly: document.getElementById("starOnly"),
  weekendOnly: document.getElementById("weekendOnly"),
  reset: document.getElementById("reset"),
  status: document.getElementById("status"),
};

const metrics = {
  matches: document.getElementById("metricMatches"),
  rating: document.getElementById("metricRating"),
  wait: document.getElementById("metricWait"),
  stars: document.getElementById("metricStars"),
  ratingValue: document.getElementById("ratingValue"),
};

controls.status.textContent = "App loaded. Checking Leaflet map library...";

if (typeof L === "undefined") {
  controls.status.textContent = "Leaflet map library did not load. Check the network connection or CDN access.";
  throw new Error("Leaflet did not load.");
}

let payload = null;
let fieldIndex = {};
let textFields = new Set();
let booleanFields = new Set();
let rows = [];
let currentRows = [];
let searchIndex = [];
let updateTimer = null;
let drawFrame = null;
let hasFitToData = false;
let controlsReady = false;

const map = L.map("map", {
  preferCanvas: true,
  zoomControl: true,
}).setView([40.72, -73.94], 11);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

const canvas = L.DomUtil.create("canvas", "tree-canvas");
const context = canvas.getContext("2d");
canvas.style.position = "absolute";
canvas.style.pointerEvents = "none";
map.getPanes().overlayPane.appendChild(canvas);

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;",
    "'": "&#39;",
  }[character]));
}

function labelFor(field) {
  return field.replaceAll("_", " ");
}

function rawValue(row, field) {
  return row[fieldIndex[field]];
}

function valueFor(row, field) {
  const raw = rawValue(row, field);
  if (textFields.has(field)) return payload.dicts[field][raw] || "Unknown";
  if (booleanFields.has(field)) return raw === 1 ? "Yes" : "No";
  return raw ?? "";
}

function numericValue(row, field, fallback = 0) {
  const value = Number(rawValue(row, field));
  return Number.isFinite(value) ? value : fallback;
}

function optionList(select, values, label) {
  select.textContent = "";
  const all = document.createElement("option");
  all.value = "";
  all.textContent = `All ${label}`;
  select.appendChild(all);

  values.forEach((value, index) => {
    const option = document.createElement("option");
    option.value = String(index);
    option.textContent = value;
    select.appendChild(option);
  });
}

function buildSearchText(row) {
  return payload.metadata.fields.map((field) => valueFor(row, field)).join(" ").toLowerCase();
}

function matchesRow(row, index) {
  const query = controls.search.value.trim().toLowerCase();
  const minRating = Number(controls.rating.value);

  if (controls.specialty.value && rawValue(row, "medical_specialty") !== Number(controls.specialty.value)) return false;
  if (controls.providerType.value && rawValue(row, "provider_type") !== Number(controls.providerType.value)) return false;
  if (controls.city.value && rawValue(row, "clinic_city") !== Number(controls.city.value)) return false;
  if (numericValue(row, "care_rating") < minRating) return false;
  if (controls.starOnly.checked && numericValue(row, "star_doctor") !== 1) return false;
  if (controls.weekendOnly.checked && numericValue(row, "weekend_availability") !== 1) return false;
  if (query && !searchIndex[index].includes(query)) return false;
  return true;
}

function summarize(matchingRows) {
  const count = matchingRows.length;
  let ratingTotal = 0;
  let waitTotal = 0;
  let starCount = 0;

  matchingRows.forEach((row) => {
    ratingTotal += numericValue(row, "care_rating");
    waitTotal += numericValue(row, "next_available_visit_days");
    starCount += numericValue(row, "star_doctor");
  });

  metrics.matches.textContent = count.toLocaleString();
  metrics.rating.textContent = count ? (ratingTotal / count).toFixed(1) : "0.0";
  metrics.wait.textContent = count ? (waitTotal / count).toFixed(1) : "0.0";
  metrics.stars.textContent = starCount.toLocaleString();
  metrics.ratingValue.textContent = Number(controls.rating.value).toFixed(1);
}

function pointRadius(zoom, isStar) {
  if (zoom < 12) return isStar ? 3.8 : 2.3;
  if (zoom < 15) return isStar ? 5.8 : 4.0;
  return isStar ? 8.8 : 6.1;
}

function colorFor(row) {
  if (numericValue(row, "star_doctor") === 1) return "#d97706";
  if (numericValue(row, "care_rating") < 3.5) return "#b42318";
  return "#2f7d4f";
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

  currentRows.forEach((row) => {
    const lat = numericValue(row, "clinic_latitude", null);
    const lng = numericValue(row, "clinic_longitude", null);
    if (lat === null || lng === null || !bounds.contains([lat, lng])) return;

    const point = map.latLngToContainerPoint([lat, lng]);
    const isStar = numericValue(row, "star_doctor") === 1;
    const radius = pointRadius(zoom, isStar);

    context.beginPath();
    context.arc(point.x, point.y, radius, 0, Math.PI * 2);
    context.fillStyle = colorFor(row);
    context.globalAlpha = 0.86;
    context.fill();

    context.globalAlpha = 1;
    context.lineWidth = isStar ? 2 : 1;
    context.strokeStyle = isStar ? "#111827" : "#ffffff";
    context.stroke();
  });
}

function scheduleDraw() {
  if (drawFrame) return;
  drawFrame = window.requestAnimationFrame(drawTrees);
}

function allFieldsHtml(row) {
  return payload.metadata.fields.map((field) => `
    <div class="field-row">
      <div class="field-name">${escapeHtml(labelFor(field))}</div>
      <div class="field-value">${escapeHtml(valueFor(row, field))}</div>
    </div>
  `).join("");
}

function popupHtml(row) {
  const rating = numericValue(row, "care_rating");
  const reviews = numericValue(row, "review_count");
  const waitDays = numericValue(row, "next_available_visit_days");
  const weekend = valueFor(row, "weekend_availability");
  const star = numericValue(row, "star_doctor") === 1 ? "Star doctor" : valueFor(row, "popularity_badge");

  return `
    <div class="popup">
      <h2>${escapeHtml(valueFor(row, "species_common"))} #${escapeHtml(valueFor(row, "provider_id"))}</h2>
      <p><strong>${escapeHtml(valueFor(row, "medical_specialty"))}</strong> | ${escapeHtml(valueFor(row, "provider_type"))}</p>
      <p><strong>Rating:</strong> ${rating.toFixed(1)} | <strong>Reviews:</strong> ${reviews.toLocaleString()} | <strong>${escapeHtml(star)}</strong></p>
      <p><strong>Wait:</strong> ${waitDays} days | <strong>Weekend:</strong> ${escapeHtml(weekend)}</p>
      <p><strong>Clinic:</strong> ${escapeHtml(valueFor(row, "clinic_name"))}, ${escapeHtml(valueFor(row, "clinic_neighborhood"))}</p>
      <p><strong>Conditions:</strong> ${escapeHtml(valueFor(row, "searchable_conditions"))}</p>
      <div class="field-list">${allFieldsHtml(row)}</div>
    </div>
  `;
}

function nearestRow(clickPoint) {
  const bounds = map.getBounds().pad(0.08);
  const zoom = map.getZoom();
  let closest = null;
  let closestDistance = Infinity;

  currentRows.forEach((row) => {
    const lat = numericValue(row, "clinic_latitude", null);
    const lng = numericValue(row, "clinic_longitude", null);
    if (lat === null || lng === null || !bounds.contains([lat, lng])) return;

    const point = map.latLngToContainerPoint([lat, lng]);
    const dx = point.x - clickPoint.x;
    const dy = point.y - clickPoint.y;
    const distance = Math.sqrt(dx * dx + dy * dy);
    const hitRadius = Math.max(10, pointRadius(zoom, numericValue(row, "star_doctor") === 1) + 4);

    if (distance <= hitRadius && distance < closestDistance) {
      closest = row;
      closestDistance = distance;
    }
  });

  return closest;
}

function applyFilters() {
  if (!payload) return;

  const filtered = [];
  for (let index = 0; index < rows.length; index += 1) {
    if (matchesRow(rows[index], index)) filtered.push(rows[index]);
  }

  currentRows = filtered;
  summarize(currentRows);
  scheduleDraw();
  controls.status.textContent = `${currentRows.length.toLocaleString()} of ${rows.length.toLocaleString()} mapped trees shown. Click any point to inspect all fields.`;
}

function scheduleFilter() {
  window.clearTimeout(updateTimer);
  updateTimer = window.setTimeout(applyFilters, 80);
}

function wireControls() {
  if (controlsReady) return;

  ["search", "specialty", "providerType", "city", "rating", "starOnly", "weekendOnly"].forEach((id) => {
    controls[id].addEventListener("input", scheduleFilter);
    controls[id].addEventListener("change", scheduleFilter);
  });

  controls.reset.addEventListener("click", () => {
    controls.search.value = "";
    controls.specialty.value = "";
    controls.providerType.value = "";
    controls.city.value = "";
    controls.rating.value = "1.5";
    controls.starOnly.checked = false;
    controls.weekendOnly.checked = false;
    applyFilters();
    map.setView([40.72, -73.94], 11);
  });

  controlsReady = true;
}

function fitToData() {
  if (hasFitToData || !rows.length) return;

  const bounds = L.latLngBounds(rows.map((row) => [numericValue(row, "clinic_latitude"), numericValue(row, "clinic_longitude")]));
  map.fitBounds(bounds, { padding: [36, 36], maxZoom: 12, animate: false });
  hasFitToData = true;
}

function preparePayload(data) {
  payload = data;
  fieldIndex = Object.fromEntries(payload.metadata.fields.map((field, index) => [field, index]));
  textFields = new Set(payload.metadata.text_fields || []);
  booleanFields = new Set(payload.metadata.boolean_fields || []);

  rows = (payload.rows || []).filter((row) => {
    const lat = Number(row[fieldIndex.clinic_latitude]);
    const lng = Number(row[fieldIndex.clinic_longitude]);
    return Number.isFinite(lat) && Number.isFinite(lng);
  });
  searchIndex = rows.map(buildSearchText);
}

async function loadData() {
  controls.status.textContent = "Fetching all-fields data...";
  const response = await fetch(DATA_URL, { cache: "no-store" });
  if (!response.ok) throw new Error(`Could not load ${DATA_URL}: HTTP ${response.status}`);

  const dataText = await response.text();
  controls.status.textContent = `Downloaded all-fields data (${(dataText.length / 1024 / 1024).toFixed(1)} MB). Parsing...`;
  preparePayload(JSON.parse(dataText));

  optionList(controls.specialty, payload.metadata.specialties, "specialties");
  optionList(controls.providerType, payload.metadata.provider_types, "provider types");
  optionList(controls.city, payload.metadata.cities, "cities");
  wireControls();
  applyFilters();
  fitToData();
  scheduleDraw();
}

map.on("move zoom resize", scheduleDraw);
map.on("click", (event) => {
  const row = nearestRow(event.containerPoint);
  if (!row) return;

  L.popup({ maxWidth: 460 })
    .setLatLng([numericValue(row, "clinic_latitude"), numericValue(row, "clinic_longitude")])
    .setContent(popupHtml(row))
    .openOn(map);
});

loadData().catch((error) => {
  controls.status.textContent = `Map data did not load: ${error.message}. Confirm assets/trees_map_all_fields.json is available.`;
  console.error(error);
});
