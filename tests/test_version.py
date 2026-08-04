"""Version consistency tests — keep the single source of truth honest."""

import re
import subprocess
import sys
from pathlib import Path

import booksi

SEMVER = re.compile(r"^\d+\.\d+\.\d+$")

ROOT = Path(__file__).resolve().parents[1]


def test_version_is_semver():
    assert SEMVER.match(booksi.__version__)


def test_booksi_cli_prints_version():
    out = subprocess.run(
        [sys.executable, "booksi.py", "-V"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert out.returncode == 0
    assert f"booksi {booksi.__version__}" in out.stdout


def test_pygals_cli_prints_version():
    out = subprocess.run(
        [sys.executable, "pyGals.py", "-V"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert out.returncode == 0
    assert f"pyGals {booksi.__version__}" in out.stdout


def test_rendered_html_stamps_version():
    from booksi.render import convert_dataframe_to_html

    import pandas as pd

    df = pd.DataFrame(
        {
            "Girl": ["Alice"],
            "Stadt": ["Wien"],
            "Bezirk": ["1010"],
            "Strasse": ["Street A"],
            "Fans": ["100"],
            "Score": ["9.5"],
            "Short": ["Hello"],
            "Preis": ["100€"],
            "Tel": ["+43111"],
            "Gurl": ["http://a.com"],
            "Purl": ["http://img/a.jpg"],
            "a1": ["✓"],
            "a0": ["✓"],
            "cim": [""],
            "cof": [""],
            "sid": [101],
            "gid": ["g1"],
            "t": [""],
        }
    )
    html = convert_dataframe_to_html(df)
    assert f"booksi v{booksi.__version__}" in html
