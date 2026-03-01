const API = 'http://localhost:8000';

async function loadExplore(){
  try{
    const res = await fetch(`${API}/api/explore`);
    const data = await res.json();
    const users = data.users || [];
    const grid = document.getElementById('grid');
    const empty = document.getElementById('empty');

    if(users.length === 0){
      grid.style.display = 'none';
      empty.style.display = 'block';
      return;
    }

    grid.innerHTML = users.map(u => `
      <div class="card" onclick="location.href='/map?user=${encodeURIComponent(u.user_id)}'">
        <div class="card-name">${u.display_name}</div>
        <div class="card-count">${u.verse_count} verse${u.verse_count!==1?'s':''} discovered</div>
        <div class="card-sample">${u.sample_title}</div>
        <div class="card-arrow">→</div>
      </div>
    `).join('');
  }catch(e){
    console.error('Failed to load explore:', e);
  }
}
loadExplore();

initParticles('bg', { count: 80, speed: 0.12, maxRadius: 1.2, maxOpacity: 0.2, connectionOpacity: 0.03 });
