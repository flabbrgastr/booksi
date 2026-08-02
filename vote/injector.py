"""Vote injector — pure function that injects vote JS/CSS into HTML."""

INJECT_HEAD = """
<style>
.vote-cell{display:inline-flex;flex-direction:column;align-items:center;gap:0;line-height:1}
.vbtn{border:none;border-radius:2px;padding:0 4px;cursor:pointer;font-size:12px;line-height:1.1;background:transparent;margin:0}
.vbtn.up{color:#4caf50}
.vbtn.up:hover,.vbtn.up.on{background:#4caf50;color:#fff}
.vbtn.down{color:#f44336}
.vbtn.down:hover,.vbtn.down.on{background:#f44336;color:#fff}
.vscore{font-weight:bold;font-size:12px;min-width:18px;text-align:center;line-height:1.1}
.vscore.pos{color:#4caf50}.vscore.neg{color:#f44336}.vscore.zero{color:#555}
.toolbar{position:sticky;top:0;z-index:100;background:#fff;padding:8px 12px;border-bottom:1px solid #ddd;display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.toolbar input[type=text]{padding:6px 10px;border:1px solid #ccc;border-radius:4px;font-size:14px;width:260px}
.toolbar select{padding:5px 8px;border:1px solid #ccc;border-radius:4px;font-size:14px}
.toolbar button{padding:5px 12px;border:1px solid #ccc;border-radius:4px;font-size:14px;cursor:pointer;background:#fff}
.toolbar button:hover{background:#f0f0f0}
.hbtn{border:none;background:transparent;cursor:pointer;font-size:16px;padding:0 2px;line-height:1;color:#ccc;transition:color .15s}
.hbtn.on{color:#e91e63}
.hbtn:hover{color:#e91e63}
.shortlist-count{font-size:12px;color:#666}
</style>
"""

