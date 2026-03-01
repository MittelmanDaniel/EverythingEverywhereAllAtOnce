const API = 'http://localhost:8000';
const token = localStorage.getItem('token');
if (!token) window.location.href = '/';

const headers = { 'Authorization': `Bearer ${token}` };
let currentStep = 1;
let pollConn = null;
let pollCollect = null;
let pollAnalysis = null;

// ============ STEP MANAGEMENT ============
function activateStep(n) {
  currentStep = n;
  for (let i = 1; i <= 3; i++) {
    const el = document.getElementById('step' + i);
    el.classList.remove('active', 'locked', 'done');
    if (i < n) el.classList.add('done');
    else if (i === n) el.classList.add('active');
    else el.classList.add('locked');
  }
}

// ============ STEP 1: Install & Sync ============
async function checkConnections() {
  try {
    const res = await fetch(`${API}/api/connections`, { headers });
    if (!res.ok) return null;
    const data = await res.json();
    // API returns { connections: [...] }, normalize to { services: [...] }
    if (data.connections && !data.services) data.services = data.connections;
    return data;
  } catch { return null; }
}

async function pollConnections() {
  const data = await checkConnections();
  if (data && data.services) {
    const connected = data.services.filter(s => s.status === 'connected');
    if (connected.length > 0) {
      completeStep1Auto(data.services);
      return;
    }
  }
  pollConn = setTimeout(pollConnections, 3000);
}

function completeStep1Auto(services) {
  clearTimeout(pollConn);
  document.getElementById('s1-status').textContent = 'Cookies synced — services detected';
  document.getElementById('s1-status').className = 'step-status ok';
  document.getElementById('s1-btn').style.display = 'none';
  activateStep(2);
  showServices(services);
}

async function completeStep1() {
  const btn = document.getElementById('s1-btn');
  const status = document.getElementById('s1-status');
  btn.disabled = true;
  btn.textContent = 'Checking...';
  status.textContent = 'Verifying cookie sync...';
  status.className = 'step-status working';

  const data = await checkConnections();
  if (data && data.services && data.services.some(s => s.status === 'connected' || s.status === 'collected')) {
    clearTimeout(pollConn);
    status.textContent = 'Cookies synced — services detected';
    status.className = 'step-status ok';
    btn.style.display = 'none';
    activateStep(2);
    showServices(data.services);
  } else {
    status.textContent = 'No cookies found yet — sync from the extension first';
    status.className = 'step-status';
    btn.disabled = false;
    btn.textContent = "I've synced my cookies";
  }
}

// ============ STEP 2: Collect Your Data ============
async function loadStep2() {
  const data = await checkConnections();
  if (data && data.services) showServices(data.services);
}

function showServices(services) {
  const container = document.getElementById('s2-services');
  container.innerHTML = services.map(s =>
    `<span class="svc ${s.status === 'connected' ? 'connected' : ''}">${s.service}: ${s.status}</span>`
  ).join('');

  const collected = services.filter(s => s.status === 'collected');
  if (collected.length > 0) {
    document.getElementById('s2-status').textContent = 'Data already collected';
    document.getElementById('s2-status').className = 'step-status ok';
    document.getElementById('s2-btn').style.display = 'none';
    activateStep(3);
    startStep3();
  }
}

async function collectGoogle() {
  const btn = document.getElementById('s2-btn');
  const status = document.getElementById('s2-status');
  btn.disabled = true;
  btn.textContent = 'Scanning...';
  status.innerHTML = '<span class="spinner"></span>Collecting your data...';
  status.className = 'step-status working';

  try {
    await fetch(`${API}/api/connections/google/collect`, {
      method: 'POST', headers
    });
    pollCollectionStatus();
  } catch {
    status.textContent = 'Failed to start collection — try again';
    status.className = 'step-status';
    btn.disabled = false;
    btn.textContent = 'Scan my Google';
  }
}

async function pollCollectionStatus() {
  const data = await checkConnections();
  if (data && data.services) {
    const google = data.services.find(s => s.service === 'google');
    if (google && google.status === 'collected') {
      document.getElementById('s2-status').textContent = 'Collection complete';
      document.getElementById('s2-status').className = 'step-status ok';
      document.getElementById('s2-btn').style.display = 'none';
      showServices(data.services);
      activateStep(3);
      startStep3();
      return;
    }
  }
  pollCollect = setTimeout(pollCollectionStatus, 3000);
}

// ============ STEP 3: Enter Your Multiverse ============
async function startStep3() {
  document.getElementById('s3-status').innerHTML = '<span class="spinner"></span>Mapping your alternate lives...';
  document.getElementById('s3-status').className = 'step-status working';
  pollAnalysisStatus();
}

async function pollAnalysisStatus() {
  try {
    const res = await fetch(`${API}/api/analysis`, { headers });
    if (res.ok) {
      const data = await res.json();
      if (data.status === 'ready' && data.paths && data.paths.length > 0) {
        document.getElementById('s3-status').textContent = 'Your multiverse is ready';
        document.getElementById('s3-status').className = 'step-status ok';
        document.getElementById('s3-paths').textContent = data.paths.length + ' paths discovered';
        document.getElementById('s3-paths').style.display = 'block';
        document.getElementById('s3-btn').style.display = 'inline-block';
        document.getElementById('step3').classList.remove('active');
        document.getElementById('step3').classList.add('done');
        return;
      }
    }
  } catch {}
  pollAnalysis = setTimeout(pollAnalysisStatus, 3000);
}

// ============ INIT ============
async function init() {
  try {
    const res = await fetch(`${API}/api/verses`, { headers });
    if (res.ok) {
      const data = await res.json();
      if (data.verses && data.verses.length > 0) {
        window.location.href = '/map';
        return;
      }
    }
  } catch {}

  const data = await checkConnections();
  if (data && data.services) {
    const connected = data.services.filter(s => s.status === 'connected' || s.status === 'collected');
    if (connected.length > 0) {
      activateStep(2);
      showServices(data.services);
      return;
    }
  }

  pollConnections();
}

init();

initParticles('bg');
