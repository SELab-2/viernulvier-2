"""Compatibility facade for the legacy CSV importer.

The implementation is split into focused modules:
- `legacy_csv_constants.py`
- `legacy_csv_normalize.py`
- `legacy_csv_io.py`
- `legacy_csv_relations.py`
- `legacy_csv_handlers.py`
- `legacy_csv_sync.py`
"""

from . import legacy_csv_constants as _constants
from . import legacy_csv_handlers as _handlers
from . import legacy_csv_io as _io
from . import legacy_csv_normalize as _normalize
from . import legacy_csv_relations as _relations
from . import legacy_csv_sync as _sync

PACKAGE_ROOT = _constants.PACKAGE_ROOT
LEGACY_PRODUCTION_ORIGINAL_CSV = _constants.LEGACY_PRODUCTION_ORIGINAL_CSV
LEGACY_PRODUCTION_CSV = _constants.LEGACY_PRODUCTION_CSV
LEGACY_EVENT_CSV = _constants.LEGACY_EVENT_CSV
LEGACY_LANGUAGE_CODE = _constants.LEGACY_LANGUAGE_CODE
LEGACY_LANGUAGE_NAME = _constants.LEGACY_LANGUAGE_NAME
LEGACY_LANGUAGE_ACTIVE = _constants.LEGACY_LANGUAGE_ACTIVE
LEGACY_PRODUCTION_FIELDNAMES = _constants.LEGACY_PRODUCTION_FIELDNAMES
LEGACY_PRODUCTION_HEADERS = _constants.LEGACY_PRODUCTION_HEADERS
LEGACY_EVENT_HEADERS = _constants.LEGACY_EVENT_HEADERS

_normalise_cell = _normalize._normalise_cell
_normalise_multiline_text = _normalize._normalise_multiline_text
_split_genres = _normalize._split_genres
_parse_legacy_datetime = _normalize._parse_legacy_datetime
_event_external_id = _normalize._event_external_id

_iter_csv_rows = _io._iter_csv_rows
_count_csv_rows = _io._count_csv_rows
detect_legacy_csv_kind = _io.detect_legacy_csv_kind

_ensure_language = _relations._ensure_language
_ensure_genre = _relations._ensure_genre
_sync_production_genres = _relations._sync_production_genres
_hall_for_name = _relations._hall_for_name

_import_legacy_production_row = _handlers._import_legacy_production_row
_import_legacy_event_row = _handlers._import_legacy_event_row

_import_legacy_csv_rows = _sync._import_legacy_csv_rows
_import_legacy_csv_file = _sync._import_legacy_csv_file
import_legacy_csv_file = _sync.import_legacy_csv_file
import_bundled_legacy_csv_files = _sync.import_bundled_legacy_csv_files

__all__ = ["detect_legacy_csv_kind", "import_bundled_legacy_csv_files", "import_legacy_csv_file"]
