const express = require('express');
const path = require('path');
const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.static(path.join(__dirname)));

app.get('/map', (req, res) => {
  res.sendFile(path.join(__dirname, 'map.html'));
});

app.get('/explore', (req, res) => {
  res.sendFile(path.join(__dirname, 'explore.html'));
});

app.get('/onboard', (req, res) => {
  res.sendFile(path.join(__dirname, 'onboard.html'));
});

app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Verse Walker running on port ${PORT}`);
});
