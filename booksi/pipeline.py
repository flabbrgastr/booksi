"""Pipeline — orchestrate the full data processing flow."""

import os
import shutil
import sys
from pathlib import Path

import pandas as pd

from booksi.config import CSV_FILENAME, DATA_DIR, HTML_FILENAME, LOCAL_HTML, WEB_ROOT
from booksi.parse import cat_files, ex_names, get_gals
from booksi.normalize import dfComprehend, someStats
from booksi.render import convert_dataframe_to_html
from booksi.storage import findhtmls, getlastdir, newsidlist, prune_items, update_dataframe


def _preprocess_html(dir_path, names):
    """Concatenate split HTML files for each category into one."""
    for name in names:
        cat_files(dir_path, name, remove=True)


def _parse_gals(dir_path, html_files, verbose=False):
    """Parse all category HTML files and return a combined DataFrame."""
    pdall = pd.DataFrame()
    for file in html_files:
        category = os.path.splitext(file)[0]
        arr = get_gals(dir_path, file)
        df = pd.DataFrame(arr)
        pdall = pd.concat([pdall, df], ignore_index=True)
    return pdall


def _delta_tag(pdall, from_day=5, to_day=0, verbose=False):
    """Tag new and updated sids across the last N days of data.

    Args:
        pdall: DataFrame to tag in-place.
        from_day: Start comparing from this many days back (inclusive).
        to_day: Stop comparing at this many days back (exclusive).
                 E.g. from_day=5, to_day=0 compares days 5,4,3,2,1 vs today.
    """
    for day in range(from_day, to_day, -1):
        new_sids = newsidlist(day, 0, verbose=verbose)
        changed_sids = update_dataframe(day, 0, verbose=verbose)
        if verbose:
            print(f"     New{day} {len(new_sids)} : Upd{day} {len(changed_sids)}")
        pdall.loc[pdall["sid"].isin(new_sids), "t"] = f"new{day}"
        pdall.loc[pdall["sid"].isin(changed_sids), "t"] = f"upd{day}"


def _write_outputs(pdall, lastdir, show_stats=False):
    """Write CSV, HTML, and copy to web root."""
    gen_dir = Path(lastdir) / "gen"
    gen_dir.mkdir(exist_ok=True)

    csv_file = gen_dir / CSV_FILENAME
    pdall.to_csv(csv_file, index=False, mode="w")
    print(f"     {CSV_FILENAME}")

    if show_stats:
        someStats(pdall)

    html_table = convert_dataframe_to_html(pdall)
    html_file = gen_dir / HTML_FILENAME
    html_file.write_text(html_table)

    shutil.copy2(html_file, LOCAL_HTML, follow_symlinks=True)
    web_copy = WEB_ROOT / HTML_FILENAME
    shutil.copy2(html_file, web_copy, follow_symlinks=True)
    print(f"     {HTML_FILENAME} -> {LOCAL_HTML}, {web_copy}")

    return {
        "csv_path": str(csv_file),
        "html_path": str(html_file),
        "web_copy": str(web_copy),
    }


def run_pipeline(
    dir_path=None,
    csv_import=False,
    show_stats=False,
    verbose=False,
    delta_range=5,
):
    """Run the full booksi data processing pipeline.

    Args:
        dir_path: Path to the data directory (defaults to BOOKSI_DATA_DIR env var).
        csv_import: If True, skip HTML parsing and read existing CSV.
        show_stats: If True, print summary statistics.
        verbose: If True, print detailed output.
        delta_range: Number of historical days to compare for delta tagging.

    Returns:
        dict with output paths and metadata.
    """
    if dir_path is None:
        dir_path = str(DATA_DIR)
    # Step 1: Prune old data
    pruned_items = prune_items(dir_path, test_mode=False)
    if pruned_items:
        print(str(pruned_items) + "   items pruned")

    # Step 2: Find latest data directory
    lastdir = getlastdir(dir_path)
    if lastdir is None:
        raise FileNotFoundError(f"No data directories found in {dir_path}")

    if verbose:
        print("⌵ processing " + lastdir[2:])

    if csv_import:
        # Ingest existing CSV file directly
        pdall = pd.read_csv(lastdir + "/gen/all.csv")
        if show_stats:
            someStats(pdall)
    else:
        # Step 3: Preprocess HTML files — concatenate split files into categories
        names = ex_names(lastdir)
        if names:
            if verbose:
                print("html preprocessing " + lastdir[2:])
            _preprocess_html(lastdir, names)

        # Step 4: Parse gals from HTML
        html_files = findhtmls(lastdir)
        pdall = _parse_gals(lastdir, html_files, verbose=verbose)

        # Step 5: Dedupe and filter
        pdall = dfComprehend(pdall)

    pdall["sid"] = pdall["sid"].astype(int)
    # Ensure 't' column is string dtype to avoid pandas 3.x dtype coercion errors
    pdall["t"] = pdall["t"].fillna("").astype(str)

    # Step 6: Write CSV first (delta tagging reads it from disk)
    if not os.path.exists(lastdir + "/gen/"):
        os.makedirs(lastdir + "/gen/")
    csv_file = lastdir + "/gen/all.csv"
    pdall.to_csv(csv_file, index=False, mode="w")
    if verbose:
        print("     all.csv")

    # Step 7: Delta comparison and tagging
    _delta_tag(pdall, from_day=delta_range, to_day=0, verbose=verbose)

    # Step 8: Write HTML outputs
    return _write_outputs(pdall, lastdir, show_stats=show_stats)