#!/usr/bin/env python3
"""booksi — data processing pipeline for adult entertainment listings."""

import sys

from booksi.pipeline import run_pipeline

if "-h" in sys.argv:
    print("""
    Usage:
        python booksi.py [options]
        -h  help
        -v  verbose
        -ci csv import instead of html analysis. Faster for testing.
        -s show stats""")
    sys.exit()

verbose = "-v" in sys.argv
csv_import = "-ci" in sys.argv
show_stats = "-s" in sys.argv

run_pipeline(
    dir_path="./data",
    csv_import=csv_import,
    show_stats=show_stats,
    verbose=verbose,
)