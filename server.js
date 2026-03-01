require('dotenv').config();
const express = require('express');
const path = require('path');
const app = express();
const PORT = process.env.PORT || 3000;

const BU_BASE = 'https://api.browser-use.com/api/v3';
const BU_KEY = process.env.BROWSER_USE_API_KEY;
const ANTHROPIC_KEY = process.env.ANTHROPIC_API_KEY;

app.use(express.json());

// ── Browser Use proxy ──────────────────────────────────────────────
async function buFetch(method, path, body) {
  console.log("Running browser use proxy");

  const res = await fetch(`${BU_BASE}${path}`, {
    method,
    headers: {
      'X-Browser-Use-API-Key': BU_KEY,
      'Content-Type': 'application/json',
    },
    ...(body ? { body: JSON.stringify(body) } : {}),
  });
  const data = await res.json();
  return { status: res.status, data };
}

// Create / dispatch session
app.post('/api/bu/sessions', async (req, res) => {
  try {
    const { status, data } = await buFetch('POST', '/sessions', req.body);
    res.status(status).json(data);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Get session status / output
app.get('/api/bu/sessions/:id', async (req, res) => {
  try {
    const { status, data } = await buFetch('GET', `/sessions/${req.params.id}`);
    res.status(status).json(data);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Stop session
app.post('/api/bu/sessions/:id/stop', async (req, res) => {
  try {
    const { status, data } = await buFetch('POST', `/sessions/${req.params.id}/stop`, req.body);
    res.status(status).json(data);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// ── Anthropic proxy ────────────────────────────────────────────────
app.post('/api/anthropic/messages', async (req, res) => {
  try {
    const upstream = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'x-api-key': ANTHROPIC_KEY,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json',
      },
      body: JSON.stringify(req.body),
    });
    const data = await upstream.json();
    res.status(upstream.status).json(data);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// ── Static + SPA fallback ──────────────────────────────────────────
app.use(express.static(path.join(__dirname)));

app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Verse Walker running on port ${PORT}`);
});
