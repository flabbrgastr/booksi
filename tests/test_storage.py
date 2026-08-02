"""Tests for booksi.storage module."""

import os
import shutil
from datetime import datetime, timedelta

import pandas as pd
import pytest

from booksi.storage import (
    findhtmls,
    getlastdir,
    matchdir,
    newsidlist,
    prune_items,
    update_dataframe,
)


class TestGetlastdir:
    def test_returns_most_recent(self, data_dir):
        (data_dir / "2025-01-01_000000").mkdir()
        (data_dir / "2025-01-03_000000").mkdir()
        (data_dir / "2025-01-02_000000").mkdir()
        result = getlastdir(str(data_dir))
        assert result.endswith("2025-01-03_000000")

    def test_returns_none_when_empty(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        result = getlastdir(str(empty))
        assert result is None

    def test_ignores_files(self, data_dir):
        (data_dir / "2025-01-01_000000").mkdir()
        (data_dir / "somefile.txt").touch()
        result = getlastdir(str(data_dir))
        assert result.endswith("2025-01-01_000000")


class TestFindhtmls:
    def test_finds_html_without_numbers(self, data_dir):
        (data_dir / "analsex.html").touch()
        (data_dir / "analsex1.html").touch()
        (data_dir / "natur.html").touch()
        (data_dir / "readme.md").touch()
        result = findhtmls(str(data_dir))
        assert sorted(result) == ["analsex.html", "natur.html"]

    def test_empty_dir(self, data_dir):
        assert findhtmls(str(data_dir)) == []


class TestMatchdir:
    def test_finds_closest_dir(self, data_dir):
        today = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        (data_dir / today).mkdir()
        result_name, delta = matchdir(str(data_dir), 0)
        assert result_name is not None
        assert delta == 0

    def test_returns_none_for_empty(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        name, delta = matchdir(str(empty), 0)
        assert name is None

    def test_finds_closest_to_delta(self, data_dir):
        now = datetime.now()
        for days_ago in [1, 3, 7]:
            d = (now - timedelta(days=days_ago)).strftime("%Y-%m-%d_120000")
            (data_dir / d).mkdir()
        name, delta = matchdir(str(data_dir), 3)
        assert delta == 3


class TestPruneItems:
    def test_prune_counts_in_real_mode(self, data_dir):
        today = datetime.now().strftime("%Y-%m-%d")
        (data_dir / f"{today}_010000").mkdir()
        (data_dir / f"{today}_020000").mkdir()
        (data_dir / f"{today}_030000").mkdir()
        pruned = prune_items(str(data_dir), test_mode=False)
        assert pruned == 2
        # Only one should remain
        remaining = [d for d in data_dir.iterdir() if d.is_dir()]
        assert len(remaining) == 1

    def test_prune_test_mode_does_not_delete(self, data_dir):
        today = datetime.now().strftime("%Y-%m-%d")
        (data_dir / f"{today}_010000").mkdir()
        (data_dir / f"{today}_020000").mkdir()
        (data_dir / f"{today}_030000").mkdir()
        pruned = prune_items(str(data_dir), test_mode=True)
        # 3 dirs same date → 2 pruned (keeps newest), but none deleted
        assert pruned == 2
        remaining = [d for d in data_dir.iterdir() if d.is_dir()]
        assert len(remaining) == 3

    def test_prune_nothing_when_one(self, data_dir):
        today = datetime.now().strftime("%Y-%m-%d")
        (data_dir / f"{today}_010000").mkdir()
        pruned = prune_items(str(data_dir), test_mode=True)
        assert pruned == 0


class TestNewsidlist:
    def test_finds_new_sids(self, data_dir, twoDATED_dirs):
        old, new = twoDATED_dirs
        # Pass dirnames relative to parent, not full paths
        old_name = old.name
        new_name = new.name
        new_sids = newsidlist(old_name, new_name, dir_path=str(data_dir))
        assert 103 in new_sids
        assert 101 not in new_sids
        assert 102 not in new_sids

    def test_same_day_skips_comparison(self, data_dir):
        # When deltaold == 0, newsidlist treats old as empty (design choice)
        today = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        d = data_dir / today
        d.mkdir()
        (d / "gen").mkdir()
        pd.DataFrame({"sid": [1, 2, 3]}).to_csv(d / "gen" / "all.csv", index=False)
        new_sids = newsidlist(str(d), str(d))
        # All sids appear "new" because old is treated as empty
        assert new_sids == [1, 2, 3]


class TestUpdateDataframe:
    def test_finds_changed_rows(self, data_dir, twoDATED_dirs):
        old, new = twoDATED_dirs
        changed = update_dataframe(old.name, new.name, dir_path=str(data_dir))
        assert 102 in changed  # Strasse changed from B to B_new
        assert 101 not in changed  # unchanged

    def test_same_day_treats_old_as_empty(self, data_dir):
        # When deltaold == 0, treats old as empty — no changes detected
        today = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        d = data_dir / today
        d.mkdir()
        (d / "gen").mkdir()
        pd.DataFrame({
            "sid": [1], "Girl": ["X"], "Tel": ["1"], "Strasse": ["A"]
        }).to_csv(d / "gen" / "all.csv", index=False)
        changed = update_dataframe(str(d), str(d))
        assert changed == []
