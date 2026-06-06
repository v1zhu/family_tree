let network = null;
let nodesDataset = null;
let edgesDataset = null;
let selectedPersonId = null;

const API_BASE = '';

async function api(method, path, body) {
  const opts = { method, headers: {} };
  if (body) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(API_BASE + path, opts);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Request failed');
  return data;
}

async function loadGraph() {
  let data;
  try {
    data = await api('GET', '/api/graph');
  } catch (e) {
    return;
  }
  if (!data.nodes || data.nodes.length === 0) {
    nodesDataset = new vis.DataSet([{ id: 0, label: 'No people yet', shape: 'box' }]);
    edgesDataset = new vis.DataSet([]);
    initNetwork();
    return;
  }

  data.nodes.forEach(n => {
    n.shape = 'circle';
    n.size = 30;
    n.font = { size: 14, color: '#2c3e50' };
    n.borderWidth = 2;
    n.color = {
      background: getGenderColor(n.gender),
      border: '#2c3e50',
      highlight: { background: '#3498db', border: '#2c3e50' },
    };
    n.title = n.label;
  });

  nodesDataset = new vis.DataSet(data.nodes);
  edgesDataset = new vis.DataSet(data.edges);
  initNetwork();
}

function getGenderColor(gender) {
  if (!gender) return '#bdc3c7';
  if (gender === 'male') return '#85c1e9';
  if (gender === 'female') return '#f1948a';
  return '#a3e4d7';
}

function initNetwork() {
  const container = document.getElementById('graphContainer');
  const options = {
    physics: {
      solver: 'forceAtlas2Based',
      forceAtlas2Based: { gravitationalConstant: -40, centralGravity: 0.005, springLength: 120, springConstant: 0.04 },
      stabilization: { iterations: 100 },
    },
    interaction: {
      hover: true,
      tooltipDelay: 200,
      zoomView: true,
      dragView: true,
    },
    edges: {
      color: { color: '#95a5a6', highlight: '#3498db' },
      font: { size: 11, color: '#666', align: 'middle' },
      smooth: { type: 'curvedCW', roundness: 0.1 },
      width: 2,
    },
    nodes: {
      borderWidth: 2,
      shadow: { enabled: true, size: 4 },
      font: { face: 'sans-serif' },
    },
  };

  network = new vis.Network(container, { nodes: nodesDataset, edges: edgesDataset }, options);

  network.on('click', function (params) {
    if (params.nodes.length > 0) {
      const nodeId = params.nodes[0];
      if (nodeId === 0) return;
      openSidebar(nodeId);
    } else {
      closeSidebar();
    }
  });

  network.on('doubleClick', function (params) {
    if (params.nodes.length > 0) {
      const nodeId = params.nodes[0];
      if (nodeId === 0) return;
      network.focus(nodeId, { scale: 1.5, animation: true });
    }
  });
}

async function openSidebar(personId) {
  selectedPersonId = personId;
  try {
    const person = await api('GET', `/api/people/${personId}`);
    document.getElementById('editId').value = person.id;
    document.getElementById('editName').value = person.name || '';
    document.getElementById('editAge').value = person.age || '';
    document.getElementById('editGender').value = person.gender || '';
    document.getElementById('editBio').value = person.bio || '';
    document.getElementById('sidebarTitle').textContent = `Edit: ${person.name || 'Unnamed #' + person.id}`;
    renderRelations(person);
    document.getElementById('sidebar').classList.remove('hidden');
  } catch (e) {
    alert('Failed to load person: ' + e.message);
  }
}

function closeSidebar() {
  document.getElementById('sidebar').classList.add('hidden');
  selectedPersonId = null;
}

function renderRelations(person) {
  const container = document.getElementById('relationsList');
  container.innerHTML = '';

  const rels = person.relationships || [];
  if (rels.length === 0) {
    container.innerHTML = '<p style="color:#999;font-size:13px">No relationships yet.</p>';
    return;
  }

  rels.forEach(rel => {
    const div = document.createElement('div');
    div.className = 'relation-item';
    div.innerHTML = `
      <div class="rel-info">
        <span class="rel-type">${rel.type}</span>
        <span class="rel-target">→ Person #${rel.target_id}</span>
      </div>
      <button class="rel-delete" data-type="${rel.type}" data-target="${rel.target_id}">&times;</button>
    `;
    div.querySelector('.rel-delete').addEventListener('click', async () => {
      try {
        await api('DELETE', '/api/relations', {
          person_id: person.id,
          target_id: rel.target_id,
          type: rel.type,
        });
        await loadGraph();
        openSidebar(person.id);
      } catch (e) {
        alert('Failed to delete: ' + e.message);
      }
    });
    container.appendChild(div);
  });
}

