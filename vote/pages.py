"""Vote pages — server-rendered HTML pages for shortlists."""

def shortlist_page(name):
    return '''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Shortlist: ''' + name + '''</title>
<style>
body{font-family:Arial,sans-serif;margin:0;padding:0;background:#fafafa}
.toolbar{background:#fff;padding:10px 16px;border-bottom:1px solid #ddd;display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.toolbar input[type=text]{padding:6px 10px;border:1px solid #ccc;border-radius:4px;font-size:14px;width:260px}
.toolbar select{padding:5px 8px;border:1px solid #ccc;border-radius:4px;font-size:14px}
.toolbar button{padding:5px 12px;border:1px solid #ccc;border-radius:4px;font-size:14px;cursor:pointer;background:#fff}
.toolbar button:hover{background:#f0f0f0}
.toolbar a{font-size:13px}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid #eee}
th{background:#f1f1f1;position:sticky;top:0;cursor:pointer}
tr:hover{background:#e6e6ff}
img{max-width:100px;max-height:100px;border:none}
.no-underline{text-decoration:none}
.rmbtn{border:none;background:transparent;cursor:pointer;color:#f44336;font-size:12px}
.rmbtn:hover{text-decoration:underline}
.empty{text-align:center;padding:40px;color:#999;font-size:16px}
.vote-cell{display:inline-flex;flex-direction:column;align-items:center;gap:0;line-height:1}
.vbtn{border:none;border-radius:2px;padding:0 4px;cursor:pointer;font-size:12px;line-height:1.1;background:transparent;margin:0}
.vbtn.up{color:#4caf50}.vbtn.up:hover{background:#4caf50;color:#fff}
.vbtn.down{color:#f44336}.vbtn.down:hover{background:#f44336;color:#fff}
.vscore{font-weight:bold;font-size:12px;min-width:18px;text-align:center;line-height:1.1}
.vscore.pos{color:#4caf50}.vscore.neg{color:#f44336}.vscore.zero{color:#555}
</style>
</head>
<body>
<div class="toolbar">
  <a href="/">← Back to all gals</a>
  <select id="sl-select"></select>
  <button id="sl-new" title="New shortlist">+</button>
  <button id="sl-rename" title="Rename">✎</button>
  <button id="sl-delete" title="Delete list">✕</button>
  <input type="text" id="search" placeholder="Search...">
  <span id="sl-count" style="font-size:13px;color:#666"></span>
</div>
<div id="content"></div>
<script>
(async()=>{
  let shortlists = [];
  let activeSL = "''' + name + '''";
  let gals = [];

  async function loadShortlists() {
    const r = await fetch('/api/shortlists');
    shortlists = await r.json();
    if (!shortlists.includes(activeSL)) activeSL = shortlists[0] || 'hot';
    renderSelect();
    await loadGals();
  }

  function renderSelect() {
    const sel = document.getElementById('sl-select');
    sel.innerHTML = shortlists.map(n => '<option value="' + n + '"' + (n===activeSL?' selected':'') + '>' + n + '</option>').join('');
    history.replaceState(null, '', '/shortlist/' + encodeURIComponent(activeSL));
  }

  async function loadGals() {
    const r = await fetch('/api/shortlists/' + encodeURIComponent(activeSL) + '/gals');
    gals = await r.json();
    renderGals();
  }

  function renderGals() {
    const q = document.getElementById('search').value.toLowerCase();
    const filtered = gals.filter(g => !q || g.name.toLowerCase().includes(q));
    document.getElementById('sl-count').textContent = filtered.length + ' / ' + gals.length + ' gals';

    if (!filtered.length) {
      document.getElementById('content').innerHTML = '<div class="empty">' + (gals.length ? 'No matches' : 'This shortlist is empty.<br><a href="/">Go add some ♥</a>') + '</div>';
      return;
    }

    let html = '<table><thead><tr><th></th><th>Girl</th><th>Votes</th><th>Fans</th><th></th></tr></thead><tbody>';
    for (const g of filtered) {
      const v = g.votes || {up:0,down:0};
      const net = v.up - v.down;
      const cls = net>0?'pos':net<0?'neg':'zero';
      html += '<tr data-id="' + g.id + '">' +
        '<td><img src="' + (g.image_url||'') + '" loading="lazy"></td>' +
        '<td><a href="' + g.id + '" target="_blank" class="no-underline">' + (g.name||'') + '</a></td>' +
        '<td><span class="vote-cell">' +
          '<button class="vbtn up" onclick="doVote(this,\'' + g.id + '\',\'up\')">▲</button>' +
          '<span class="vscore ' + cls + '">' + net + '</span>' +
          '<button class="vbtn down" onclick="doVote(this,\'' + g.id + '\',\'down\')">▼</button>' +
        '</span></td>' +
        '<td>' + (g.fans||'') + '</td>' +
        '<td><button class="rmbtn" onclick="removeGal(\'' + g.id + '\')">remove</button></td>' +
        '</tr>';
    }
    html += '</tbody></table>';
    document.getElementById('content').innerHTML = html;
  }

  window.removeGal = async function(id) {
    await fetch('/api/shortlists/' + encodeURIComponent(activeSL) + '/gals/' + encodeURIComponent(id), {method:'DELETE'});
    gals = gals.filter(g => g.id !== id);
    renderGals();
  };

  window.doVote = async function(btn, id, dir) {
    const r = await fetch('/api/vote',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,vote:dir})});
    if(!r.ok) return;
    const cell = btn.closest('.vote-cell');
    const score = cell.querySelector('.vscore');
    let n = parseInt(score.textContent)||0;
    n += dir==='up'?1:-1;
    score.textContent = n;
    score.className = 'vscore '+(n>0?'pos':n<0?'neg':'zero');
  };

  document.getElementById('sl-select').addEventListener('change', e => {
    activeSL = e.target.value;
    renderSelect();
    loadGals();
  });

  document.getElementById('sl-new').addEventListener('click', async () => {
    const name = prompt('New shortlist name:');
    if (!name || !name.trim()) return;
    await fetch('/api/shortlists', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({name:name.trim()})});
    activeSL = name.trim();
    await loadShortlists();
  });

  document.getElementById('sl-rename').addEventListener('click', async () => {
    const name = prompt('Rename shortlist:', activeSL);
    if (!name || !name.trim() || name.trim() === activeSL) return;
    await fetch('/api/shortlists/' + encodeURIComponent(activeSL), {method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify({name:name.trim()})});
    activeSL = name.trim();
    await loadShortlists();
  });

  document.getElementById('sl-delete').addEventListener('click', async () => {
    if (!confirm('Delete shortlist "' + activeSL + '"?')) return;
    await fetch('/api/shortlists/' + encodeURIComponent(activeSL), {method:'DELETE'});
    activeSL = 'hot';
    await loadShortlists();
  });

  document.getElementById('search').addEventListener('input', () => renderGals());

  await loadShortlists();
})();
</script>
</body>
</html>'''

