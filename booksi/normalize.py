"""Normalize/merge — dedupe, stats, top rows."""

import re
import pandas as pd


def dfComprehend(dfnew):
    """Dedupe and filter DataFrame."""
    if dfnew.empty:
        return dfnew

    pattern = r"trans|^ts |^Ts_|real.*doll|doll.*real"
    pattern = re.compile(pattern, re.IGNORECASE)

    oldnum = len(dfnew.index)
    print("    ", +oldnum, "comprehended to ", end="", flush=True)
    dfnew = dfnew.sort_values(by=["Girl"], ascending=True)

    dfnew = dfnew[
        ~(
            dfnew["Girl"].str.contains(pattern, na=False)
            | dfnew["Short"].str.contains(pattern, na=False)
        )
    ]
    # Group by Girl, Tel, and sid to avoid merging different profiles with same name
    # Drop rows with missing group keys first (previously dropped silently by
    # groupby's dropna), then coerce object columns to str so .max() never
    # compares incompatible types (e.g. Fans as int 0 vs str "905", Purl None vs str).
    dfnew = dfnew.dropna(subset=["Girl", "Tel", "sid"])
    for col in dfnew.columns:
        if col not in ("Girl", "Tel", "sid") and dfnew[col].dtype == object:
            dfnew[col] = dfnew[col].fillna("").astype(str)
    dfnew = dfnew.groupby(["Girl", "Tel", "sid"], as_index=False).max()

    newnum = len(dfnew.index)
    percentage = (oldnum - len(dfnew.index)) / oldnum * 100
    print(f"{newnum} -{percentage:.0f}%")
    return dfnew


def dups(df, columnid=""):
    """Count duplicates in a column."""
    dups = 0
    total = len(df)
    counts = df[columnid].value_counts()
    duplicates = counts[counts > 1]
    duplicate_list = list(zip(duplicates.index, duplicates.values))
    for columnid, occurrences in duplicate_list:
        dups += occurrences
    print(f"    Total: {total}, Uniques: {total - dups}")


def get_top_10_rows(top_10_rows, amount=10, Top=True, title="", print_top_10_rows=True):
    """Get top N rows by Fans."""
    import wcwidth
    top_10_rows = top_10_rows.fillna("")
    top_10_rows["Fans"] = (
        top_10_rows["Fans"]
        .astype(str)
        .str.replace(r"\u202f|\xa0|\s", "", regex=True)
        .replace("", "0")
        .astype(int)
    )
    top_10_rows = (
        top_10_rows[["Girl", "Strasse", "Fans", "a1", "a0", "cim", "cof"]]
        .sort_values("Fans", ascending=not Top)
        .head(amount)
    )
    top_10_rows = top_10_rows.reset_index(drop=True)
    top_10_rows.index += 1
    top_10_rows.index.name = "Rank"
    if print_top_10_rows:
        fancy_print(title, level=2)
        print(top_10_rows)
    return top_10_rows


def someStats(df):
    """Print statistics about the data."""
    rows_all_checkmarks = df[
        (df["a1"] == "✓") & (df["a0"] == "✓") & (df["cof"] == "✓") & (df["cim"] == "✓")
    ]
    rows_both_a1_a0 = df[(df["a1"] == "✓") & (df["a0"] == "✓")]
    rows_both_cum = df[(df["cof"] == "✓") & (df["cim"] == "✓")]
    rows_a0_only = df[(df["a1"] != "✓") & (df["a0"] == "✓")]

    get_top_10_rows(rows_all_checkmarks, 5, title="TOP Supergals              🍑🍑💦💦")
    get_top_10_rows(rows_both_a1_a0, 5, title="TOP Ass                🍑🍑")
    get_top_10_rows(rows_both_cum, 5, title="TOP Cum              💦💦")
    get_top_10_rows(rows_a0_only, 5, 5, title="TOP Ass0              0🍑")

    print("Tels:")
    dups(df, "Tel")


def fancy_print(message, level=1):
    import wcwidth
    if level == 1:
        header = f"=== {message} ==="
        line = "=" * sum(wcwidth.wcwidth(c) for c in header)
    elif level == 2:
        header = f"--- {message} ---"
        line = "-" * sum(wcwidth.wcwidth(c) for c in header)
    else:
        header = f"{message}"

    if level in [1, 2]:
        print(line)
    print(header)
    if level in [1, 2]:
        print(line)