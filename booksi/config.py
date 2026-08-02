"""Configuration — centralised paths and settings from env vars or defaults."""

import os
from pathlib import Path

# Base directories
DATA_DIR = Path(os.environ.get("BOOKSI_DATA_DIR", "./data"))
WEB_ROOT = Path(os.environ.get("BOOKSI_WEB_ROOT", "/var/www/booksi"))
LOCAL_HTML = Path(os.environ.get("BOOKSI_LOCAL_HTML", "./all.html"))

# Output files
HTML_FILENAME = "all.html"
CSV_FILENAME = "all.csv"

# Vote server
VOTE_DB = Path(os.environ.get("BOOKSI_VOTE_DB", "./votes.db"))
HTML_SRC = WEB_ROOT / HTML_FILENAME


def data_gen_csv(data_dir: Path | None = None) -> Path:
    """Return path to the latest gen/all.csv inside data_dir."""
    d = data_dir or DATA_DIR
    return d / "gen" / CSV_FILENAME


def data_gen_html(data_dir: Path | None = None) -> Path:
    """Return path to the latest gen/all.html inside data_dir."""
    d = data_dir or DATA_DIR
    return d / "gen" / HTML_FILENAME
