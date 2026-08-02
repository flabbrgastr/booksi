"""Tests for vote.models module."""

import pytest

from vote.models import (
    add_to_shortlist,
    delete_shortlist,
    ensure_shortlist,
    get_shortlist_gals,
    get_shortlists,
    get_votes_dict,
    init_db,
    record_vote,
    remove_from_shortlist,
    rename_shortlist,
)


@pytest.fixture
def db(tmp_path):
    """Create a fresh in-memory-like DB for each test."""
    db_path = tmp_path / "test.db"
    conn = init_db(str(db_path))
    yield conn
    conn.close()


@pytest.fixture
def db_with_gals(db):
    """DB with sample gals synced."""
    db.execute(
        "INSERT INTO gals (id, name, profile_url, image_url, fans) VALUES (?, ?, ?, ?, ?)",
        ("http://a.com", "Alice", "http://a.com", "http://img/a.jpg", 100),
    )
    db.execute(
        "INSERT INTO gals (id, name, profile_url, image_url, fans) VALUES (?, ?, ?, ?, ?)",
        ("http://b.com", "Bob", "http://b.com", "http://img/b.jpg", 200),
    )
    db.commit()
    return db


class TestInitDb:
    def test_creates_tables(self, db):
        tables = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = {t[0] for t in tables}
        assert "gals" in table_names
        assert "shortlists" in table_names
        assert "shortlist_items" in table_names

    def test_creates_hot_shortlist(self, db):
        shortlists = get_shortlists(db)
        assert "hot" in shortlists


class TestRecordVote:
    def test_upvote(self, db_with_gals):
        record_vote(db_with_gals, "http://a.com", "up")
        row = db_with_gals.execute(
            "SELECT upvotes FROM gals WHERE id=?", ("http://a.com",)
        ).fetchone()
        assert row[0] == 1

    def test_downvote(self, db_with_gals):
        record_vote(db_with_gals, "http://a.com", "down")
        row = db_with_gals.execute(
            "SELECT downvotes FROM gals WHERE id=?", ("http://a.com",)
        ).fetchone()
        assert row[0] == 1

    def test_multiple_votes(self, db_with_gals):
        record_vote(db_with_gals, "http://a.com", "up")
        record_vote(db_with_gals, "http://a.com", "up")
        record_vote(db_with_gals, "http://a.com", "down")
        row = db_with_gals.execute(
            "SELECT upvotes, downvotes FROM gals WHERE id=?", ("http://a.com",)
        ).fetchone()
        assert row[0] == 2
        assert row[1] == 1


class TestGetVotesDict:
    def test_returns_only_voted(self, db_with_gals):
        record_vote(db_with_gals, "http://a.com", "up")
        votes = get_votes_dict(db_with_gals)
        assert "http://a.com" in votes
        assert "http://b.com" not in votes

    def test_vote_structure(self, db_with_gals):
        record_vote(db_with_gals, "http://a.com", "up")
        record_vote(db_with_gals, "http://a.com", "down")
        votes = get_votes_dict(db_with_gals)
        assert votes["http://a.com"] == {"up": 1, "down": 1}


class TestShortlists:
    def test_ensure_shortlist(self, db):
        ensure_shortlist(db, "favorites")
        assert "favorites" in get_shortlists(db)

    def test_ensure_idempotent(self, db):
        ensure_shortlist(db, "favorites")
        ensure_shortlist(db, "favorites")
        assert get_shortlists(db).count("favorites") == 1

    def test_add_to_shortlist(self, db_with_gals):
        add_to_shortlist(db_with_gals, "hot", "http://a.com")
        gals = get_shortlist_gals(db_with_gals, "hot")
        assert len(gals) == 1
        assert gals[0]["id"] == "http://a.com"

    def test_remove_from_shortlist(self, db_with_gals):
        add_to_shortlist(db_with_gals, "hot", "http://a.com")
        remove_from_shortlist(db_with_gals, "hot", "http://a.com")
        gals = get_shortlist_gals(db_with_gals, "hot")
        assert len(gals) == 0

    def test_delete_shortlist(self, db):
        ensure_shortlist(db, "temp")
        delete_shortlist(db, "temp")
        assert "temp" not in get_shortlists(db)

    def test_rename_shortlist(self, db):
        ensure_shortlist(db, "old_name")
        rename_shortlist(db, "old_name", "new_name")
        lists = get_shortlists(db)
        assert "new_name" in lists
        assert "old_name" not in lists
