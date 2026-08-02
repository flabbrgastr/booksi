"""Vote models — DB schema, sync, and vote recording."""

import os
import sqlite3

from bs4 import BeautifulSoup


def init_db(db_path):
    """Create all tables and return a connection."""
    conn = sqlite3.connect(db_path)
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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS shortlists (
            name TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS shortlist_items (
            shortlist_name TEXT REFERENCES shortlists(name) ON DELETE CASCADE,
            gal_id TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (shortlist_name, gal_id)
        )
    """)
    conn.execute("INSERT OR IGNORE INTO shortlists (name) VALUES ('hot')")
    conn.commit()
    return conn


def sync_gals(conn, html_path):
    """Sync gals from the all.html file into the DB. Returns count of added gals."""
    if not os.path.exists(html_path):
        return 0

    added = 0
    with open(html_path, "r") as f:
        soup = BeautifulSoup(f, "html.parser")

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
    rows = conn.execute(
        "SELECT id, upvotes, downvotes FROM gals WHERE upvotes>0 OR downvotes>0"
    ).fetchall()
    return {r[0]: {"up": r[1], "down": r[2]} for r in rows}


def record_vote(conn, gal_id, direction):
    """Record a vote (up or down) for a gal."""
    if direction == "up":
        conn.execute("UPDATE gals SET upvotes = upvotes + 1 WHERE id=?", (gal_id,))
    elif direction == "down":
        conn.execute("UPDATE gals SET downvotes = downvotes + 1 WHERE id=?", (gal_id,))
    conn.commit()


# --- Shortlist functions ---

def ensure_shortlist(conn, name):
    """Create a shortlist if it doesn't exist."""
    conn.execute("INSERT OR IGNORE INTO shortlists (name) VALUES (?)", (name,))
    conn.commit()


def get_shortlists(conn):
    """Return list of shortlist names."""
    rows = conn.execute("SELECT name FROM shortlists ORDER BY name").fetchall()
    return [r[0] for r in rows]


def get_shortlist_gals(conn, name):
    """Return list of gals in a shortlist."""
    rows = conn.execute("""
        SELECT g.id, g.name, g.image_url, g.fans, g.upvotes, g.downvotes
        FROM shortlist_items si
        JOIN gals g ON g.id = si.gal_id
        WHERE si.shortlist_name = ?
        ORDER BY si.added_at
    """, (name,)).fetchall()
    return [{"id": r[0], "name": r[1], "image_url": r[2], "fans": r[3],
             "votes": {"up": r[4], "down": r[5]}} for r in rows]


def add_to_shortlist(conn, name, gal_id):
    """Add a gal to a shortlist."""
    ensure_shortlist(conn, name)
    conn.execute("INSERT OR IGNORE INTO shortlist_items (shortlist_name, gal_id) VALUES (?, ?)", (name, gal_id))
    conn.commit()


def remove_from_shortlist(conn, name, gal_id):
    """Remove a gal from a shortlist."""
    conn.execute("DELETE FROM shortlist_items WHERE shortlist_name=? AND gal_id=?", (name, gal_id))
    conn.commit()


def delete_shortlist(conn, name):
    """Delete a shortlist and all its items."""
    conn.execute("DELETE FROM shortlist_items WHERE shortlist_name=?", (name,))
    conn.execute("DELETE FROM shortlists WHERE name=?", (name,))
    conn.commit()


def rename_shortlist(conn, old_name, new_name):
    """Rename a shortlist."""
    conn.execute("UPDATE shortlists SET name=? WHERE name=?", (new_name, old_name))
    conn.execute("UPDATE shortlist_items SET shortlist_name=? WHERE shortlist_name=?", (new_name, old_name))
    conn.commit()
