"""
Tests for field value normalization and parsing.
"""

from __future__ import annotations

import builtins
import datetime
from decimal import Decimal
import logging

from django.db import models
import pytest

from apps.imports.scrapers import viernulvier
from apps.imports.scrapers.viernulvier import (
    clean_string,
    clean_vendor_id,
    normalize_performer_type,
    normalize_url,
    _parse_field_value,
)


# ---------------------------------------------------------------------------
# clean_string
# ---------------------------------------------------------------------------


class TestCleanString:
    def test_strips_surrounding_whitespace(self) -> None:
        assert clean_string("  hello  ") == "hello"

    def test_removes_null_byte(self) -> None:
        result = clean_string("hello\x00world")
        assert "\x00" not in result
        assert "hello" in result

    def test_keeps_tab_newline_cr(self) -> None:
        result = clean_string("a\tb\rc\nd")
        assert "\t" in result
        assert "\r" in result
        assert "\n" in result

    def test_removes_other_control_chars(self) -> None:
        assert clean_string("a\x01\x08\x0b\x0c\x0e\x1fb") == "ab"

    def test_none_returns_empty_string(self) -> None:
        assert clean_string(None) == ""

    def test_preserves_unicode(self) -> None:
        assert clean_string("Café 🎭") == "Café 🎭"


# ---------------------------------------------------------------------------
# clean_vendor_id
# ---------------------------------------------------------------------------


class TestCleanVendorId:
    def test_none_returns_none(self) -> None:
        assert clean_vendor_id(None) is None

    def test_empty_string_returns_none(self) -> None:
        assert clean_vendor_id("") is None

    def test_whitespace_only_returns_none(self) -> None:
        assert clean_vendor_id("   ") is None

    def test_html_like_value_returns_none(self) -> None:
        assert clean_vendor_id("<i class='icon'>vendor</i>") is None

    def test_valid_string_returned_stripped(self) -> None:
        assert clean_vendor_id("  ABC123  ") == "ABC123"

    def test_valid_string_no_stripping_needed(self) -> None:
        assert clean_vendor_id("V42") == "V42"


# ---------------------------------------------------------------------------
# normalize_url
# ---------------------------------------------------------------------------


class TestNormalizeUrl:
    @pytest.mark.parametrize("value", ["", "0", "none", "null", "undefined", "-", "n/a", "nvt", None])
    def test_empty_like_values_return_empty_string(self, value) -> None:
        assert normalize_url(value) == ""

    def test_valid_https_url_returned(self) -> None:
        assert normalize_url("https://example.com/path") == "https://example.com/path"

    def test_invalid_url_returns_empty(self) -> None:
        assert normalize_url("not-a-url") == ""

    def test_whitespace_stripped_before_validation(self) -> None:
        assert normalize_url("  https://example.com  ") == "https://example.com"

    def test_case_insensitive_empty_checks(self) -> None:
        assert normalize_url("NONE") == ""
        assert normalize_url("NULL") == ""
        assert normalize_url("N/A") == ""


# ---------------------------------------------------------------------------
# normalize_performer_type
# ---------------------------------------------------------------------------


class TestNormalizePerformerType:
    def test_person_maps_to_solo(self) -> None:
        assert normalize_performer_type("person") == "solo"

    def test_group_passed_through_lowercase(self) -> None:
        assert normalize_performer_type("GROUP") == "group"

    def test_none_returns_empty_string(self) -> None:
        assert normalize_performer_type(None) == ""

    def test_unknown_value_lowercased(self) -> None:
        assert normalize_performer_type("DUO") == "duo"


# ---------------------------------------------------------------------------
# _parse_field_value - Comprehensive Type Coverage
# ---------------------------------------------------------------------------


