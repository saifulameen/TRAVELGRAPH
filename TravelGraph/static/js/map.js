/*
  map.js
  Shared Leaflet map utilities used across the homepage preview map,
  the planner's main map, and the Dijkstra visualizer map.
*/

// Approximate center of the supported city graph (South India).
const TG_DEFAULT_CENTER = [11.5, 78.2];
const TG_DEFAULT_ZOOM = 7;

function tgCreateBaseMap(elementId, center, zoom) {
  const map = L.map(elementId, {
    zoomControl: true,
    scrollWheelZoom: true,
  }).setView(center || TG_DEFAULT_CENTER, zoom || TG_DEFAULT_ZOOM);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);

  return map;
}

function tgMakeDivIcon(label, cssClass) {
  return L.divIcon({
    className: '',
    html: `<div class="tg-marker-label ${cssClass}">${label}</div>`,
    iconSize: [30, 30],
    iconAnchor: [15, 15],
  });
}

// Non-interactive preview map for the homepage.
function initPreviewMap(elementId) {
  const map = tgCreateBaseMap(elementId, TG_DEFAULT_CENTER, 6);
  map.scrollWheelZoom.disable();

  fetch('/api/cities')
    .then((res) => res.json())
    .then((data) => {
      if (!data.success) return;
      data.cities.forEach((city) => {
        L.circleMarker([city.lat, city.lon], {
          radius: 5,
          color: '#1a73e8',
          fillColor: '#1a73e8',
          fillOpacity: 0.8,
          weight: 1,
        })
          .addTo(map)
          .bindPopup(`<strong>${city.name}</strong>`);
      });
    })
    .catch(() => {
      // Preview map still shows tiles even if the city fetch fails.
    });

  return map;
}
