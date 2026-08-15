/*
  planner.js
  Powers the Directions panel + main interactive map on the planner page:
    - location search / autocomplete
    - swap source/destination
    - Get Directions -> calls /api/route -> draws route on the map
    - route info card, route details, Fit Route, My Location
*/

let tgMap = null;
let tgRouteLine = null;
let tgMarkers = [];
let tgSelectedSource = null; // { name, lat, lon }
let tgSelectedDest = null;
let tgLastRouteData = null;

document.addEventListener('DOMContentLoaded', () => {
  tgMap = tgCreateBaseMap('mainMap', TG_DEFAULT_CENTER, TG_DEFAULT_ZOOM);

  setupSearchBox('sourceInput', 'sourceSuggestions', (loc) => {
    tgSelectedSource = loc;
  });
  setupSearchBox('destInput', 'destSuggestions', (loc) => {
    tgSelectedDest = loc;
  });

  document.getElementById('swapBtn').addEventListener('click', swapLocations);
  document.getElementById('getDirectionsBtn').addEventListener('click', handleGetDirections);
  document.getElementById('fitRouteBtn').addEventListener('click', fitToRoute);
  document.getElementById('myLocationBtn').addEventListener('click', useMyLocation);
  document.getElementById('viewDetailsBtn').addEventListener('click', toggleRouteDetails);
});

function setupSearchBox(inputId, suggestionsId, onSelect) {
  const input = document.getElementById(inputId);
  const suggestionsBox = document.getElementById(suggestionsId);
  let debounceTimer = null;

  input.addEventListener('input', () => {
    const query = input.value.trim();
    clearTimeout(debounceTimer);

    if (query.length < 2) {
      suggestionsBox.classList.remove('active');
      suggestionsBox.innerHTML = '';
      return;
    }

    debounceTimer = setTimeout(() => {
      fetch(`/api/search?q=${encodeURIComponent(query)}`)
        .then((res) => res.json())
        .then((data) => {
          renderSuggestions(data.results || [], suggestionsBox, (loc) => {
            input.value = loc.name;
            suggestionsBox.classList.remove('active');
            onSelect(loc);
          });
        })
        .catch(() => {
          suggestionsBox.classList.remove('active');
        });
    }, 250);
  });

  document.addEventListener('click', (e) => {
    if (!suggestionsBox.contains(e.target) && e.target !== input) {
      suggestionsBox.classList.remove('active');
    }
  });
}

function renderSuggestions(results, box, onPick) {
  box.innerHTML = '';
  if (results.length === 0) {
    box.classList.remove('active');
    return;
  }
  results.forEach((loc) => {
    const item = document.createElement('div');
    item.className = 'tg-suggestion-item';
    item.innerHTML = `<span>${loc.name}</span>` +
      (loc.in_graph ? '<span class="tg-suggestion-tag">In graph</span>' : '<span class="tg-suggestion-tag">Search only</span>');
    item.addEventListener('click', () => onPick(loc));
    box.appendChild(item);
  });
  box.classList.add('active');
}

function swapLocations() {
  const sourceInput = document.getElementById('sourceInput');
  const destInput = document.getElementById('destInput');

  const tempVal = sourceInput.value;
  sourceInput.value = destInput.value;
  destInput.value = tempVal;

  const tempLoc = tgSelectedSource;
  tgSelectedSource = tgSelectedDest;
  tgSelectedDest = tempLoc;
}

function showError(message) {
  const box = document.getElementById('errorBox');
  box.textContent = message;
  box.style.display = 'block';
  document.getElementById('routeResult').style.display = 'none';
}

function hideError() {
  document.getElementById('errorBox').style.display = 'none';
}