INJECT_BODY = """
<script>
(async()=>{
  const toolbar = document.createElement('div');
  toolbar.className = 'toolbar';
  toolbar.innerHTML = `
    <input type="text" id="search" placeholder="Search name, location, description...">
    <select id="sl-select"></select>
    <button id="sl-new" title="New shortlist">+</button>
    <a id="sl-view" href="/shortlist/hot" style="font-size:13px">My Shortlists</a>
    <span id="sl-count" class="shortlist-count"></span>
  `;
  document.body.insertBefore(toolbar, document.body.firstChild);

  let shortlists = [];
  let activeSL = 'hot';
  let slGals = new Set();

  async function loadShortlists() {
    const r = await fetch('/api/shortlists');
    shortlists = await r.json();
    if (!shortlists.includes(activeSL)) activeSL = shortlists[0] || 'hot';
    renderSLSelect();
    await loadSLGals();
  }

  function renderSLSelect() {
    const sel = document.getElementById('sl-select');
    sel.innerHTML = shortlists.map(n => `<option value="${n}"${n===activeSL?' selected':''}>${n}</option>`).join('');
    document.getElementById('sl-view').href = '/shortlist/' + activeSL;
  }

  async function loadSLGals() {
    const r = await fetch('/api/shortlists/' + encodeURIComponent(activeSL) + '/gals');
    const items = await r.json();
    slGals = new Set(items.map(g => g.id));
    updateHeartButtons();
  }

  function updateHeartButtons() {
    document.querySelectorAll('.hbtn').forEach(btn => {
      const url = btn.dataset.url;
      btn.classList.toggle('on', slGals.has(url));
    });
    const count = document.getElementById('sl-count');
    if (count) count.textContent = slGals.size ? slGals.size + ' saved' : '';
  }

  document.getElementById('sl-select').addEventListener('change', e => {
    activeSL = e.target.value;
    document.getElementById('sl-view').href = '/shortlist/' + activeSL;
    loadSLGals();
  });

  document.getElementById('sl-new').addEventListener('click', async () => {
    const name = prompt('New shortlist name:');
    if (!name || !name.trim()) return;
    await fetch('/api/shortlists', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({name:name.trim()})});
    activeSL = name.trim();
    await loadShortlists();
  });

  window.toggleShortlist = async function(btn, url) {
    const on = slGals.has(url);
    if (on) {
      await fetch('/api/shortlists/' + encodeURIComponent(activeSL) + '/gals/' + encodeURIComponent(url), {method:'DELETE'});
      slGals.delete(url);
    } else {
      await fetch('/api/shortlists/' + encodeURIComponent(activeSL) + '/gals', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({id:url})});
      slGals.add(url);
    }
    btn.classList.toggle('on', !on);
    const count = document.getElementById('sl-count');
    if (count) count.textContent = slGals.size ? slGals.size + ' saved' : '';
  };

  await loadShortlists();

  const ths = document.querySelectorAll('thead th');
  if(ths.length>0){
    const hth = document.createElement('th');
    hth.textContent='\\u2605';
    hth.style.cssText='position:sticky;top:0;background:#f1f1f1;cursor:default;width:28px';
    if(ths[1] && ths[1].nextSibling) ths[1].parentNode.insertBefore(hth, ths[1].nextSibling);
    else if(ths[0]) ths[0].parentNode.appendChild(hth);

    const vth = document.createElement('th');
    vth.textContent='Vote';
    vth.style.cssText='position:sticky;top:0;background:#f1f1f1;cursor:default;width:36px';
    hth.parentNode.insertBefore(vth, hth.nextSibling);
  }

  const resp = await fetch('/api/votes');
  const votes = await resp.json();

  document.querySelectorAll('tbody tr').forEach(tr=>{
    const tds = tr.querySelectorAll('td');
    if(tds.length<2) return;
    const a = tds[1].querySelector('a');
    if(!a) return;
    const url = a.href;
    const v = votes[url] || {up:0, down:0};
    const net = v.up - v.down;
    const cls = net>0?'pos':net<0?'neg':'zero';

    const htd = document.createElement('td');
    htd.style.cssText='text-align:center';
    htd.innerHTML = '<button class="hbtn' + (slGals.has(url)?' on':'') + '" data-url="' + url + '" onclick="toggleShortlist(this,&#39;' + url + '&#39;)">&#9829;</button>';
    tds[1].parentNode.insertBefore(htd, tds[1].nextSibling);

    const vtd = document.createElement('td');
    vtd.innerHTML = '<span class="vote-cell">' +
      '<button class="vbtn up" onclick="doVote(this,&#39;' + url + '&#39;,&#39;up&#39;)">&#9650;</button>' +
      '<span class="vscore ' + cls + '">' + net + '</span>' +
      '<button class="vbtn down" onclick="doVote(this,&#39;' + url + '&#39;,&#39;down&#39;)">&#9660;</button>' +
      '</span>';
    htd.parentNode.insertBefore(vtd, htd.nextSibling);
    if(net<0) { tr.style.display='none'; tr.dataset.voteHidden='1'; }
  });

  document.getElementById('search').addEventListener('input', e => {
    const q = e.target.value.toLowerCase();
    document.querySelectorAll('tbody tr').forEach(tr => {
      if (tr.dataset.voteHidden) return; // skip vote-hidden rows
      const text = tr.textContent.toLowerCase();
      tr.style.display = text.includes(q) ? '' : 'none';
    });
  });
})();

async function doVote(btn, id, dir){
  const r = await fetch('/api/vote',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,vote:dir})});
  if(!r.ok) return;
  const cell = btn.closest('.vote-cell');
  const score = cell.querySelector('.vscore');
  let n = parseInt(score.textContent)||0;
  n += dir==='up'?1:-1;
  score.textContent = n;
  score.className = 'vscore '+(n>0?'pos':n<0?'neg':'zero');
  cell.querySelectorAll('.vbtn').forEach(b=>b.classList.remove('on'));
  btn.classList.add('on');
  if(n<0) btn.closest('tr').style.display='none';
}
</script>
"""


def inject_votes(html):
    """Inject vote JS/CSS into the original all.html. Pure function."""
    html = html.replace("</head>", INJECT_HEAD + "</head>", 1)
    html = html.replace("</body>", INJECT_BODY + "</body>", 1)
    return html
