"""Value normalization and field coercion helpers for Viernulvier payloads."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
import logging
import re
from typing import Any

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models
from django.utils.dateparse import parse_date, parse_datetime

from .viernulvier_constants import _EMPTY_URL_VALUES

logger = logging.getLogger("apps.imports.scrapers.viernulvier")
_url_validator = URLValidator()


def normalize_url(value: Any) -> str:
    """Return the value only if it is a valid URL, otherwise return empty string."""
    if value is None:
        return ""
    s = str(value).strip()
    if s.lower() in _EMPTY_URL_VALUES:
        return ""
    try:
        _url_validator(s)
        return s
    except ValidationError:
        return ""


def normalize_performer_type(value: Any) -> str:
    """Map API performer_type values to internal enum values."""
    mapping = {"person": "solo"}
    s = str(value).strip().lower() if value else ""
    return mapping.get(s, s)


def clean_string(value: Any) -> str:
    """Strip whitespace and remove non-printable control characters."""
    if value is None:
        return ""
    s = str(value).strip()
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", s)


def clean_vendor_id(value: Any) -> str | None:
    """Return None for empty or html-like vendor IDs; otherwise return string value."""
    if value is None:
        return None
    s = str(value).strip()
    if not s or s.startswith("<i"):
        return None
    return s


def nee_ja_to_bool(value: Any) -> bool:
    """Coerce Dutch/English truthy strings and integers to Python bool."""
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"ja", "true", "1", "yes"}:
            return True
        if v in {"nee", "false", "0", "", "no"}:
            return False
    return bool(value)


def camel_to_snake(value: str) -> str:
    """Convert camelCase API key to snake_case model field name."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", value).lower()


def _parse_decimal(model_field: models.Field, value: Any) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        logger.warning("Cannot convert '%s' to Decimal for field '%s'", value, model_field.name)
        return None


def _parse_int(model_field: models.Field, value: Any) -> int | None:
    try:
        return int(value)
    except (ValueError, TypeError):
        logger.warning("Cannot convert '%s' to int for field '%s'", value, model_field.name)
        return None


def _parse_float(model_field: models.Field, value: Any) -> float | None:
    try:
        return float(value)
    except (ValueError, TypeError):
        logger.warning("Cannot convert '%s' to float for field '%s'", value, model_field.name)
        return None


def _parse_datetime_value(model_field: models.Field, value: Any) -> Any:
    if not isinstance(value, str):
        return value
    candidate = value.removeprefix("-")
    if candidate[:4] == "0000":
        candidate = "1970" + candidate[4:]
    parsed = parse_datetime(candidate)
    if parsed is None:
        logger.debug("Cannot parse datetime '%s' for field '%s'", value, model_field.name)
    return parsed


def _parse_non_text_field(model_field: models.Field, value: Any) -> Any:
    parsed_value: Any = value
    if isinstance(model_field, models.URLField):
        parsed_value = normalize_url(value)
    elif isinstance(model_field, models.BooleanField):
        parsed_value = nee_ja_to_bool(value)
    elif isinstance(model_field, models.DecimalField):
        parsed_value = _parse_decimal(model_field, value)
    elif isinstance(model_field, models.IntegerField):
        parsed_value = _parse_int(model_field, value)
    elif isinstance(model_field, models.FloatField):
        parsed_value = _parse_float(model_field, value)
    elif isinstance(model_field, models.DateTimeField):
        parsed_value = _parse_datetime_value(model_field, value)
    elif isinstance(model_field, models.DateField) and isinstance(value, str):
        parsed_value = parse_date(value)
    return parsed_value


def parse_field_value(model_field: models.Field, value: Any) -> Any:
    """Coerce an API value to the correct Python type for the given model field."""
    if value is None:
        return None
    if isinstance(model_field, (models.TextField, models.CharField)):
        cleaned = clean_string(value)
        max_len = getattr(model_field, "max_length", None)
        if max_len and len(cleaned) > max_len:
            logger.debug("Field '%s' truncated: %d -> %d chars", model_field.name, len(cleaned), max_len)
            cleaned = cleaned[:max_len]
        return cleaned
    return _parse_non_text_field(model_field, value)