async function refreshGraph() {
  await loadGraph();
  if (selectedPersonId !== null) {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar.classList.contains('hidden')) {
      openSidebar(selectedPersonId);
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  loadGraph();

  document.getElementById('addPersonBtn').addEventListener('click', () => {
    document.getElementById('addPersonModal').classList.remove('hidden');
  });

  document.getElementById('confirmAddPerson').addEventListener('click', async () => {
    const name = document.getElementById('newPersonName').value;
    const age = document.getElementById('newPersonAge').value;
    const gender = document.getElementById('newPersonGender').value;
    const bio = document.getElementById('newPersonBio').value;
    try {
      await api('POST', '/api/people', {
        name, age: age ? parseInt(age) : null, gender, bio,
      });
      document.getElementById('newPersonName').value = '';
      document.getElementById('newPersonAge').value = '';
      document.getElementById('newPersonGender').value = '';
      document.getElementById('newPersonBio').value = '';
      document.getElementById('addPersonModal').classList.add('hidden');
      await refreshGraph();
    } catch (e) {
      alert('Failed to add: ' + e.message);
    }
  });

  document.getElementById('savePersonBtn').addEventListener('click', async () => {
    const id = parseInt(document.getElementById('editId').value);
    const name = document.getElementById('editName').value;
    const age = document.getElementById('editAge').value;
    const gender = document.getElementById('editGender').value;
    const bio = document.getElementById('editBio').value;
    try {
      await api('PUT', `/api/people/${id}`, {
        name, age: age ? parseInt(age) : null, gender, bio,
      });
      await refreshGraph();
    } catch (e) {
      alert('Failed to save: ' + e.message);
    }
  });

  document.getElementById('deletePersonBtn').addEventListener('click', async () => {
    const id = parseInt(document.getElementById('editId').value);
    if (!confirm(`Delete person #${id} and all their relationships?`)) return;
    try {
      await api('DELETE', `/api/people/${id}`);
      closeSidebar();
      await refreshGraph();
    } catch (e) {
      alert('Failed to delete: ' + e.message);
    }
  });

  document.getElementById('closeSidebarBtn').addEventListener('click', closeSidebar);

  document.getElementById('addRelationBtn').addEventListener('click', async () => {
    const targetId = parseInt(document.getElementById('relTargetId').value);
    const type = document.getElementById('relType').value;
    if (!targetId) return alert('Enter a target person ID');
    try {
      await api('POST', '/api/relations', {
        person_id: selectedPersonId,
        target_id: targetId,
        type: type,
      });
      document.getElementById('relTargetId').value = '';
      await refreshGraph();
    } catch (e) {
      alert('Failed to add relationship: ' + e.message);
    }
  });

  document.getElementById('findRelationBtn').addEventListener('click', () => {
    document.getElementById('findModal').classList.remove('hidden');
    document.getElementById('findResult').textContent = '';
    document.getElementById('findResult').className = '';
  });

  document.getElementById('findBtn').addEventListener('click', async () => {
    const id1 = parseInt(document.getElementById('findId1').value);
    const id2 = parseInt(document.getElementById('findId2').value);
    if (!id1 || !id2) return alert('Enter both person IDs');
    const resultDiv = document.getElementById('findResult');
    try {
      const data = await api('GET', `/api/relation/${id1}/${id2}`);
      resultDiv.textContent = data.relationship;
      resultDiv.className = '';
    } catch (e) {
      resultDiv.textContent = 'Error: ' + e.message;
      resultDiv.className = 'error';
    }
  });

  document.querySelectorAll('.modal-close').forEach(el => {
    el.addEventListener('click', () => {
      document.querySelectorAll('.modal').forEach(m => m.classList.add('hidden'));
    });
  });

  document.querySelectorAll('.modal').forEach(m => {
    m.addEventListener('click', (e) => {
      if (e.target === m) m.classList.add('hidden');
    });
  });
});