function handleGetDirections() {
  hideError();

  const sourceInput = document.getElementById('sourceInput').value.trim();
  const destInput = document.getElementById('destInput').value.trim();

  const source = (tgSelectedSource && tgSelectedSource.name === sourceInput) ? tgSelectedSource.name : sourceInput;
  const destination = (tgSelectedDest && tgSelectedDest.name === destInput) ? tgSelectedDest.name : destInput;

  if (!source) { showError('Please enter a starting location.'); return; }
  if (!destination) { showError('Please enter a destination.'); return; }

  const btn = document.getElementById('getDirectionsBtn');
  btn.disabled = true;
  btn.textContent = 'Calculating...';

  fetch('/api/route', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source, destination }),
  })
    .then((res) => res.json())
    .then((data) => {
      btn.disabled = false;
      btn.textContent = 'Get Directions';

      if (!data.success) {
        showError(data.error || 'Unable to calculate a route.');
        return;
      }

      tgLastRouteData = data;
      renderRouteOnMap(data);
      renderRouteCard(data);
    })
    .catch(() => {
      btn.disabled = false;
      btn.textContent = 'Get Directions';
      showError('Could not reach the server. Please try again.');
    });
}

function renderRouteOnMap(data) {
  // Clear previous route/markers.
  if (tgRouteLine) { tgMap.removeLayer(tgRouteLine); tgRouteLine = null; }
  tgMarkers.forEach((m) => tgMap.removeLayer(m));
  tgMarkers = [];

  const geometry = data.route_geometry;

  if (geometry && geometry.length > 1) {
    tgRouteLine = L.polyline(geometry, {
      color: '#1a73e8',
      weight: 5,
      opacity: 0.85,
      lineJoin: 'round',
    }).addTo(tgMap);
  }

  const sourceCoords = data.markers.source;
  const destCoords = data.markers.destination;

  const sourceMarker = L.marker([sourceCoords.lat, sourceCoords.lon], {
    icon: tgMakeDivIcon('A', 'tg-marker-a'),
  }).addTo(tgMap).bindPopup(`<strong>${data.source}</strong><br>Start`);
  tgMarkers.push(sourceMarker);

  const destMarker = L.marker([destCoords.lat, destCoords.lon], {
    icon: tgMakeDivIcon('B', 'tg-marker-b'),
  }).addTo(tgMap).bindPopup(`<strong>${data.destination}</strong><br>Destination`);
  tgMarkers.push(destMarker);

  (data.markers.waypoints || []).forEach((wp, idx) => {
    const marker = L.marker([wp.lat, wp.lon], {
      icon: tgMakeDivIcon(idx + 1, 'tg-marker-way'),
    }).addTo(tgMap).bindPopup(`<strong>${wp.name}</strong><br>Via`);
    tgMarkers.push(marker);
  });

  fitToRoute();
}

function fitToRoute() {
  if (tgRouteLine) {
    tgMap.fitBounds(tgRouteLine.getBounds(), { padding: [40, 40] });
  } else if (tgMarkers.length > 0) {
    const group = L.featureGroup(tgMarkers);
    tgMap.fitBounds(group.getBounds(), { padding: [60, 60] });
  }
}

function useMyLocation() {
  if (!navigator.geolocation) {
    showError('Geolocation is not supported by your browser.');
    return;
  }
  navigator.geolocation.getCurrentPosition(
    (position) => {
      const { latitude, longitude } = position.coords;
      tgMap.setView([latitude, longitude], 12);
      L.circleMarker([latitude, longitude], {
        radius: 8, color: '#1a73e8', fillColor: '#1a73e8', fillOpacity: 0.6,
      }).addTo(tgMap).bindPopup('You are here').openPopup();
    },
    () => {
      showError('Location access was denied. Enable location permissions to use this feature.');
    }
  );
}

function formatDuration(minutes) {
  const hrs = Math.floor(minutes / 60);
  const mins = Math.round(minutes % 60);
  if (hrs === 0) return `${mins} min`;
  return `${hrs} hr ${mins} min`;
}

