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


# --- Category flags (loaded from gals.conf) ---

VALID_FLAGS = {"a1", "a0", "cim", "cof"}


def load_categories(config_path="gals.conf"):
    """Parse [htmls] section from gals.conf.

    Returns list of dicts: [{"name": "analsex", "flags": {"a1": True}}, ...]
    Each line: category_name [flag ...]
    Valid flags: a1 a0 cim cof
    """
    categories = []
    in_htmls = False
    try:
        with open(config_path) as f:
            for line in f:
                line = line.strip()
                if line == "[htmls]":
                    in_htmls = True
                    continue
                if line.startswith("[") and in_htmls:
                    break
                if in_htmls and line and not line.startswith("#"):
                    parts = line.split()
                    name = parts[0]
                    flags = {f: f in parts[1:] for f in VALID_FLAGS}
                    categories.append({"name": name, "flags": flags})
    except FileNotFoundError:
        pass
    return categories


def data_gen_csv(data_dir: Path | None = None) -> Path:
    """Return path to the latest gen/all.csv inside data_dir."""
    d = data_dir or DATA_DIR
    return d / "gen" / CSV_FILENAME


def data_gen_html(data_dir: Path | None = None) -> Path:
    """Return path to the latest gen/all.html inside data_dir."""
    d = data_dir or DATA_DIR
    return d / "gen" / HTML_FILENAME
