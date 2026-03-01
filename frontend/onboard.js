const API = 'http://localhost:8000';
const token = localStorage.getItem('token');
if (!token) window.location.href = '/';

const headers = { 'Authorization': `Bearer ${token}` };
let pollCollect = null;
let pollAnalysis = null;

// ============ STEP MANAGEMENT ============
// Steps are step2 (collect) and step3 (multiverse) in the DOM
function activateStep(n) {
  for (const id of ['step2', 'step3']) {
    const el = document.getElementById(id);
    const stepN = id === 'step2' ? 2 : 3;
    el.classList.remove('active', 'locked', 'done');
    if (stepN < n) el.classList.add('done');
    else if (stepN === n) el.classList.add('active');
    else el.classList.add('locked');
  }
}

async function checkConnections() {
  try {
    const res = await fetch(`${API}/api/connections`, { headers });
    if (!res.ok) return null;
    const data = await res.json();
    if (data.connections && !data.services) data.services = data.connections;
    return data;
  } catch { return null; }
}

// ============ STEP 1 (DOM: step2): Collect Your Data ============

function showServices(services) {
  const container = document.getElementById('s2-services');
  container.innerHTML = services.map(s =>
    `<span class="svc ${s.status === 'connected' ? 'connected' : ''}">${s.service}: ${s.status}</span>`
  ).join('');

  const collected = services.filter(s => s.status === 'collected');
  if (collected.length > 0) {
    document.getElementById('s2-status').textContent = 'Data already collected';
    document.getElementById('s2-status').className = 'step-status ok';
    document.getElementById('s2-btn').textContent = 'Re-scan my Google';
    document.getElementById('s2-btn').disabled = false;
    activateStep(3);
    startStep3();
  }
}

let activeSessionId = null;

async function collectGoogle() {
  const btn = document.getElementById('s2-btn');
  const status = document.getElementById('s2-status');
  btn.disabled = true;
  btn.textContent = 'Starting browser...';
  status.innerHTML = '<span class="spinner"></span>Creating cloud browser...';
  status.className = 'step-status working';

  try {
    // 1. Create a Browser Use session with a live URL
    const res = await fetch(`${API}/api/connections/session/start`, {
      method: 'POST', headers
    });
    if (!res.ok) throw new Error('Failed to create session');
    const { session_id, live_url } = await res.json();
    activeSessionId = session_id;

    // 2. Show the live browser to the user
    if (live_url) {
      document.getElementById('s2-live-iframe').src = live_url;
      document.getElementById('s2-live-container').style.display = 'block';
    }

    status.textContent = 'Log into your Google account in the browser above';
    status.className = 'step-status working';
    btn.style.display = 'none';
    document.getElementById('s2-scan-btns').style.display = 'block';
  } catch (e) {
    status.textContent = 'Failed to start browser — try again';
    status.className = 'step-status';
    btn.disabled = false;
    btn.textContent = 'Scan my Google';
  }
}

let isPolling = false;

async function startGoogleScan() {
  const btn = document.getElementById('s2-google-btn');
  btn.disabled = true;
  btn.textContent = 'Scanning...';

  try {
    await fetch(`${API}/api/connections/google/collect`, {
      method: 'POST',
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: activeSessionId })
    });
    if (!isPolling) { isPolling = true; pollCollectionStatus(); }
  } catch {
    btn.disabled = false;
    btn.textContent = 'Scan Google Data';
  }
}

async function startHistoryScan() {
  const btn = document.getElementById('s2-history-btn');
  btn.disabled = true;
  btn.textContent = 'Scanning...';

  try {
    await fetch(`${API}/api/connections/history/collect`, {
      method: 'POST',
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: activeSessionId })
    });
    if (!isPolling) { isPolling = true; pollCollectionStatus(); }
  } catch {
    btn.disabled = false;
    btn.textContent = 'Scan Browser History';
  }
}

async function pollCollectionStatus() {
  const data = await checkConnections();
  if (data && data.services) {
    const google = data.services.find(s => s.service === 'google');
    const history = data.services.find(s => s.service === 'history');

    // Check for errors on either service
    if ((google && google.status === 'error') || (history && history.status === 'error')) {
      document.getElementById('s2-status').textContent = 'Collection failed — try again';
      document.getElementById('s2-status').className = 'step-status';
      document.getElementById('s2-btn').style.display = 'inline-block';
      document.getElementById('s2-btn').disabled = false;
      document.getElementById('s2-btn').textContent = 'Scan my Google';
      document.getElementById('s2-scan-btns').style.display = 'none';
      document.getElementById('s2-live-container').style.display = 'none';
      isPolling = false;
      return;
    }

    // Both services must finish before advancing
    const googleDone = google && google.status === 'collected';
    const historyDone = history && history.status === 'collected';
    if (googleDone && historyDone) {
      document.getElementById('s2-status').textContent = 'Collection complete';
      document.getElementById('s2-status').className = 'step-status ok';
      document.getElementById('s2-btn').style.display = 'none';
      document.getElementById('s2-scan-btns').style.display = 'none';
      document.getElementById('s2-live-container').style.display = 'none';
      isPolling = false;
      showServices(data.services);
      activateStep(3);
      startStep3();
      return;
    }

    // Update status with progress
    const parts = [];
    if (googleDone) parts.push('Google data ✓');
    else parts.push('Google data...');
    if (historyDone) parts.push('Browser history ✓');
    else parts.push('Browser history...');
    document.getElementById('s2-status').innerHTML = '<span class="spinner"></span>' + parts.join(' · ');
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

  // Check if already collected — skip straight to step 3
  const data = await checkConnections();
  if (data && data.services) {
    const collected = data.services.filter(s => s.status === 'collected');
    if (collected.length > 0) {
      showServices(data.services);
      return;
    }
  }

  // Otherwise land on step 2 (collect)
  activateStep(2);
}

function logout() {
  localStorage.removeItem('token');
  window.location.href = '/';
}

init();

initParticles('bg');
