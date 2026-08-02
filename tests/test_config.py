"""Tests for booksi.config module."""

import os

import pytest

from booksi.config import load_categories


class TestLoadCategories:
    def test_loads_from_gals_conf(self):
        categories = load_categories("gals.conf")
        assert len(categories) == 4
        names = [c["name"] for c in categories]
        assert "analsex" in names
        assert "anal_natur_no_condom" in names

    def test_parses_flags(self):
        categories = load_categories("gals.conf")
        anal = next(c for c in categories if c["name"] == "analsex")
        assert anal["flags"]["a1"] is True
        assert anal["flags"]["a0"] is False
        assert anal["flags"]["cim"] is False
        assert anal["flags"]["cof"] is False

    def test_multiple_flags(self):
        categories = load_categories("gals.conf")
        natur = next(c for c in categories if c["name"] == "anal_natur_no_condom")
        assert natur["flags"]["a1"] is True
        assert natur["flags"]["a0"] is True

    def test_cum_flags(self):
        categories = load_categories("gals.conf")
        cof = next(c for c in categories if "cum_on_face" in c["name"])
        assert cof["flags"]["cof"] is True
        cim = next(c for c in categories if "cum_in_mouth" in c["name"])
        assert cim["flags"]["cim"] is True

    def test_missing_file_returns_empty(self):
        categories = load_categories("nonexistent.conf")
        assert categories == []

    def test_custom_config(self, tmp_path):
        conf = tmp_path / "test.conf"
        conf.write_text("[htmls]\n# comment\ntest_category a1 cof\nanother\n")
        categories = load_categories(str(conf))
        assert len(categories) == 2
        assert categories[0]["name"] == "test_category"
        assert categories[0]["flags"]["a1"] is True
        assert categories[0]["flags"]["cof"] is True
        assert categories[0]["flags"]["a0"] is False
        assert categories[1]["name"] == "another"
        assert all(v is False for v in categories[1]["flags"].values())
