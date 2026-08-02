"""Shared fixtures for booksi tests."""

import os
import shutil
from datetime import datetime, timedelta

import pandas as pd
import pytest


@pytest.fixture
def data_dir(tmp_path):
    """Create a temporary data directory with sample structure."""
    data = tmp_path / "data"
    data.mkdir()
    return data


@pytest.fixture
def sample_csv(tmp_path):
    """Create a sample CSV file for delta comparison tests."""
    df = pd.DataFrame({
        "Girl": ["Alice", "Bob", "Charlie"],
        "sid": [101, 102, 103],
        "Tel": ["111", "222", "333"],
        "Strasse": ["Street A", "Street B", "Street C"],
        "t": ["", "", ""],
    })
    csv_path = tmp_path / "all.csv"
    df.to_csv(csv_path, index=False)
    return csv_path


@pytest.fixture
def sample_dataframe():
    """Return a minimal DataFrame matching booksi schema."""
    return pd.DataFrame({
        "Girl": ["Alice", "Bob", "Charlie"],
        "Stadt": ["Wien", "Wien", "Wien"],
        "Bezirk": ["1010", "1020", "1030"],
        "Strasse": ["Street A", "Street B", "Street C"],
        "Fans": ["100", "200", "300"],
        "Score": ["9.5", "8.0", "10"],
        "Short": ["Hello", "Hi", "Hey"],
        "Preis": ["100€", "80€", "120€"],
        "Tel": ["+43111", "+43222", "+43333"],
        "Gurl": ["http://a.com", "http://b.com", "http://c.com"],
        "Purl": ["http://img/a.jpg", "http://img/b.jpg", "http://img/c.jpg"],
        "a1": ["✓", "", "✓"],
        "a0": ["✓", "✓", ""],
        "cim": ["", "✓", "✓"],
        "cof": ["✓", "", "✓"],
        "sid": [101, 102, 103],
        "gid": ["g1", "g2", "g3"],
        "t": ["", "", ""],
    })


@pytest.fixture
def dated_dir(data_dir):
    """Create a date-stamped directory with gen/all.csv."""
    today = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    d = data_dir / today
    d.mkdir()
    gen = d / "gen"
    gen.mkdir()
    df = pd.DataFrame({
        "Girl": ["Alice"],
        "sid": [101],
        "Tel": ["111"],
        "Strasse": ["Street A"],
        "t": [""],
    })
    df.to_csv(gen / "all.csv", index=False)
    return d


@pytest.fixture
def twoDATED_dirs(data_dir):
    """Create two date-stamped dirs for delta testing."""
    now = datetime.now()
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d_%H%M%S")
    today = now.strftime("%Y-%m-%d_%H%M%S")

    old = data_dir / yesterday
    old.mkdir()
    (old / "gen").mkdir()
    pd.DataFrame({
        "Girl": ["Alice", "Bob"],
        "sid": [101, 102],
        "Tel": ["111", "222"],
        "Strasse": ["A", "B"],
        "t": ["", ""],
    }).to_csv(old / "gen" / "all.csv", index=False)

    new = data_dir / today
    new.mkdir()
    (new / "gen").mkdir()
    pd.DataFrame({
        "Girl": ["Alice", "Bob", "Charlie"],
        "sid": [101, 102, 103],
        "Tel": ["111", "222", "333"],
        "Strasse": ["A", "B_new", "C"],
        "t": ["", "", ""],
    }).to_csv(new / "gen" / "all.csv", index=False)

    return old, new
