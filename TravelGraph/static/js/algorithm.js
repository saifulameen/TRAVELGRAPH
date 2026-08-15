/*
  algorithm.js
  Powers the Dijkstra Visualizer on the algorithm.html page.
  Calls /api/algorithm to get the REAL step-by-step trace produced by
  the backend's Dijkstra implementation, then lets the user step
  through it (Previous / Next / Play / Pause / Reset) with a live map.
*/

let vizMap = null;
let vizCityCoords = {};
let vizSteps = [];
let vizCurrentStepIndex = 0;
let vizPlayTimer = null;
let vizPath = [];
let vizSource = null;
let vizDestination = null;
let vizNodeMarkers = {};

document.addEventListener('DOMContentLoaded', () => {
  fetch('/api/cities')
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        data.cities.forEach((c) => { vizCityCoords[c.name] = { lat: c.lat, lon: c.lon }; });
      }
    });

  document.getElementById('vizRunBtn').addEventListener('click', runVisualizer);
  document.getElementById('vizPrevBtn').addEventListener('click', () => stepTo(vizCurrentStepIndex - 1));
  document.getElementById('vizNextBtn').addEventListener('click', () => stepTo(vizCurrentStepIndex + 1));
  document.getElementById('vizPlayBtn').addEventListener('click', togglePlay);
  document.getElementById('vizResetBtn').addEventListener('click', () => { stopPlay(); stepTo(0); });
});

function showVizError(message) {
  const box = document.getElementById('vizErrorBox');
  box.textContent = message;
  box.style.display = 'block';
  document.getElementById('vizPanel').style.display = 'none';
}

function runVisualizer() {
  const source = document.getElementById('vizSource').value;
  const destination = document.getElementById('vizDest').value;

  document.getElementById('vizErrorBox').style.display = 'none';

  if (source === destination) {
    showVizError('Please choose two different cities.');
    return;
  }

  const btn = document.getElementById('vizRunBtn');
  btn.disabled = true;
  btn.textContent = 'Running...';

  fetch('/api/algorithm', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source, destination }),
  })
    .then((res) => res.json())
    .then((data) => {
      btn.disabled = false;
      btn.textContent = 'Visualize Dijkstra';

      if (!data.success) {
        showVizError(data.error || 'Unable to run the algorithm.');
        return;
      }

      vizSteps = data.algorithm_steps;
      vizPath = data.path;
      vizSource = source;
      vizDestination = destination;

      document.getElementById('vizPanel').style.display = 'grid';
      initVizMap();
      stepTo(0);
    })
    .catch(() => {
      btn.disabled = false;
      btn.textContent = 'Visualize Dijkstra';
      showVizError('Could not reach the server. Please try again.');
    });
}

function initVizMap() {
  if (vizMap) {
    vizMap.remove();
    vizMap = null;
  }
  vizMap = tgCreateBaseMap('vizMap', TG_DEFAULT_CENTER, 7);
  vizNodeMarkers = {};

  Object.entries(vizCityCoords).forEach(([name, coords]) => {
    const marker = L.circleMarker([coords.lat, coords.lon], {
      radius: 6,
      color: '#b0b6bd',
      fillColor: '#e8eaed',
      fillOpacity: 1,
      weight: 2,
    }).addTo(vizMap).bindPopup(`<strong>${name}</strong>`);
    vizNodeMarkers[name] = marker;
  });
}

function stepTo(index) {
  if (index < 0 || index >= vizSteps.length) return;
  vizCurrentStepIndex = index;
  const step = vizSteps[index];

  document.getElementById('vizStepLabel').textContent = `Step ${index + 1} / ${vizSteps.length}`;
  document.getElementById('vizCurrentNode').textContent = step.current_node;
  document.getElementById('vizCurrentDistance').textContent = `${step.current_distance} km`;

  const visitedEl = document.getElementById('vizVisited');
  visitedEl.innerHTML = '';
  step.visited_so_far.forEach((node) => {
    const tag = document.createElement('span');
    tag.className = 'tg-viz-tag';
    tag.textContent = node;
    visitedEl.appendChild(tag);
  });

  const pqEl = document.getElementById('vizPQ');
  pqEl.innerHTML = '';
  if (step.priority_queue_snapshot.length === 0) {
    pqEl.innerHTML = '<div class="tg-viz-pq-item"><span>Empty</span></div>';
  } else {
    step.priority_queue_snapshot.forEach((entry) => {
      const row = document.createElement('div');
      row.className = 'tg-viz-pq-item';
      row.innerHTML = `<span>${entry.node}</span><span>${entry.distance} km</span>`;
      pqEl.appendChild(row);
    });
  }

  updateVizMapMarkers(step);

  document.getElementById('vizPrevBtn').disabled = index === 0;
  document.getElementById('vizNextBtn').disabled = index === vizSteps.length - 1;
}

function updateVizMapMarkers(step) {
  Object.entries(vizNodeMarkers).forEach(([name, marker]) => {
    let color = '#b0b6bd';
    let fill = '#e8eaed';

    if (name === step.current_node) {
      color = '#d93025';
      fill = '#f6b3ae';
    } else if (step.visited_so_far.includes(name)) {
      color = '#1e8e3e';
      fill = '#a8dab5';
    } else if (step.priority_queue_snapshot.some((e) => e.node === name)) {
      color = '#1a73e8';
      fill = '#aecbfa';
    }

    marker.setStyle({ color, fillColor: fill });
  });
}

function togglePlay() {
  const btn = document.getElementById('vizPlayBtn');
  if (vizPlayTimer) {
    stopPlay();
  } else {
    btn.textContent = 'Pause';
    vizPlayTimer = setInterval(() => {
      if (vizCurrentStepIndex >= vizSteps.length - 1) {
        stopPlay();
        return;
      }
      stepTo(vizCurrentStepIndex + 1);
    }, 1200);
  }
}

function stopPlay() {
  if (vizPlayTimer) {
    clearInterval(vizPlayTimer);
    vizPlayTimer = null;
  }
  document.getElementById('vizPlayBtn').textContent = 'Play';
}
