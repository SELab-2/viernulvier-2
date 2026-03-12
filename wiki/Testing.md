## Testing

This section documents the testing approach for both backend and frontend.

### Backend

#### 1) Running Tests

Commands below assume you are in `backend/` and your virtual environment is active.

```bash
# Full suite
pytest

# One app
pytest tests/languages

# One test file
pytest tests/languages/test_language_views.py

# One test class
pytest tests/languages/test_language_views.py::TestLanguageListView

# One test case
pytest tests/languages/test_language_views.py::TestLanguageListView::test_returns_200
```

#### 2) Coverage Workflow

```bash
# Run tests with coverage
coverage run -m pytest

# Human-readable report with missing lines
coverage report -m

# Optional HTML report
coverage html
```

Goal: keep coverage high and avoid introducing uncovered logic when adding features.

#### 3) Test Folder Structure

Tests live in `backend/tests/` and mirror the app structure.

```text
tests/
   <app_name>/
      test_<app>_admin.py
      test_<app>_models.py
      test_<app>_serializers.py
      test_<app>_views.py
```

Example:
- App: `languages`
- Tests: `tests/languages/test_language_admin.py`, `tests/languages/test_language_models.py`, ...

#### 4) What to Test Per Layer

`schemas.py` is documentation-only and generally does not need dedicated tests.

- **Models**
   - Field constraints (`null/blank/default/choices/unique`)
   - `clean()` and `save()` behavior
   - DB constraints and cascade behavior
   - `__str__` output and model helpers

- **Admin**
   - Model registration
   - `list_display`, `list_filter`, `search_fields`, `ordering`
   - Inlines, readonly fields, custom display helpers
   - Custom actions and permission behavior (if overridden)

- **Serializers**
   - Required/optional fields
   - Validation rules + error messages
   - Output shape and computed fields

- **Views / API**
   - Auth + permissions (`401/403` behavior)
   - CRUD success and failure paths
   - Pagination/filtering/ordering
   - Not found / invalid payload handling
   - Query efficiency where relevant (e.g. no N+1 regressions)

#### 5) Factories

Shared factories live in `tests/factories/`.

Use factories by default instead of manual object creation to keep tests:
- concise,
- consistent,
- reusable across suites.

When adding a model, add or extend its factory in `tests/factories/<app>.py`.

#### 6) Adding a New App (Testing Checklist)

1. Create `tests/<app>/`.
2. Add layer-based test files (`admin`, `models`, `serializers`, `views`).
3. Add/update `tests/factories/<app>.py`.
4. Add tests for cross-cutting behavior if introduced (auth, permissions, throttling).
5. Run:

```bash
pytest tests/<app>
coverage run -m pytest tests/<app>
coverage report -m
```

### Frontend

TODO