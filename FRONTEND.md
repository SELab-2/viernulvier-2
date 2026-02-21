# Frontend setup

## Overview

This project uses:
- Vite + React 19 + TypeScript
- React Router v7
- React-i18next (English/Dutch)
- Material UI
- Jest + React Testing Library
- ESLint (flat config) + Prettier
- GitHub Actions CI

## Prerequisites

- Node.js LTS installed
- npm available in your terminal

## Install

From the repo root:

```
cd frontend
npm install
```

## Common commands

Run the dev server:

```
npm run dev
```

Create a production build:

```
npm run build
```

Preview the production build locally:

```
npm run preview
```

Run unit tests:

```
npm test
```

Run linting:

```
npm run lint
```

Format files:

```
npm run format
```

## Project layout

- src/main.tsx: app entry point, theme setup, and i18n init
- src/App.tsx: root component (renders Router)
- src/router.tsx: route definitions and layout
- src/components/Navbar.tsx: navigation bar with language switcher
- src/pages/: page components for each route
- src/i18n.ts: i18next configuration
- src/locales/en/translation.json: English strings
- src/locales/nl/translation.json: Dutch strings

## Routing

Routes are defined in src/router.tsx:
- `/` → Home page
- `/events` → Events list
- `/events/:id` → Event detail
- `/productions` → Productions list

To add a new route:
1. Create a page component in src/pages/
2. Import it in src/router.tsx
3. Add a `<Route>` entry
4. Optionally add a navigation link in src/components/Navbar.tsx

## i18n notes

Add or edit translations in the JSON files under src/locales. Language switch is controlled via i18next and can be wired into a navbar or user settings later.


## CI/CD

A GitHub Actions workflow (`.github/workflows/frontend.yml`) runs automatically on push/PR to `main` or `develop` branches:
1. Installs dependencies
2. Runs linting
3. Runs tests
4. Builds the project

Check the Actions tab in your GitHub repo to see build status.

## Testing notes

Jest uses jsdom. The config is in frontend/jest.config.cjs. If you add new tests, keep them under src/**/__tests__ or name them *.test.ts(x).

## Linting notes

ESLint uses the flat config in frontend/eslint.config.cjs. If you add new rules or plugins, update that file.

## Security checks

Use this to check production dependencies only:

```
npm audit --omit=dev
```

Dev-only advisories may remain because of tooling dependencies.
