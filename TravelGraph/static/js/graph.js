/*
  graph.js
  Renders the Graph Explorer page: an SVG node-link diagram of the
  weighted graph, plus the full adjacency list and graph statistics,
  fetched from /api/graph.
*/

document.addEventListener('DOMContentLoaded', () => {
  fetch('/api/graph')
    .then((res) => res.json())
    .then((data) => {
      if (!data.success) return;
      renderStats(data);
      renderAdjacencyList(data.adjacency_list);
      renderGraphSvg(data.nodes, data.edge_list);
    })
    .catch(() => {
      document.getElementById('graphStats').innerHTML =
        '<p style="color:var(--tg-text-secondary)">Unable to load graph data.</p>';
    });
});

function renderStats(data) {
  document.getElementById('statVertices').textContent = data.vertices;
  document.getElementById('statEdges').textContent = data.edges;
}

function renderAdjacencyList(adjacencyList) {
  const container = document.getElementById('adjacencyList');
  container.innerHTML = '';

  Object.keys(adjacencyList).sort().forEach((city) => {
    const neighbours = adjacencyList[city];
    const neighbourText = Object.keys(neighbours).length > 0
      ? Object.entries(neighbours).map(([n, w]) => `${n} (${w} km)`).join(', ')
      : 'No direct connections';

    const item = document.createElement('div');
    item.className = 'tg-adjacency-item';
    item.innerHTML = `
      <div class="tg-adjacency-city">${city}</div>
      <div class="tg-adjacency-neighbours">${neighbourText}</div>
    `;
    container.appendChild(item);
  });
}

function renderGraphSvg(nodes, edges) {
  const svg = document.getElementById('graphSvg');
  const width = 800;
  const height = 600;
  const cx = width / 2;
  const cy = height / 2;
  const radius = 240;

  // Layout nodes in a circle for a clean, readable diagram
  // (independent of real-world lat/lon, purely for graph clarity).
  const positions = {};
  const n = nodes.length;
  nodes.forEach((node, i) => {
    const angle = (2 * Math.PI * i) / n - Math.PI / 2;
    positions[node.id] = {
      x: cx + radius * Math.cos(angle),
      y: cy + radius * Math.sin(angle),
    };
  });

  const svgns = 'http://www.w3.org/2000/svg';
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`);

  // Draw edges first (so nodes render on top).
  edges.forEach((edge) => {
    const p1 = positions[edge.source];
    const p2 = positions[edge.target];
    if (!p1 || !p2) return;

    const line = document.createElementNS(svgns, 'line');
    line.setAttribute('x1', p1.x);
    line.setAttribute('y1', p1.y);
    line.setAttribute('x2', p2.x);
    line.setAttribute('y2', p2.y);
    line.setAttribute('stroke', '#c7cdd6');
    line.setAttribute('stroke-width', '1.5');
    svg.appendChild(line);

    const midX = (p1.x + p2.x) / 2;
    const midY = (p1.y + p2.y) / 2;
    const label = document.createElementNS(svgns, 'text');
    label.setAttribute('x', midX);
    label.setAttribute('y', midY);
    label.setAttribute('font-size', '9');
    label.setAttribute('fill', '#5f6368');
    label.setAttribute('text-anchor', 'middle');
    label.textContent = `${edge.weight}`;
    svg.appendChild(label);
  });

  // Draw nodes.
  nodes.forEach((node) => {
    const pos = positions[node.id];

    const circle = document.createElementNS(svgns, 'circle');
    circle.setAttribute('cx', pos.x);
    circle.setAttribute('cy', pos.y);
    circle.setAttribute('r', 9);
    circle.setAttribute('fill', '#1a73e8');
    circle.setAttribute('stroke', '#ffffff');
    circle.setAttribute('stroke-width', '2');
    svg.appendChild(circle);

    const text = document.createElementNS(svgns, 'text');
    const labelOffsetY = pos.y < cy ? -14 : 20;
    text.setAttribute('x', pos.x);
    text.setAttribute('y', pos.y + labelOffsetY);
    text.setAttribute('font-size', '11');
    text.setAttribute('font-weight', '600');
    text.setAttribute('fill', '#202124');
    text.setAttribute('text-anchor', 'middle');
    text.textContent = node.id;
    svg.appendChild(text);
  });
}
