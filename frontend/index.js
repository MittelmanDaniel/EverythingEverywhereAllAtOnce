const API = 'http://localhost:8000';
let mode = 'login';

const token = localStorage.getItem('token');
if (token) {
  fetch(`${API}/api/auth/me`, { headers: { 'Authorization': `Bearer ${token}` } })
    .then(r => { if (r.ok) window.location.href = '/onboard'; })
    .catch(() => {});
}

function toggleMode() {
  mode = mode === 'login' ? 'signup' : 'login';
  document.getElementById('submit').textContent = mode === 'login' ? 'Enter the multiverse' : 'Begin your journey';
  document.getElementById('alt').textContent = mode === 'login' ? 'Create account' : 'Back to login';
  document.getElementById('toggle-text').innerHTML = mode === 'login'
    ? 'No account? <a onclick="toggleMode()">Sign up</a>'
    : 'Already exploring? <a onclick="toggleMode()">Log in</a>';
  document.getElementById('err').textContent = '';
}

async function handleSubmit() {
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  const err = document.getElementById('err');
  err.textContent = '';

  if (!email || !password) { err.textContent = 'Fill in both fields'; return; }

  const btn = document.getElementById('submit');
  btn.textContent = mode === 'login' ? 'Entering...' : 'Creating...';
  btn.style.pointerEvents = 'none';

  try {
    const endpoint = mode === 'login' ? '/api/auth/login' : '/api/auth/signup';
    const res = await fetch(`${API}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Something went wrong');

    localStorage.setItem('token', data.access_token);
    window.location.href = '/onboard';
  } catch (e) {
    err.textContent = e.message;
    btn.textContent = mode === 'login' ? 'Enter the multiverse' : 'Begin your journey';
    btn.style.pointerEvents = 'auto';
  }
}

document.getElementById('password').addEventListener('keydown', e => { if (e.key === 'Enter') handleSubmit() });

initParticles('bg');
