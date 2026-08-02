"""Tests for booksi.parse module."""

import os

import pytest

from booksi.parse import extract_price, ex_names


class TestExtractPrice:
    def test_hourly_price(self):
        # Returns highest price found
        assert extract_price("15 Minuten 40€ / 60 Minuten 100€") == "100€"

    def test_hourly_only(self):
        assert extract_price("100€ / Stunde") == "100€"

    def test_returns_highest(self):
        assert extract_price("80€ / 120€ / 200€") == "200€"

    def test_price_with_euro(self):
        assert extract_price("Stunde nur 150€") == "150€"

    def test_price_no_match(self):
        assert extract_price("Kein Preis angegeben") == ""

    def test_empty_string(self):
        assert extract_price("") == ""

    def test_none(self):
        assert extract_price(None) == ""

    def test_whitespace_only(self):
        assert extract_price("   ") == ""

    def test_simple_price(self):
        assert extract_price("80€") == "80€"

    def test_price_in_long_text(self):
        text = "Das ist ein langer Text mit 200€ pro Stunde und mehr"
        assert extract_price(text) == "200€"


class TestExNames:
    def test_extracts_base_names(self, data_dir):
        (data_dir / "analsex1.html").touch()
        (data_dir / "analsex2.html").touch()
        (data_dir / "natur1.html").touch()
        (data_dir / "readme.md").touch()
        result = ex_names(str(data_dir))
        assert result == ["analsex", "natur"]

    def test_deduplicates(self, data_dir):
        (data_dir / "cat1.html").touch()
        (data_dir / "cat2.html").touch()
        (data_dir / "cat3.html").touch()
        result = ex_names(str(data_dir))
        assert result == ["cat"]

    def test_empty_dir(self, data_dir):
        assert ex_names(str(data_dir)) == []

    def test_sorts_alphabetically(self, data_dir):
        (data_dir / "zulu1.html").touch()
        (data_dir / "alpha1.html").touch()
        result = ex_names(str(data_dir))
        assert result == ["alpha", "zulu"]
