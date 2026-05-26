const DATA_URL = "assets/trees_map.json";

const IDX = {
  lng: 0,
  lat: 1,
  providerId: 2,
  speciesCommon: 3,
  speciesScientific: 4,
  specialty: 5,
  providerType: 6,
  years: 7,
  rating: 8,
  reviews: 9,
  star: 10,
  badge: 11,
  wait: 12,
  weekend: 13,
  access: 14,
  sideManner: 15,
  conditions: 16,
  philosophy: 17,
  reviewSummary: 18,
  services: 19,
  prescription: 20,
  waitingFeature: 21,
  leafPaperwork: 22,
  branchStatus: 23,
  clinicName: 24,
  address: 25,
  zipcode: 26,
  city: 27,
  neighborhood: 28,
};

const controls = {
  search: document.getElementById("search"),
  specialty: document.getElementById("specialty"),
  providerType: document.getElementById("providerType"),
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

function text(column, index) {
  return payload.dicts[column][index] || "Unknown";
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

  values.forEach((value, index) => {
    const option = document.createElement("option");
    option.value = String(index);
    option.textContent = value;
    select.appendChild(option);
  });
}

function buildSearchText(row) {
  return [
    row[IDX.providerId],
    text("species_common", row[IDX.speciesCommon]),
    text("species_scientific", row[IDX.speciesScientific]),
    text("medical_specialty", row[IDX.specialty]),
    text("provider_type", row[IDX.providerType]),
    text("searchable_conditions", row[IDX.conditions]),
    text("clinic_name", row[IDX.clinicName]),
    text("clinic_address", row[IDX.address]),
    text("clinic_zipcode", row[IDX.zipcode]),
    text("clinic_city", row[IDX.city]),
    text("clinic_neighborhood", row[IDX.neighborhood]),
  ].join(" ").toLowerCase();
}

function matchesRow(row, index) {
  const query = controls.search.value.trim().toLowerCase();
  const minRating = Number(controls.rating.value);

  if (controls.specialty.value && row[IDX.specialty] !== Number(controls.specialty.value)) return false;
  if (controls.providerType.value && row[IDX.providerType] !== Number(controls.providerType.value)) return false;
  if (row[IDX.rating] < minRating) return false;
  if (controls.starOnly.checked && row[IDX.star] !== 1) return false;
  if (controls.weekendOnly.checked && row[IDX.weekend] !== 1) return false;
  if (query && !searchIndex[index].includes(query)) return false;
  return true;
}

function summarize(matchingRows) {
  const count = matchingRows.length;
  let ratingTotal = 0;
  let waitTotal = 0;
  let starCount = 0;

  matchingRows.forEach((row) => {
    ratingTotal += Number(row[IDX.rating]);
    waitTotal += Number(row[IDX.wait]);
    starCount += Number(row[IDX.star]);
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
  if (row[IDX.star] === 1) return "#d97706";
  if (row[IDX.rating] < 3.5) return "#b42318";
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
    const lat = row[IDX.lat];
    const lng = row[IDX.lng];
    if (!bounds.contains([lat, lng])) return;

    const point = map.latLngToContainerPoint([lat, lng]);
    const isStar = row[IDX.star] === 1;
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

function popupHtml(row) {
  const rating = Number(row[IDX.rating] || 0);
  const reviews = Number(row[IDX.reviews] || 0);
  const waitDays = Number(row[IDX.wait] || 0);
  const weekend = row[IDX.weekend] === 1 ? "Yes" : "Taking a break";
  const star = row[IDX.star] === 1 ? "Star doctor" : text("popularity_badge", row[IDX.badge]);

  return `
    <div class="popup">
      <h2>${escapeHtml(text("species_common", row[IDX.speciesCommon]))} #${escapeHtml(row[IDX.providerId])}</h2>
      <p><strong>${escapeHtml(text("medical_specialty", row[IDX.specialty]))}</strong> | ${escapeHtml(text("provider_type", row[IDX.providerType]))}</p>
      <p><strong>Rating:</strong> ${rating.toFixed(1)} | <strong>Reviews:</strong> ${reviews.toLocaleString()} | <strong>${escapeHtml(star)}</strong></p>
      <p><strong>Wait:</strong> ${waitDays} days | <strong>Weekend:</strong> ${weekend}</p>
      <p><strong>Scores:</strong> access ${row[IDX.access]}, shade-side manner ${Number(row[IDX.sideManner]).toFixed(1)}</p>
      <p><strong>Conditions:</strong> ${escapeHtml(text("searchable_conditions", row[IDX.conditions]))}</p>
      <p><strong>Clinic:</strong> ${escapeHtml(text("clinic_name", row[IDX.clinicName]))}, ${escapeHtml(text("clinic_neighborhood", row[IDX.neighborhood]))}</p>
      <p><strong>Address:</strong> ${escapeHtml(text("clinic_address", row[IDX.address]))}, ${escapeHtml(text("clinic_city", row[IDX.city]))} ${escapeHtml(text("clinic_zipcode", row[IDX.zipcode]))}</p>
      <p><strong>Services:</strong> ${escapeHtml(text("primary_care_services", row[IDX.services]))}</p>
      <p><strong>Prescription:</strong> ${escapeHtml(text("signature_prescription", row[IDX.prescription]))}</p>
      <p class="review">${escapeHtml(text("patient_review_summary", row[IDX.reviewSummary]))}</p>
    </div>
  `;
}

function nearestRow(clickPoint) {
  const bounds = map.getBounds().pad(0.08);
  const zoom = map.getZoom();
  let closest = null;
  let closestDistance = Infinity;

  currentRows.forEach((row) => {
    const lat = row[IDX.lat];
    const lng = row[IDX.lng];
    if (!bounds.contains([lat, lng])) return;

    const point = map.latLngToContainerPoint([lat, lng]);
    const dx = point.x - clickPoint.x;
    const dy = point.y - clickPoint.y;
    const distance = Math.sqrt(dx * dx + dy * dy);
    const hitRadius = Math.max(10, pointRadius(zoom, row[IDX.star] === 1) + 4);

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
  controls.status.textContent = `${currentRows.length.toLocaleString()} of ${rows.length.toLocaleString()} mapped trees shown. Click any point to inspect its record.`;
}

function scheduleFilter() {
  window.clearTimeout(updateTimer);
  updateTimer = window.setTimeout(applyFilters, 80);
}

function wireControls() {
  if (controlsReady) return;

  ["search", "specialty", "providerType", "rating", "starOnly", "weekendOnly"].forEach((id) => {
    controls[id].addEventListener("input", scheduleFilter);
    controls[id].addEventListener("change", scheduleFilter);
  });

  controls.reset.addEventListener("click", () => {
    controls.search.value = "";
    controls.specialty.value = "";
    controls.providerType.value = "";
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

  const bounds = L.latLngBounds(rows.map((row) => [row[IDX.lat], row[IDX.lng]]));
  map.fitBounds(bounds, { padding: [36, 36], maxZoom: 12, animate: false });
  hasFitToData = true;
}

async function loadData() {
  controls.status.textContent = "Fetching tree data...";
  const response = await fetch(DATA_URL, { cache: "no-store" });
  if (!response.ok) throw new Error(`Could not load ${DATA_URL}: HTTP ${response.status}`);

  const dataText = await response.text();
  controls.status.textContent = `Downloaded tree data (${(dataText.length / 1024 / 1024).toFixed(1)} MB). Parsing...`;
  payload = JSON.parse(dataText);
  rows = payload.rows || [];
  searchIndex = rows.map(buildSearchText);

  optionList(controls.specialty, payload.metadata.specialties, "specialties");
  optionList(controls.providerType, payload.metadata.provider_types, "provider types");
  wireControls();
  applyFilters();
  fitToData();
  scheduleDraw();
}

map.on("move zoom resize", scheduleDraw);
map.on("click", (event) => {
  const row = nearestRow(event.containerPoint);
  if (!row) return;

  L.popup({ maxWidth: 390 })
    .setLatLng([row[IDX.lat], row[IDX.lng]])
    .setContent(popupHtml(row))
    .openOn(map);
});

loadData().catch((error) => {
  controls.status.textContent = `Map data did not load: ${error.message}. Confirm assets/trees_map.json is available.`;
  console.error(error);
});
