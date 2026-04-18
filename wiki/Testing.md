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

#### 1) Running Tests

Commands below assume you are in `frontend/`.

```bash
# Install dependencies (first time or after package changes)
npm ci

# Full test suite
npm test

# Focused run (single file or pattern)
npm test -- --testPathPatterns "Navbar.test.tsx"

# Run sequentially (useful for debugging)
npm test -- --runInBand
```

#### 2) Linting and Formatting

```bash
# Lint (must pass in CI)
npm run lint

# Auto-fix lint issues
npm run lint:fix

# Check formatting without writing
npm run format:check

# Auto-fix formatting
npm run format:fix
```

#### 3) Test Folder Structure

Tests live in `frontend/src/__tests__/` and mirror the component, page, service, and theme structure.

```text
src/
  __tests__/
      components/
      pages/
      services/
      theme/
```

#### 4) What to Test Per Layer

- **Components** — render output, interaction behavior, aria attributes, and i18n label correctness.
- **Pages** — route rendering, fetch orchestration, and loading/error/empty state transitions.
- **Services** — request paths, query parameters, and error propagation.
- **Theme helpers** — token mapping, palette creation, and shared style objects.

Use `data-testid` attributes for stable element selection; prefer them over CSS class names or positional queries.

#### 5) Testing Guidelines

- Use `MemoryRouter` when testing components that use `useLocation` or `Link`.
- Use `ThemeProvider` when the component depends on MUI theme values or breakpoints.
- Use `I18nextProvider` or the shared test i18n instance when asserting translations.
- Use `fireEvent` for simple interactions; use `userEvent` when pointer/keyboard fidelity matters.
- Avoid asserting on CSS class names or MUI internals — assert on accessible attributes (`aria-label`, `aria-current`) and visible text.
- Set the i18n language in `beforeEach` so translation assertions are deterministic.
- Do not add tests for browser APIs (e.g. `ClickAwayListener` pointer events) that JSDOM cannot reliably simulate.

---

## Linting and Formatting

We use [Ruff](https://docs.astral.sh/ruff/) for linting, formatting and import sorting the backend Python codebase. It replaces tools like Flake8, isort and Black with a single, significantly faster alternative.

### Running Locally

Commands below assume you are in `backend/` and your virtual environment is active.

```bash
# Check for lint errors
ruff check .

# Auto-fix lint errors where possible
ruff check . --fix

# Check formatting
ruff format --check .

# Apply formatting
ruff format .
```

Run both `ruff check` and `ruff format` before pushing to avoid CI failures on pull requests.

### CI Behaviour

Ruff is integrated into the CI pipeline with two distinct jobs that run under different conditions.

#### Auto-fix (on push)

When code is pushed directly to `main`, `dev`, or `backend`, CI automatically runs Ruff with `--fix` and commits any resulting changes back to the branch. This means minor fixable issues are resolved without any manual intervention.

This job is skipped if the push was already made by `github-actions[bot]`, preventing commit loops.

#### Lint check (on pull request)

When a pull request is opened against `main`, `dev`, or `backend`, CI runs Ruff in check-only mode — no fixes are applied and no commits are made. If any lint or formatting issues are found, the job fails and the PR cannot be merged until they are resolved locally.

This ensures that all code merged via PRs is clean before it lands.

#### Summary

| Event | Job | Behaviour |
| --- | --- | --- |
| Push to `main` / `dev` / `backend` | `autofix` | Runs `ruff check --fix` + `ruff format`, commits changes if any |
| Pull request to `main` / `dev` / `backend` | `lint` | Runs `ruff check` + `ruff format --check`, fails on any issue |
