# Frontend setup

## Overview

This project uses:
- Vite + React 19 + TypeScript
- React-i18next (English/Dutch)
- Material UI
- Jest + React Testing Library
- ESLint (flat config) + Prettier

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
- src/App.tsx: sample UI and language switch
- src/i18n.ts: i18next configuration
- src/locales/en/translation.json: English strings
- src/locales/nl/translation.json: Dutch strings

## i18n notes

Add or edit translations in the JSON files under src/locales. Language switch is controlled via i18next and can be wired into a navbar or user settings later.

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
