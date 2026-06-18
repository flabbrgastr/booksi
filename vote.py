#!/usr/bin/env python3
"""Minimal voting server for booksi gals. SQLite + stdlib HTTP."""

import json
import os
import re
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "votes.db")
HTML_SRC = "/var/www/booksi/all.html"
PORT = 8008

# --- JS/CSS to inject into the original HTML ---

INJECT_HEAD = """
<style>
.vote-cell{display:flex;align-items:center;gap:4px;white-space:nowrap}
.vbtn{border:none;border-radius:3px;padding:2px 6px;cursor:pointer;font-size:15px;line-height:1;background:transparent}
.vbtn.up{color:#4caf50}
.vbtn.up:hover,.vbtn.up.on{background:#4caf50;color:#fff}
.vbtn.down{color:#f44336}
.vbtn.down:hover,.vbtn.down.on{background:#f44336;color:#fff}
.vscore{font-weight:bold;min-width:24px;text-align:center}
.vscore.pos{color:#4caf50}.vscore.neg{color:#f44336}.vscore.zero{color:#555}
</style>
"""

INJECT_BODY = """
<script>
(async()=>{
  // Add vote header
  const ths = document.querySelectorAll('thead th');
  if(ths.length>0){
    const vth = document.createElement('th');
    vth.textContent='Vote';
    vth.style.cssText='position:sticky;top:0;background:#f1f1f1;cursor:default';
    // Insert after Name column (index 1)
    if(ths[1] && ths[1].nextSibling) ths[1].parentNode.insertBefore(vth, ths[1].nextSibling);
    else if(ths[0]) ths[0].parentNode.appendChild(vth);
  }

  // Fetch current votes
  const resp = await fetch('/api/votes');
  const votes = await resp.json(); // {profile_url: {up:N, down:N}}

  // Process each row
  document.querySelectorAll('tbody tr').forEach(tr=>{
    const tds = tr.querySelectorAll('td');
    if(tds.length<2) return;
    // Find profile URL from the Girl link
    const a = tds[1].querySelector('a');
    if(!a) return;
    const url = a.href;
    const v = votes[url] || {up:0, down:0};
    const net = v.up - v.down;
    const cls = net>0?'pos':net<0?'neg':'zero';

    // Create vote cell
    const vtd = document.createElement('td');
    vtd.innerHTML = `<span class="vote-cell">
      <button class="vbtn up" onclick="doVote(this,'${url}','up')">▲</button>
      <span class="vscore ${cls}">${net}</span>
      <button class="vbtn down" onclick="doVote(this,'${url}','down')">▼</button>
    </span>`;
    // Insert after Girl column (index 1)
    tds[1].parentNode.insertBefore(vtd, tds[1].nextSibling);
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
  // Highlight active button
  cell.querySelectorAll('.vbtn').forEach(b=>b.classList.remove('on'));
  btn.classList.add('on');
}
</script>
"""

# --- DB functions ---

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS gals (
            id TEXT PRIMARY KEY,
            name TEXT,
            profile_url TEXT,
            image_url TEXT,
            fans INTEGER DEFAULT 0,
            upvotes INTEGER DEFAULT 0,
            downvotes INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    return conn

def sync_gals(conn):
    if not os.path.exists(HTML_SRC):
        return 0
    from bs4 import BeautifulSoup
    with open(HTML_SRC, "r") as f:
        soup = BeautifulSoup(f, "html.parser")
    added = 0
    for row in soup.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) < 11:
            continue
        img_tag = cols[0].find("img")
        image_url = img_tag["src"] if img_tag else ""
        a_tag = cols[1].find("a")
        name = cols[1].get_text(strip=True)
        profile_url = a_tag["href"] if a_tag else ""
        fans_text = cols[4].get_text(strip=True).replace("\xa0", "").replace(" ", "")
        try:
            fans = int(fans_text)
        except ValueError:
            fans = 0
        if not profile_url:
            continue
        cur = conn.execute("SELECT 1 FROM gals WHERE id=?", (profile_url,))
        if cur.fetchone() is None:
            conn.execute(
                "INSERT INTO gals (id, name, profile_url, image_url, fans) VALUES (?, ?, ?, ?, ?)",
                (profile_url, name, profile_url, image_url, fans),
            )
            added += 1
    conn.commit()
    return added

def get_votes_dict(conn):
    """Return {profile_url: {up: N, down: N}} for all gals with votes."""
    rows = conn.execute("SELECT id, upvotes, downvotes FROM gals WHERE upvotes>0 OR downvotes>0").fetchall()
    return {r[0]: {"up": r[1], "down": r[2]} for r in rows}

def vote(conn, gal_id, direction):
    if direction == "up":
        conn.execute("UPDATE gals SET upvotes = upvotes + 1 WHERE id=?", (gal_id,))
    elif direction == "down":
        conn.execute("UPDATE gals SET downvotes = downvotes + 1 WHERE id=?", (gal_id,))
    conn.commit()

def inject_votes(html):
    """Inject vote JS/CSS into the original all.html."""
    # Inject CSS before </head>
    html = html.replace("</head>", INJECT_HEAD + "</head>", 1)
    # Inject JS before </body>
    html = html.replace("</body>", INJECT_BODY + "</body>", 1)
    return html

# Cache the enhanced HTML
_html_cache = None
_html_cache_mtime = 0

def get_html():
    global _html_cache, _html_cache_mtime
    try:
        mtime = os.path.getmtime(HTML_SRC)
    except OSError:
        return "<html><body><h1>all.html not found</h1></body></html>"
    if _html_cache is None or mtime != _html_cache_mtime:
        with open(HTML_SRC, "r") as f:
            _html_cache = inject_votes(f.read())
        _html_cache_mtime = mtime
    return _html_cache

# --- HTTP server ---

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/votes":
            votes = get_votes_dict(self.server.conn)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(json.dumps(votes).encode())
        elif parsed.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(get_html().encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/vote":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            gal_id = body.get("id")
            direction = body.get("vote")
            if gal_id and direction in ("up", "down"):
                vote(self.server.conn, gal_id, direction)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"ok":true}')
            else:
                self.send_response(400)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()


def main():
    conn = init_db()
    added = sync_gals(conn)
    print(f"DB: {DB_PATH}")
    if added:
        print(f"Synced {added} new gals")
    total = conn.execute("SELECT COUNT(*) FROM gals").fetchone()[0]
    print(f"Total: {total} gals")
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    server.conn = conn
    print(f"Listening on http://0.0.0.0:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nBye.")
        server.server_close()

if __name__ == "__main__":
    main()
