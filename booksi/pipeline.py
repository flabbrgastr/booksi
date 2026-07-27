"""Pipeline — orchestrate the full data processing flow."""

import os
import shutil
import sys

import pandas as pd

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


def _delta_tag(pdall, new_delta=5, old_delta=0, verbose=False):
    """Tag new and updated sids across the last N days of data."""
    new = new_delta
    old = old_delta

    for old_idx in range(old, new, -1):
        new_sids = newsidlist(old_idx, new, verbose=verbose)
        changed_sids = update_dataframe(old_idx, new, verbose=verbose)
        if verbose:
            print(f"     New{old_idx} {len(new_sids)} : Upd{old_idx} {len(changed_sids)}")
        pdall.loc[pdall["sid"].isin(new_sids), "t"] = f"new{old_idx}"
        pdall.loc[pdall["sid"].isin(changed_sids), "t"] = f"upd{old_idx}"


def _write_outputs(pdall, lastdir, show_stats=False):
    """Write CSV, HTML, and copy to web root."""
    if not os.path.exists(lastdir + "/gen/"):
        os.makedirs(lastdir + "/gen/")

    csv_file = lastdir + "/gen/" + "all.csv"
    pdall.to_csv(csv_file, index=False, mode="w")
    print("     all.csv")

    if show_stats:
        someStats(pdall)

    html_table = convert_dataframe_to_html(pdall)
    html_file = lastdir + "/gen/" + "all.html"
    with open(html_file, "w") as hfile:
        hfile.write(html_table)

    shutil.copy2(html_file, "./all.html", follow_symlinks=True)
    shutil.copy2(html_file, "/var/www/booksi/all.html", follow_symlinks=True)
    print("     all.html -> ./all.html, /var/www/booksi/all.html")

    return {
        "csv_path": csv_file,
        "html_path": html_file,
        "web_copy": "/var/www/booksi/all.html",
    }


def run_pipeline(
    dir_path="./data",
    csv_import=False,
    show_stats=False,
    verbose=False,
    delta_range=5,
):
    """Run the full booksi data processing pipeline.

    Args:
        dir_path: Path to the data directory.
        csv_import: If True, skip HTML parsing and read existing CSV.
        show_stats: If True, print summary statistics.
        verbose: If True, print detailed output.
        delta_range: Number of historical days to compare for delta tagging.

    Returns:
        dict with output paths and metadata.
    """
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

    # Step 6: Delta comparison and tagging
    pdall["sid"] = pdall["sid"].astype(int)
    # Ensure 't' column is string dtype to avoid pandas 3.x dtype coercion errors
    pdall["t"] = pdall["t"].fillna("").astype(str)
    _delta_tag(pdall, new_delta=0, old_delta=delta_range, verbose=verbose)

    # Step 7: Write outputs
    return _write_outputs(pdall, lastdir, show_stats=show_stats)