function renderRouteCard(data) {
  document.getElementById('routeResult').style.display = 'block';

  document.getElementById('routeTime').textContent = formatDuration(data.display_duration_minutes);
  document.getElementById('routeDistance').textContent = `${data.display_distance_km} km`;
  document.getElementById('routeLabel').textContent = data.duration_is_estimated
    ? 'Estimated travel time · Shortest Route (Dijkstra)'
    : 'Shortest Route (Dijkstra)';

  const viaEl = document.getElementById('routeVia');
  viaEl.textContent = data.via_cities.length > 0 ? `Via: ${data.via_cities.join(', ')}` : 'Direct route';

  const pathEl = document.getElementById('routePath');
  pathEl.innerHTML = '';
  data.path.forEach((city, idx) => {
    const item = document.createElement('div');
    item.className = 'tg-route-path-item';
    item.innerHTML = `<span class="tg-route-path-dot"></span><span>${city}</span>`;
    pathEl.appendChild(item);
    if (idx < data.path.length - 1) {
      const arrow = document.createElement('div');
      arrow.className = 'tg-route-path-arrow';
      arrow.textContent = '↓';
      pathEl.appendChild(arrow);
    }
  });

  const statsEl = document.getElementById('routeStats');
  statsEl.innerHTML = `<span>${data.city_count} cities</span><span>${data.segment_count} route segments</span>`;

  if (data.notice) {
    const notice = document.createElement('div');
    notice.style.cssText = 'margin-top:10px;font-size:12.5px;color:#8a6d00;background:#fff8e1;border:1px solid #ffe08a;border-radius:8px;padding:8px 10px;';
    notice.textContent = data.notice;
    statsEl.after(notice);
  }

  renderRouteDetails(data);
  renderAlternatives(data);

  document.getElementById('routeDetails').style.display = 'none';
  document.getElementById('viewDetailsBtn').textContent = 'View Route Details';
}

function renderRouteDetails(data) {
  const detailsEl = document.getElementById('routeDetails');
  detailsEl.innerHTML = '';

  data.path.forEach((city, idx) => {
    const isFirst = idx === 0;
    const isLast = idx === data.path.length - 1;
    const marker = isFirst ? 'A' : isLast ? 'B' : String(idx);

    const step = document.createElement('div');
    step.className = 'tg-route-detail-step';
    step.innerHTML = `<span class="tg-route-detail-marker">${marker}</span><span>${city}</span>`;
    detailsEl.appendChild(step);

    if (!isLast) {
      const segment = data.segments[idx];
      const travel = document.createElement('div');
      travel.className = 'tg-route-detail-step';
      travel.style.color = 'var(--tg-text-secondary)';
      travel.innerHTML = `<span class="tg-route-detail-marker">↓</span><span>Travel toward ${data.path[idx + 1]} (~${segment.distance_km} km)</span>`;
      detailsEl.appendChild(travel);
    }
  });
}

function toggleRouteDetails() {
  const detailsEl = document.getElementById('routeDetails');
  const btn = document.getElementById('viewDetailsBtn');
  const isHidden = detailsEl.style.display === 'none';
  detailsEl.style.display = isHidden ? 'block' : 'none';
  btn.textContent = isHidden ? 'Hide Route Details' : 'View Route Details';
}

function renderAlternatives(data) {
  const altEl = document.getElementById('altRoutes');

  if (!data.road_geometry_fully_available) {
    altEl.style.display = 'none';
    return;
  }

  // We only ever have the single Dijkstra-determined shortest route from
  // the backend. We clearly present it as the recommended (and only
  // computed) route rather than fabricating alternatives.
  altEl.innerHTML = `
    <div class="tg-route-path-title">Routes</div>
    <div class="tg-alt-route-item">
      <span><span class="tg-alt-dot recommended"></span>Recommended (Dijkstra shortest path)</span>
      <span>${data.display_distance_km} km</span>
    </div>
  `;
  altEl.style.display = 'block';
}
