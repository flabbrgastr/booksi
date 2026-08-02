"""Vote HTTP server — thin handler that delegates to models and injector."""

import json
import os
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

from booksi.config import HTML_SRC, VOTE_DB
from vote.models import (
    get_votes_dict, record_vote, sync_gals,
    ensure_shortlist, get_shortlists, get_shortlist_gals,
    add_to_shortlist, remove_from_shortlist, delete_shortlist, rename_shortlist,
)
from vote.injector import inject_votes
from vote.pages import shortlist_page

PORT = int(os.environ.get("BOOKSI_VOTE_PORT", 8008))

_html_cache = None
_html_cache_mtime = 0


def _get_html():
    """Read and cache the injected HTML, reloading when file changes."""
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


def _send_json(handler, data, status=200):
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Cache-Control", "no-cache")
    handler.end_headers()
    handler.wfile.write(json.dumps(data).encode())


def _send_html(handler, html, status=200):
    handler.send_response(status)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.end_headers()
    handler.wfile.write(html.encode())


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/api/votes":
            _send_json(self, get_votes_dict(self.server.conn))
        elif path == "/api/shortlists":
            _send_json(self, get_shortlists(self.server.conn))
        elif re.match(r"^/api/shortlists/([^/]+)/gals$", path):
            m = re.match(r"^/api/shortlists/([^/]+)/gals$", path)
            _send_json(self, get_shortlist_gals(self.server.conn, m.group(1)))
        elif path.startswith("/shortlist/"):
            name = path[len("/shortlist/"):] or "hot"
            _send_html(self, shortlist_page(name))
        elif path == "/":
            _send_html(self, _get_html())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        if path == "/api/vote":
            gal_id, direction = body.get("id"), body.get("vote")
            if gal_id and direction in ("up", "down"):
                record_vote(self.server.conn, gal_id, direction)
                _send_json(self, {"ok": True})
            else:
                self.send_response(400)
                self.end_headers()
        elif path == "/api/shortlists":
            name = body.get("name", "").strip()
            if name:
                ensure_shortlist(self.server.conn, name)
                _send_json(self, {"ok": True})
            else:
                self.send_response(400)
                self.end_headers()
        elif re.match(r"^/api/shortlists/([^/]+)/gals$", path):
            m = re.match(r"^/api/shortlists/([^/]+)/gals$", path)
            gal_id = body.get("id")
            if gal_id:
                add_to_shortlist(self.server.conn, m.group(1), gal_id)
                _send_json(self, {"ok": True})
            else:
                self.send_response(400)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        m = re.match(r"^/api/shortlists/([^/]+)$", path)
        if m:
            new_name = body.get("name", "").strip()
            if new_name:
                rename_shortlist(self.server.conn, m.group(1), new_name)
                _send_json(self, {"ok": True})
            else:
                self.send_response(400)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        m = re.match(r"^/api/shortlists/([^/]+)/gals/([^/]+)$", path)
        if m:
            remove_from_shortlist(self.server.conn, m.group(1), m.group(2))
            _send_json(self, {"ok": True})
            return
        m = re.match(r"^/api/shortlists/([^/]+)$", path)
        if m:
            delete_shortlist(self.server.conn, m.group(1))
            _send_json(self, {"ok": True})
            return
        self.send_response(404)
        self.end_headers()


def main():
    from vote.models import init_db

    conn = init_db(str(VOTE_DB))
    added = sync_gals(conn, str(HTML_SRC))
    print(f"DB: {VOTE_DB}")
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
