"""Storage — file/disk utilities for data management, pruning, delta comparison."""

import os
import re
import shutil
from collections import defaultdict
from datetime import datetime

import pandas as pd

from booksi.config import CSV_FILENAME, DATA_DIR


def prune_items(path, test_mode=True):
    """Prune old data directories/files, keeping most recent per day/week."""
    files_by_week = defaultdict(lambda: defaultdict(list))
    folders_by_week = defaultdict(lambda: defaultdict(list))
    now = datetime.now()
    pruned_items = 0

    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        try:
            item_date = datetime.strptime(item[:10], "%Y-%m-%d")
        except ValueError:
            print(f"Skipping {item}, does not match expected format")
            continue

        weeks_since_creation = (now - item_date).days // 7

        if os.path.isfile(item_path):
            files_by_week[weeks_since_creation][item_date].append(item_path)
        elif os.path.isdir(item_path):
            folders_by_week[weeks_since_creation][item_date].append(item_path)

    for week, files_by_date in files_by_week.items():
        for date, files in files_by_date.items():
            files.sort(key=lambda x: os.path.getctime(x), reverse=True)
            for file in files[1:]:
                if test_mode:
                    print(f"Test mode: Would delete file {file}")
                else:
                    os.remove(file)
                    pruned_items += 1

    for week, folders_by_date in folders_by_week.items():
        for date, folders in folders_by_date.items():
            folders.sort(key=lambda x: os.path.getctime(x), reverse=True)
            for folder in folders[1:]:
                if test_mode:
                    print(f"Test mode: Would delete folder {folder}")
                else:
                    shutil.rmtree(folder)
                    pruned_items += 1

    return pruned_items


def getlastdir(dir_path):
    """Get the most recent date-stamped directory in path."""
    directories = sorted(
        [
            d for d in os.listdir(dir_path)
            if os.path.isdir(os.path.join(dir_path, d))
        ],
        reverse=True,
    )
    return os.path.join(dir_path, directories[0]) if directories else None


def findhtmls(dir_path):
    """Find (category) HTML files without numbers in name."""
    htmls = []
    for file in os.listdir(dir_path):
        if file.endswith(".html") and not any(char.isdigit() for char in file):
            htmls.append(file)
    return htmls


def check_file_exists(filename):
    """Check if a file exists and return open handle."""
    try:
        return open(filename, "r")
    except FileNotFoundError:
        print(f"The file {filename} does not exist!")
        return None


def count_occurrences(file_path, pattern):
    """Count regex pattern occurrences in a file."""
    with open(file_path, "r") as f:
        content = f.read()
    return len(re.findall(pattern, content))


def matchdir(path, delta):
    """Find directory closest to N days old."""
    current_date = datetime.now().date()
    dir_delta_pairs = []

    for directory in os.listdir(path):
        full = os.path.join(path, directory)
        if not os.path.isdir(full):
            continue
        try:
            date_str = directory.split("_")[0]
            dir_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            continue
        dir_delta = (current_date - dir_date).days
        dir_delta_pairs.append((directory, dir_delta))

    if not dir_delta_pairs:
        return None, None

    closest_delta = min(dir_delta_pairs, key=lambda x: abs(delta - x[1]))[1]
    closest_dir = next(
        (p[0] for p in dir_delta_pairs if p[1] == closest_delta), None
    )
    return closest_dir, closest_delta


def _resolve_folder(folder, dir_path, default_delta=0):
    """Resolve int delta or string folder name to path and delta."""
    if isinstance(folder, int):
        name, delta = matchdir(dir_path, folder)
        if name is None:
            return None, delta
        return os.path.join(dir_path, name, "gen", "all.csv"), delta
    else:
        csv = os.path.join(dir_path, folder, "gen", "all.csv")
        try:
            date_str = folder.split("_")[0]
            folder_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            delta = (datetime.now().date() - folder_date).days
        except ValueError:
            delta = default_delta
        return csv, delta


def newsidlist(old_folder, new_folder, column="sid", dir_path=None, verbose=False):
    """Find new sids in new_folder not present in old_folder."""
    if dir_path is None:
        dir_path = str(DATA_DIR)
    old_csv, deltaold = _resolve_folder(old_folder, dir_path)
    new_csv, deltanew = _resolve_folder(new_folder, dir_path)

    if not old_csv or not os.path.exists(old_csv) or deltaold == 0:
        if verbose:
            print(f"No historical data (delta={deltaold}). Using empty DataFrame.")
        old_df = pd.DataFrame(columns=[column])
    else:
        old_df = pd.read_csv(old_csv)

    new_df = pd.read_csv(new_csv)

    new_values = new_df[~new_df[column].isin(old_df[column])][column].tolist()

    if verbose:
        matched = new_df[new_df[column].isin(new_values)]
        print(f"{len(matched)} new rows:")
        print(matched)
        print(f"Old delta: {deltaold}, New delta: {deltanew}")

    return new_values


def update_dataframe(old_folder, new_folder, dir_path=None, verbose=False):
    """Find sids where Tel, Strasse, or Girl changed between old and new."""
    if dir_path is None:
        dir_path = str(DATA_DIR)
    old_csv, deltaold = _resolve_folder(old_folder, dir_path)
    new_csv, deltanew = _resolve_folder(new_folder, dir_path)

    if not old_csv or not os.path.exists(old_csv) or deltaold == 0:
        if verbose:
            print(f"No historical data (delta={deltaold}). Using empty DataFrame.")
        old_df = pd.DataFrame(columns=["sid", "Girl", "Tel", "Strasse"])
    else:
        old_df = pd.read_csv(old_csv).fillna("")

    new_df = pd.read_csv(new_csv).fillna("")

    merged = pd.merge(old_df, new_df, on="sid", suffixes=("_old", "_new"))
    changed = merged[
        (merged["Tel_old"] != merged["Tel_new"])
        | (merged["Strasse_old"] != merged["Strasse_new"])
        | (merged["Girl_old"] != merged["Girl_new"])
    ]

    changed_sids = changed["sid"].tolist()

    if verbose and not changed.empty:
        print("Differences found:")
        print(
            changed[
                ["sid", "Girl_old", "Girl_new", "Tel_old", "Tel_new",
                 "Strasse_old", "Strasse_new"]
            ]
        )
    elif verbose:
        print("No differences found.")

    return changed_sids