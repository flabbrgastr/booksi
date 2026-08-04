#!/usr/bin/env python3
"""booksi — data processing pipeline for adult entertainment listings."""

import sys

from booksi import __version__
from booksi.pipeline import run_pipeline

if "-h" in sys.argv:
    print("""
    Usage:
        python booksi.py [options]
        -h  help
        -V  print version and exit
        -v  verbose
        -ci csv import instead of html analysis. Faster for testing.
        -s show stats

    Environment variables:
        BOOKSI_DATA_DIR   Data directory (default: ./data)
        BOOKSI_WEB_ROOT   Web root for all.html (default: /var/www/booksi)
        BOOKSI_LOCAL_HTML Local copy of all.html (default: ./all.html)""")
    sys.exit()

if "-V" in sys.argv or "--version" in sys.argv:
    print(f"booksi {__version__}")
    sys.exit()

verbose = "-v" in sys.argv
csv_import = "-ci" in sys.argv
show_stats = "-s" in sys.argv

run_pipeline(
    csv_import=csv_import,
    show_stats=show_stats,
    verbose=verbose,
)