class TestParseFieldValue:
    def test_charfield_cleans_and_returns(self) -> None:
        f = models.CharField(max_length=100)
        assert _parse_field_value(f, "  hello  ") == "hello"

    def test_charfield_truncates_to_max_length(self) -> None:
        f = models.CharField(max_length=5)
        result = _parse_field_value(f, "hello world")
        assert result == "hello"
        assert len(result) == 5

    def test_textfield_none_returns_none(self) -> None:
        assert _parse_field_value(models.TextField(), None) is None

    def test_urlfield_valid_url_returned(self) -> None:
        f = models.URLField()
        assert _parse_field_value(f, "https://example.com") == "https://example.com"

    def test_booleanfield_ja_true(self) -> None:
        assert _parse_field_value(models.BooleanField(), "ja") is True

    def test_booleanfield_nee_false(self) -> None:
        assert _parse_field_value(models.BooleanField(), "nee") is False

    def test_decimalfield_valid_string(self) -> None:
        f = models.DecimalField(max_digits=10, decimal_places=2)
        assert _parse_field_value(f, "25.50") == Decimal("25.50")

    def test_decimalfield_integer_input(self) -> None:
        f = models.DecimalField(max_digits=10, decimal_places=2)
        assert _parse_field_value(f, 10) == Decimal(10)

    def test_decimalfield_invalid_returns_none(self, caplog) -> None:
        f = models.DecimalField(max_digits=10, decimal_places=2)
        caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)
        assert _parse_field_value(f, "not-a-decimal") is None

    def test_integerfield_valid_string(self) -> None:
        assert _parse_field_value(models.IntegerField(), "42") == 42

    def test_integerfield_invalid_returns_none(self, caplog) -> None:
        caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)
        assert _parse_field_value(models.IntegerField(), "abc") is None

    def test_floatfield_valid(self) -> None:
        assert _parse_field_value(models.FloatField(), "3.14") == pytest.approx(3.14)

    def test_floatfield_invalid_returns_none(self, caplog) -> None:
        caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)
        assert _parse_field_value(models.FloatField(), "xyz") is None

    def test_datetimefield_negative_year_repaired(self) -> None:
        result = _parse_field_value(models.DateTimeField(), "-2024-06-01T00:00:00Z")
        assert result is not None
        assert result.year == 2024

    def test_datetimefield_non_string_passthrough(self) -> None:
        value = datetime.datetime(2024, 6, 1, 12, 30, tzinfo=datetime.UTC)
        assert _parse_field_value(models.DateTimeField(), value) is value

    def test_datetimefield_year_zero_mapped_to_1970(self) -> None:
        result = _parse_field_value(models.DateTimeField(), "0000-12-25T10:00:00Z")
        assert result is not None
        assert result.year == 1970

    def test_datetimefield_unparseable_returns_none(self, caplog) -> None:
        caplog.set_level(logging.DEBUG, logger=viernulvier.logger.name)
        assert _parse_field_value(models.DateTimeField(), "definitely-not-a-date") is None

    def test_datefield_valid_string(self) -> None:
        result = _parse_field_value(models.DateField(), "2024-07-04")
        assert result is not None
        assert result.year == 2024
        assert result.month == 7
        assert result.day == 4

    def test_jsonfield_passthrough(self) -> None:
        assert _parse_field_value(models.JSONField(), {"key": "val"}) == {"key": "val"}

    def test_none_passthrough(self) -> None:
        assert _parse_field_value(models.IntegerField(), None) is None


# ---------------------------------------------------------------------------
# _parse_field_value - DateTime Edge Cases
# ---------------------------------------------------------------------------


def test_parse_field_value_datetime_negative_year() -> None:
    field = models.DateTimeField()
    result = viernulvier._parse_field_value(field, "-2024-01-01T12:00:00Z")
    assert result is not None
    assert result.year == 2024


def test_parse_field_value_datetime_year_zero() -> None:
    field = models.DateTimeField()
    result = viernulvier._parse_field_value(field, "0000-12-25T23:59:59Z")
    assert result is not None
    assert result.year == 1970
    assert result.month == 12


def test_parse_field_value_datefield_string() -> None:
    field = models.DateField()
    result = viernulvier._parse_field_value(field, "2024-06-15")
    assert result is not None
    assert result.year == 2024
    assert result.month == 6
    assert result.day == 15


def test_parse_field_value_none_returns_none() -> None:
    field = models.DateTimeField()
    assert viernulvier._parse_field_value(field, None) is None


def test_parse_field_value_urlfield_branch(monkeypatch) -> None:
    """URLField branch is reachable only by bypassing the CharField check,
    since URLField inherits CharField and would otherwise be caught first."""

    url_field = models.URLField()
    url_field.name = "url"

    original_isinstance = builtins.isinstance

    def patched_isinstance(obj, classes):
        if obj is url_field and classes == (models.TextField, models.CharField):
            return False
        return original_isinstance(obj, classes)

    monkeypatch.setattr(builtins, "isinstance", patched_isinstance)

    assert viernulvier._parse_field_value(url_field, "https://example.com") == "https://example.com"
    assert viernulvier._parse_field_value(url_field, "not-a-url") == ""

