# Frontend

## Mockups (Figma)

[![Figma Design](https://img.shields.io/badge/Bekijk%20in-Figma-F24E1E?logo=figma)](https://www.figma.com/proto/NO5K1na6jzQBVNDxNWuFHu/selab?node-id=0-1&t=s3LbIfzwLgKREpvT-1)

## Overview

The frontend is a **Vite** + **React** + **TypeScript** single-page application. It uses **Material UI** for components, **i18next** for translations, and **React Router v7** for client-side navigation.

At app startup, `frontend/src/App.tsx` restores the persisted theme mode from `localStorage`, creates the theme with `createAppTheme`, applies `CssBaseline`, and renders the router.

## Current Structure

```text
frontend/
├── public/
│   └── fonts/
├── src/
│   ├── __tests__/
│   ├── components/
|   |   ├── blogs/
│   │   ├── carousel/
│   │   ├── chips/
│   │   ├── entity/
|   |   ├── extra/
│   │   ├── production/
│   │   ├── productions/
│   │   ├── searchbar/
│   │   ├── series/
│   │   ├── series_details/
│   │   └── skeletons/
│   ├── locales/
│   │   ├── en/
│   │   └── nl/
│   ├── pages/
│   ├── services/
│   │   ├── blogs/
│   │   ├── events/
│   │   ├── genres/
│   │   ├── halls/
│   │   ├── languages/
│   │   ├── locations/
│   │   ├── media/
│   │   ├── media_files/
│   │   ├── pricing/
│   │   ├── productions/
│   │   ├── spaces/
│   │   └── tags/
│   ├── theme/
│   ├── types/
│   ├── utils/
│   ├── App.tsx
│   ├── i18n.ts
│   ├── index.css
│   ├── main.tsx
│   └── router.tsx
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tsconfig.node.json
├── tsconfig.jest.json
├── jest.config.cjs
└── eslint.config.cjs
```

## Tech Stack

### Core

- **Vite** for dev/build tooling
- **React 19** for UI composition
- **TypeScript** for type safety

### UI and Styling

- **Material UI** (`@mui/material`, `@mui/icons-material`, `@mui/system`)
- **Emotion** (`@emotion/react`, `@emotion/styled`)

### Routing and i18n

- **react-router-dom v7**
- **i18next** + **react-i18next**

### Data and Utility Libraries

- **axios** for API requests
- **dompurify** for safe HTML rendering
- **embla-carousel-react** + **embla-carousel-wheel-gestures** for carousel interactions

## Styling System

Styling is intentionally split into layers:

1. `frontend/src/theme/tokens.ts` defines shared values (colors, spacing, typography, shadows, breakpoints).
2. `frontend/src/theme/muiPalette.ts` converts tokens into light/dark MUI themes.
3. `frontend/src/theme/styles.ts` contains shared `sx` recipes for common UI patterns.
4. `frontend/src/index.css` provides global CSS variables, font-face declarations, and page-level base rules.

The current design system uses **ABC Monument Grotesk** from `public/fonts/`.

## Routing

Routes are defined in `frontend/src/router.tsx`.

The SPA uses a language segment as the first URL part (`/nl/...` or `/en/...`).
The active UI language is derived from that segment.
Unprefixed URLs are redirected to the current/default language path.
Within that segment, Dutch routes use translated slugs where available (for example `/nl/archief` and `/nl/reeksen`).

| Route | Component | Notes |
| --- | --- | --- |
| `/:lang` | `HomePage` | Language-aware landing page (`lang` is `nl` or `en`) |
| `/:lang/archive` (EN), `/:lang/archief` (NL) | `ProductionsPage` | Canonical archive listing route per language |
| `/:lang/productions` (EN), `/:lang/producties` (NL) | redirect to archive route | Compatibility alias |
| `/:lang/productions/:id` (EN), `/:lang/producties/:id` (NL) | `ProductionDetailPage` | Production detail page |
| `/:lang/series` (EN), `/:lang/reeksen` (NL) | `SeriesPage` | Series overview |
| `/:lang/series/:id` (EN), `/:lang/reeksen/:id` (NL) | `SeriesDetailPage` | Series detail page |
| `/:lang/blogs` | `BlogsPage` | Stories/blog listing |
| `/:lang/blogs/:id` | `BlogDetailPage` | Story detail page |
| `/:lang/media` | redirect to `/:lang/archive` | Temporary alias |
| `/:lang/media/:id` | redirect to `/:lang/archive` | Temporary alias |
| `/:lang/*` | `NotFoundPage` | 404 fallback |
| `/` and unprefixed paths | redirect to localized path | Keeps old links working |

The router also scrolls to top on route changes and renders shared `Navbar` + `Footer` around page content.

## Data Access

Frontend API logic is grouped by feature under `frontend/src/services/`.

- `Api.ts` and `ApiTypes.ts` define the Axios client and shared error shape.
- `ApiParams.ts` centralizes list query param formatting.
- Domain modules (blogs, productions, media, locations, pricing, tags, etc.) keep request logic close to each feature.

## Installation

### Prerequisites

1. **Node.js LTS** (v20+ recommended)
2. **npm**

### Steps

From the repository root:

```bash
cd frontend
npm install
```

If you need a fully clean install (for CI parity), use:

```bash
npm ci
```

## Available Scripts

### Development

```bash
npm run dev
```

Runs Vite dev server (default `http://localhost:5173`).

### Build

```bash
npm run build
```

Type-checks and builds production assets into `frontend/dist/`.

### Preview

```bash
npm run preview
```

Preview the production build locally.

### Testing

```bash
npm test
npm run test:watch
```

### Linting and Formatting

```bash
npm run lint
npm run lint:fix
npm run format:check
npm run format:fix
```

## Testing

Frontend tests run with **Jest** + **jsdom** + **React Testing Library**.

- Main config: `frontend/jest.config.cjs`
- Setup file: `frontend/src/setupTests.ts`
- Tests: `frontend/src/__tests__/`

Most component tests wrap with `MemoryRouter`, `ThemeProvider`, and i18n context where required.

## Configuration Files

- `package.json`: dependencies and scripts
- `vite.config.ts`: Vite plugins/build configuration
- `tsconfig.json`: app TypeScript config
- `tsconfig.node.json`: TS config for tooling-side files
- `tsconfig.jest.json`: TS config for tests
- `eslint.config.cjs`: ESLint flat config
- `jest.config.cjs`: Jest test config
- `.prettierrc.json`: Prettier formatting rules

## Adding a New Package

### Install

```bash
cd frontend
npm install <package-name>
```

For dev-only packages:

```bash
npm install --save-dev <package-name>
```

### Verify and Commit

1. Confirm it is in `dependencies` or `devDependencies`.
2. Commit `package.json` and lockfile changes.

Guideline:

- runtime package -> `dependencies`
- tooling/test package -> `devDependencies`

## Security

### Dependency Audit

```bash
npm audit --omit=dev
```

This focuses on production dependency risk.

### Frontend Security Practices in This Repo

- API traffic is centralized via `Api.ts`
- HTML sanitization uses `dompurify`
- Secrets should remain in environment variables and never be committed

## HTML Support in Text Sections

All text sections in the frontend (descriptions, excerpts, teaser text, etc.) support **safe HTML rendering** via the `HtmlText` component.

### How It Works

- The `HtmlText` component (`frontend/src/components/HtmlText.tsx`) wraps the `SanitizeHtml` utility to safely render HTML.
- All HTML is sanitized using **DOMPurify** to prevent XSS attacks.
- Dangerous attributes (`on*`, `script`, `style`, etc.) are stripped.
- Images are automatically constrained to responsive sizing (`max-width: 100%`, `height: auto`).
- If content is empty, an optional fallback message is displayed.

### Components Using HTML Rendering

The following components now support HTML:

| Component | Field | Notes |
| --- | --- | --- |
| `BlogGridCard` | `excerpt` | Blog excerpt displayed in grid layout |
| `BlogListCard` | `excerpt` | Blog excerpt displayed in list layout |
| `SeriesGridCard` | `description` | Series description in grid layout |
| `SeriesListCard` | `description` | Series description in list layout |
| `SeriesHeader` | `description` | Series description on detail page |
| `Description` (production) | `teaser`, `description` | Production teaser and full description |

## Troubleshooting

### Dev Server Port Conflict

```bash
npm run dev -- --port 3000
```

### Test Environment Errors (browser APIs in Jest)

Check `frontend/src/setupTests.ts` for polyfills/mocks (`TextEncoder`, `ResizeObserver`, `matchMedia`, etc.).

### ESLint Issues After Dependency Updates

Run:

```bash
npm run lint
```

Then verify plugin compatibility in `eslint.config.cjs`.

### Build or TS Resolution Errors

Run:

```bash
npm run build
```

And verify `tsconfig*.json` consistency.

## Resources

- [Vite Documentation](https://vite.dev/)
- [React Docs](https://react.dev/)
- [Material UI](https://mui.com/)
- [React Router](https://reactrouter.com/)
- [react-i18next](https://react.i18next.com/)
- [Jest](https://jestjs.io/)
- [React Testing Library](https://testing-library.com/react)
