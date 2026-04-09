## Mockups (Figma)

[![Figma Design](https://img.shields.io/badge/Bekijk%20in-Figma-F24E1E?logo=figma)](https://www.figma.com/proto/NO5K1na6jzQBVNDxNWuFHu/selab?node-id=0-1&t=s3LbIfzwLgKREpvT-1)

## Overview

The frontend is built with modern React tooling and follows best practices for type safety, internationalization, and code quality:

```text
frontend/
├── src/
│   ├── components/      # Reusable UI components
│   ├── locales/         # i18n translation files
│   │   ├── en/          # English translations
│   │   └── nl/          # Dutch translations
│   ├── pages/           # Page-level components
│   ├── services/        # API calls ??
│   ├── theme/           # Centralized styling
│   ├── types/           # interfaces and types
│   ├── utils/           # Utility functions 
│   ├── router.tsx       # Route definitions
│   ├── i18n.ts          # i18next configuration
│   ├── main.tsx         # App entry point
│   └── App.tsx          # Root component
├── package.json         # Dependencies and scripts
├── vite.config.ts       # Vite bundler config
├── tsconfig.json        # TypeScript config
├── jest.config.cjs      # Jest test config
├── eslint.config.cjs    # ESLint flat config
└── .prettierrc.json     # Prettier formatting config
```

This structure ensures clear separation of concerns, easy navigation, and maintainability.

---

## Tech Stack

### Core

- **Vite** → Fast development server and build tool
- **React 19** → UI library with latest features
- **TypeScript** → Type safety and better DX

### UI & Styling

- **Material UI (MUI)** → Component library implementing Material Design
- **Emotion** → CSS-in-JS (MUI peer dependency)

---

## Styling System (Tokens + Shared Styles)

To keep styling consistent and easy to maintain, we use a layered approach:

### 1. Tokens for shared visual values

Use design tokens as the single source of truth for values like:

- colors
- spacing
- typography
- border radius
- shadows
- transitions

**File:** `frontend/src/theme/tokens.ts`

If a style value should be reused across components, add it to tokens instead of hardcoding it.

### 2. Theme for MUI integration

MUI theme creation is centralized and built from tokens.

**File:** `frontend/src/theme/muiPalette.ts`

`createAppTheme` is used at the app root so light/dark mode and component defaults stay consistent.

### 3. Shared style patterns for repeated UI

Common `sx` patterns live in a shared helper.

**File:** `frontend/src/theme/styles.ts`

Use shared patterns for repeated structures (e.g., navbar/footer/card/grid). Add new shared patterns here when multiple components need the same styling structure.

### 4. Component-local style helpers when behavior is component-specific

Keep style logic local when it depends on component context/state and is not broadly reusable.

**Example file:** `frontend/src/components/chips/genreAndTagChipStyles.ts`

### 5. Global CSS only for app-wide/page-wide rules

Global CSS is used for base styles, CSS variables, and layout rules that are not component-specific.

**File:** `frontend/src/index.css`

---

## Practical Rules

When adding or changing styles:

1. First check if a token already exists in `frontend/src/theme/tokens.ts`.
2. If the style pattern is reused, add/use `frontend/src/theme/styles.ts`.
3. If the style is specific to one component's behavior, keep it near that component.
4. Avoid hardcoded colors and repeated magic numbers in components where tokens can be used.
5. Keep `createAppTheme` as the single theme entry point in `frontend/src/App.tsx`.

### Routing

- **React Router v7** → Client-side routing with nested routes

### Internationalization

- **i18next** + **react-i18next** → English/Dutch translations

### Testing

- **Jest** → Test runner
- **React Testing Library** → Component testing utilities
- **jsdom** → Browser environment simulation

### Code Quality

- **ESLint** → Linting (flat config format)
- **Prettier** → Code formatting
- **TypeScript** → Static type checking

---

## Dependencies

### Production Dependencies (dependencies)

These are shipped to production and required at runtime:

```json
{
  "@emotion/react": "^11.11.4",
  "@emotion/styled": "^11.11.5",
  "@mui/icons-material": "^6.2.15",
  "@mui/material": "^6.2.15",
  "i18next": "^23.15.1",
  "react": "^19.0.0",
  "react-dom": "^19.0.0",
  "react-i18next": "^15.4.0",
  "react-router-dom": "^7.1.3"
}
```

### Development Dependencies (devDependencies)

These are only used during development and testing:

```json
{
  "@testing-library/jest-dom": "^6.4.6",
  "@testing-library/react": "^16.0.1",
  "@testing-library/user-event": "^14.5.2",
  "@types/jest": "^29.5.14",
  "@types/react": "^19.0.3",
  "@types/react-dom": "^19.0.3",
  "@typescript-eslint/eslint-plugin": "^8.56.0",
  "@typescript-eslint/parser": "^8.56.0",
  "@vitejs/plugin-react": "^4.3.4",
  "eslint": "^9.7.0",
  "eslint-config-prettier": "^9.1.0",
  "eslint-plugin-prettier": "^5.2.1",
  "eslint-plugin-react": "^7.35.0",
  "eslint-plugin-react-hooks": "^5.1.0",
  "eslint-plugin-react-refresh": "^0.4.12",
  "globals": "^15.9.0",
  "identity-obj-proxy": "^3.0.0",
  "jest": "^29.7.0",
  "jest-environment-jsdom": "^29.7.0",
  "jsdom": "^24.1.3",
  "prettier": "^3.3.3",
  "ts-jest": "^29.2.5",
  "typescript": "^5.6.3",
  "vite": "^7.3.1"
}
```

---

## Installation

### Prerequisites

1. **Node.js LTS** (v20 or later)
2. **npm** (comes with Node.js)

### Steps

From the repository root:

```bash
cd frontend
npm install
```

This installs all dependencies (both production and development).

---

## Available Scripts

### Development

Start the dev server with hot reload:

```bash
npm run dev
```

Runs on `http://localhost:5173` by default.

### Build

Create an optimized production build:

```bash
npm run build
```

Output goes to `frontend/dist/`.

### Preview

Preview the production build locally:

```bash
npm run preview
```

### Testing

Run all tests:

```bash
npm test
```

Run tests in watch mode:

```bash
npm run test:watch
```

### Linting

Check for code quality issues:

```bash
npm run lint
```

### Formatting

Format all files with Prettier:

```bash
npm run format
```

---

## Routing

Routes are defined in `src/router.tsx`:

| Route                | Component              | Description          |
|----------------------|------------------------|----------------------|
| `/`                  | `HomePage`             | Landing page         |
| `/events`            | `EventsPage`           | Events list          |
| `/events/:id`        | `EventDetailPage`      | Single event details |
| `/productions`       | `ProductionsPage`      | Productions list     |
| `/productions/:id`   | `ProductionDetailPage` | Single production    |

### Adding a New Route

1. Create a page component in `src/pages/`:

```tsx
// src/pages/MyNewPage.tsx
import { Container, Typography } from '@mui/material'

const MyNewPage = () => {
  return (
    <Container>
      <Typography variant="h4">My New Page</Typography>
    </Container>
  )
}

export default MyNewPage
```

2. Import it in `src/router.tsx`:

```tsx
import MyNewPage from './pages/MyNewPage'
```

3. Add a `<Route>`:

```tsx
<Route path="/my-new-page" element={<MyNewPage />} />
```

4. Optionally add a nav link in `src/components/Navbar.tsx`:

```tsx
<Button color="inherit" component={RouterLink} to="/my-new-page">
  {t('nav.myNewPage')}
</Button>
```

---

## Internationalization (i18n)

Language switching is integrated in the navbar (EN/NL buttons).

### Translation Files

- `src/locales/en/translation.json` → English
- `src/locales/nl/translation.json` → Dutch

### Structure

```json
{
  "title": "...",
  "subtitle": "...",
  "nav": {
    "home": "...",
    "events": "...",
    "productions": "..."
  },
  "events": {
    "title": "...",
    "listPlaceholder": "...",
    "detailTitle": "...",
    "detailPlaceholder": "...",
    "backToEvents": "..."
  },
  "productions": { ... }
}
```

### Using Translations in Components

```tsx
import { useTranslation } from 'react-i18next'

const MyComponent = () => {
  const { t } = useTranslation()
  
  return <Typography>{t('nav.home')}</Typography>
}
```

### With Interpolation

```tsx
{t('events.detailPlaceholder', { id: '123' })}
```

In translation file:

```json
{
  "detailPlaceholder": "Event details for ID {{id}} will be displayed here."
}
```

---

## Testing

### Test Setup

- **Config**: `jest.config.cjs`
- **Setup file**: `src/setupTests.ts` (imports jest-dom matchers and polyfills)
- **Test location**: `src/__tests__/` or `*.test.tsx` files

### Running Tests

```bash
npm test
```

### Example Test

```tsx
import { render, screen } from '@testing-library/react'
import App from '../App'
import '../i18n'

describe('App', () => {
  it('renders navigation', () => {
    render(<App />)
    expect(screen.getByText('Archive')).toBeInTheDocument()
  })
})
```

---

## Linting & Formatting

### ESLint

Uses **flat config** format (`eslint.config.cjs`).

Run lint checks:

```bash
npm run lint
```

### Prettier

Config in `.prettierrc.json`:

```json
{
  "semi": false,
  "singleQuote": true,
  "trailingComma": "all",
  "printWidth": 100
}
```

Format all files:

```bash
npm run format
```

---

## CI/CD

A GitHub Actions workflow runs on every push/PR to `main` or `develop`:

**File**: `.github/workflows/frontend.yml`

**Steps**:

1. Install dependencies
2. Run linting
3. Run tests
4. Build the project

Check the **Actions** tab in GitHub to see build status.

---

## Adding a New Package

### 1. Install the package

```bash
cd frontend
npm install <package-name>
```

For development-only packages:

```bash
npm install --save-dev <package-name>
```

### 2. Verify it's added to package.json

Check `dependencies` or `devDependencies` section.

### 3. Commit the changes

```bash
git add package.json package-lock.json
git commit -m "Add <package-name>"
```

### Guidelines

- **Production dependency** → needed at runtime (e.g., axios, date-fns)
- **Dev dependency** → only for development/testing (e.g., @types/*, testing-library)

---

## Security

### Checking for Vulnerabilities

```bash
npm audit --omit=dev
```

This checks **production dependencies only** and ignores dev-only issues.

### Current Status

Dev-only advisories may remain due to ESLint/Jest transitive dependencies. These do not affect production builds.

---

## Troubleshooting

### Port already in use

If port 5173 is taken, Vite will auto-increment. Or specify a custom port:

```bash
npm run dev -- --port 3000
```

### Tests fail with "TextEncoder is not defined"

Already fixed in `src/setupTests.ts` with a polyfill.

### ESLint errors after upgrading

Check `eslint.config.cjs` and ensure plugin versions match ESLint version.

### TypeScript errors with imports

Enable `esModuleInterop` in `tsconfig.json` (already configured).

---

## Best Practices

1. **Component structure**: Keep pages in `src/pages/`, reusable components in `src/components/`
2. **Translations**: Always use `t()` for user-facing text, never hardcode strings
3. **Types**: Define prop types with TypeScript interfaces
4. **Testing**: Write tests for critical user flows
5. **Commits**: Run `npm run format` before committing

---

## Resources

- [Vite Documentation](https://vite.dev/)
- [React 19 Docs](https://react.dev/)
- [Material UI](https://mui.com/)
- [React Router v7](https://reactrouter.com/)
- [react-i18next](https://react.i18next.com/)
- [Jest](https://jestjs.io/)
- [React Testing Library](https://testing-library.com/react)
