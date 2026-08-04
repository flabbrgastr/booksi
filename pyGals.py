#!/usr/bin/env python3
"""pyGals — scrape listing pages from booksusi.com using wget."""

import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from booksi import __version__
from booksi.config import DATA_DIR, load_categories
from rename import rename_jpgs


def load_config(config_path="gals.conf"):
    """Parse gals.conf into categories list and variables dict.

    [htmls] lines are bare category names with flags (no '=' sign), so
    configparser cannot parse the file as INI. Parse the raw file manually:
    category names come from load_categories(), variables from the
    [variables] section (key=value).
    """
    categories = [c["name"] for c in load_categories(config_path)]

    variables = {}
    section = None
    with open(config_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                section = line[1:-1]
                continue
            if section == "variables" and "=" in line:
                key, value = map(str.strip, line.split("=", 1))
                variables[key] = value

    return categories, variables


def build_wget_args(variables, include_images=False):
    """Build wget argument list from config."""
    args = [
        "-e", "robots=off",
        "-q", "-k", "-K", "--adjust-extension",
        "-U", "mozilla",
        "-nH", "-nd",
    ]
    if include_images:
        domain = variables.get("arg4i", "")
        args += ["-p", "-H", domain]
    args += ["--convert-links", "--random-wait"]
    return args


def strip_to_body(filepath):
    """Rewrite HTML file keeping only content between <body> and </body>."""
    with open(filepath, "r") as f:
        content = f.read()
    match = re.search(r"(<body>.*?</body>)", content, re.DOTALL)
    if match:
        with open(filepath, "w") as f:
            f.write(match.group(1))


def count_listings(filepath):
    """Count 'listing' occurrences in an HTML file."""
    try:
        with open(filepath, "r") as f:
            return f.read().count("listing")
    except (OSError, UnicodeDecodeError):
        return 0


def fetch_category(category, out_dir, wget_args, gals_per_page, test_limit=0):
    """Fetch all pages for one category. Returns total listings found."""
    base_url = variables["html0"]
    page_url = variables["html2"]
    page = 1
    total = 0
    listings = gals_per_page  # start loop

    while listings >= gals_per_page:
        url = f"{base_url}{category}{page_url}{page}"
        subprocess.run(["wget"] + wget_args + [f"-P{out_dir}", url])

        # wget saves as indexN.html — rename to categoryN.html
        src = out_dir / f"index{page}.html"
        dst = out_dir / f"{category}{page}.html"
        if src.exists():
            src.rename(dst)
        else:
            # wget may have saved with query string — find it
            for f in out_dir.glob(f"index*{page}.html*"):
                f.rename(dst)
                break

        strip_to_body(dst)
        listings = count_listings(dst) - test_limit
        total += max(listings, 0)
        print(".", end="", flush=True)
        page += 1

    return total


def cleanup_downloads(out_dir):
    """Remove non-HTML files from download directory."""
    extensions = [
        "*.orig", "*.svg", "*.css", "*.css?*", "*.js?*",
        "*.jpg", "*.jpg?", "*.png", "*.[0-9]", "*.[0-9][0-9]",
    ]
    for pattern in extensions:
        for f in out_dir.glob(pattern):
            f.unlink(missing_ok=True)


def prune_old_data(data_dir, max_age_days):
    """Delete data dirs/tars older than max_age_days.

    Age is taken from the YYYY-MM-DD prefix in the entry name, not the
    filesystem ctime — dirs re-created by the tar-extraction fallback would
    otherwise get fresh ctimes and never be pruned. Old .tar.gz backups are
    pruned too, so the data dir cannot grow unbounded.
    """
    if max_age_days <= 0:
        return
    now = datetime.now()
    cutoff = now - timedelta(days=max_age_days)
    for entry in data_dir.iterdir():
        try:
            entry_date = datetime.strptime(entry.name[:10], "%Y-%m-%d")
        except ValueError:
            continue
        if entry_date >= cutoff:
            continue
        if entry.is_dir():
            shutil.rmtree(entry)
            print(f"  pruned {entry.name}/")
        elif entry.name.endswith(".tar.gz"):
            entry.unlink(missing_ok=True)
            print(f"  pruned {entry.name}")


def main():
    parser = argparse.ArgumentParser(description="Scrape listing pages from booksusi.com")
    parser.add_argument("-i", action="store_true", help="Include images")
    parser.add_argument("-a", action="store_true", help="Anal categories only")
    parser.add_argument("-f", action="store_true", help="Keep local folder storage")
    parser.add_argument("-t", action="store_true", help="Test mode (skip 10 listings per page)")
    parser.add_argument("-V", "--version", action="version", version=f"pyGals {__version__}")
    args = parser.parse_args()

    global variables
    categories, variables = load_config()
    if not categories:
        print("No categories found in gals.conf")
        sys.exit(1)

    test_limit = 10 if args.t else 0
    gals_per_page = int(variables.get("GalsinPage", 23))
    max_age_days = int(variables.get("N", 0))

    if args.a:
        categories = [c for c in categories if "an" in c]

    data_dir = DATA_DIR
    data_dir.mkdir(exist_ok=True)

    datum = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_dir = data_dir / datum
    out_dir.mkdir()

    wget_args = build_wget_args(variables, include_images=args.i)
    if args.i:
        print("Include images")

    print(f"Getting Gals on {datum} (booksi {__version__})")
    print(categories)
    print()

    for cat in categories:
        print(cat, end=" ")
        total = fetch_category(cat, out_dir, wget_args, gals_per_page, test_limit)
        print(total)

    print("Cleaning up...")
    cleanup_downloads(out_dir)
    rename_jpgs(str(out_dir))

    prune_old_data(data_dir, max_age_days)

    # Tar backup — kept locally (gdrive upload was deprecated)
    tar_path = data_dir / f"{datum}.tar.gz"
    subprocess.run(["tar", "-zcf", str(tar_path), str(out_dir)])

    if not args.f:
        shutil.rmtree(out_dir)

    print("Finished!")


if __name__ == "__main__":
    main()
