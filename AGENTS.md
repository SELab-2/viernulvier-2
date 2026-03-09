# AGENTS.md

Guidance for human and AI contributors working in this repository.

## Scope

This file applies to the full repository unless a deeper `AGENTS.md` is added in a subdirectory.

## Project Layout

- `backend/`: Django + DRF API, domain apps under `backend/apps/`, tests under `backend/tests/`.
- `frontend/`: React + TypeScript + Vite SPA, tests in `frontend/src/__tests__/`.
- `infrastructure/`: Docker Compose and nginx/certbot deployment assets.
- `wiki/`: Project documentation pages and team knowledge base.

## Core Rules

- Keep changes focused and minimal to the requested task.
- Do not rename/move files unless needed for the task.
- Preserve existing patterns and style in each folder.
- Never commit secrets, tokens, or private keys.
- Update docs when behavior, architecture, operational runbooks, or developer workflow changes.
- When implementation changes affect documented behavior, update relevant pages in `wiki/` in the same change set.

## Backend (Django)

- Follow existing app boundaries in `backend/apps/*`.
- Prefer serializers + viewsets/views consistent with neighboring code.
- Keep schema/openapi declarations aligned with endpoint changes.
- Add or update tests in `backend/tests/` for behavior changes.

### Backend Validation

From `backend/`:

```bash
pytest
```

If needed for quick checks, run targeted tests:

```bash
pytest tests/<area>
```

## Frontend (React + TS)

- Keep components typed; avoid introducing `any` without strong reason.
- Reuse existing routing/i18n/testing patterns in `frontend/src/`.
- Prefer small, composable components and predictable state changes.
- Add or update tests for changed UI logic.

### Frontend Validation

From `frontend/`:

```bash
npm test
npm run build
```

## Infrastructure

- Keep environment-specific changes aligned across relevant compose files.
- Avoid hardcoding environment-specific credentials or host-specific paths.
- Validate nginx and compose edits for both syntax and consistency.

## Wiki / Documentation

- Treat `wiki/` as the canonical source for project process and operational docs.
- Keep docs close to code changes: if an endpoint, workflow, or deployment step changes, update matching wiki pages.
- Prefer updating existing pages over creating duplicates for the same topic.

## Pull Request / Change Checklist

- Code is formatted and consistent with local style.
- Relevant tests are added/updated and passing.
- No unrelated files were changed.
- Documentation, wiki pages, and config examples are updated if needed.

## Notes for AI Agents

- Read nearby files before editing to match conventions.
- Prefer precise edits over broad refactors.
- Explain assumptions in PR/commit messages when context is uncertain.
- If a change could be breaking, call it out explicitly and suggest a migration path.
