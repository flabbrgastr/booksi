"""Tests for booksi.normalize module."""

import pandas as pd

from booksi.normalize import dfComprehend


class TestDfComprehend:
    def test_removes_trans_entries(self):
        df = pd.DataFrame({
            "Girl": ["Alice", "Trans_ts_model", "Bob"],
            "Tel": ["1", "2", "3"],
            "sid": [1, 2, 3],
            "Short": ["normal", "normal", "normal"],
            "a1": ["", "", ""],
            "a0": ["", "", ""],
            "cim": ["", "", ""],
            "cof": ["", "", ""],
        })
        result = dfComprehend(df)
        assert len(result) == 2
        assert "Trans_ts_model" not in result["Girl"].values

    def test_removes_doll_entries(self):
        df = pd.DataFrame({
            "Girl": ["Alice", "Real Doll", "Bob"],
            "Tel": ["1", "2", "3"],
            "sid": [1, 2, 3],
            "Short": ["normal", "normal", "normal"],
            "a1": ["", "", ""],
            "a0": ["", "", ""],
            "cim": ["", "", ""],
            "cof": ["", "", ""],
        })
        result = dfComprehend(df)
        assert len(result) == 2

    def test_deduplicates_by_girl_tel_sid(self):
        df = pd.DataFrame({
            "Girl": ["Alice", "Alice", "Bob"],
            "Tel": ["111", "111", "222"],
            "sid": [1, 1, 2],
            "Short": ["v1", "v2", "normal"],
            "a1": ["", "✓", ""],
            "a0": ["", "", ""],
            "cim": ["", "", ""],
            "cof": ["", "", ""],
        })
        result = dfComprehend(df)
        assert len(result) == 2
        alice = result[result["Girl"] == "Alice"]
        assert len(alice) == 1

    def test_empty_dataframe(self):
        df = pd.DataFrame(columns=["Girl", "Tel", "sid", "Short", "a1", "a0", "cim", "cof"])
        result = dfComprehend(df)
        assert len(result) == 0

    def test_filters_in_short(self):
        # Pattern is ^ts (starts with "ts"), not just contains "ts"
        df = pd.DataFrame({
            "Girl": ["Alice", "Bob"],
            "Tel": ["1", "2"],
            "sid": [1, 2],
            "Short": ["normal", "ts Studio available"],
            "a1": ["", ""],
            "a0": ["", ""],
            "cim": ["", ""],
            "cof": ["", ""],
        })
        result = dfComprehend(df)
        assert len(result) == 1
        assert "Alice" in result["Girl"].values
