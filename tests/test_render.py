"""Tests for booksi.render module."""

import pandas as pd
import pytest

from booksi.render import convert_dataframe_to_html


class TestConvertDataframeToHtml:
    def test_returns_html_string(self, sample_dataframe):
        result = convert_dataframe_to_html(sample_dataframe)
        assert isinstance(result, str)
        assert "<html>" in result
        assert "</html>" in result

    def test_contains_table(self, sample_dataframe):
        result = convert_dataframe_to_html(sample_dataframe)
        assert "<table" in result
        assert "</table>" in result

    def test_contains_sortable_js(self, sample_dataframe):
        result = convert_dataframe_to_html(sample_dataframe)
        assert "sortable" in result

    def test_contains_girl_names(self, sample_dataframe):
        result = convert_dataframe_to_html(sample_dataframe)
        assert "Alice" in result
        assert "Bob" in result
        assert "Charlie" in result

    def test_images_added(self, sample_dataframe):
        result = convert_dataframe_to_html(sample_dataframe)
        assert "<img" in result
        assert "http://img/a.jpg" in result

    def test_girl_names_are_links(self, sample_dataframe):
        result = convert_dataframe_to_html(sample_dataframe)
        assert '<a href="http://a.com"' in result

    def test_checkmarks_replaced(self, sample_dataframe):
        result = convert_dataframe_to_html(sample_dataframe)
        assert "🍑" in result  # a0 or a1 with ✓
        assert "💦" in result  # cim or cof with ✓

    def test_empty_dataframe(self):
        df = pd.DataFrame(columns=[
            "Girl", "Stadt", "Bezirk", "Strasse", "Fans", "Score",
            "Short", "Preis", "Tel", "Gurl", "Purl",
            "a1", "a0", "cim", "cof", "sid", "gid", "t",
        ])
        result = convert_dataframe_to_html(df)
        assert "<table" in result
        assert "Gals: 0" in result

    def test_t_column_shows_new_tag(self, sample_dataframe):
        sample_dataframe.loc[0, "t"] = "new1"
        result = convert_dataframe_to_html(sample_dataframe)
        assert "new1" in result
