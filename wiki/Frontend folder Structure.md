# Frontend Folder Structure

## Overview

The frontend is organized around reusable UI building blocks, feature-specific services, and route-level pages. The structure currently looks like this:

```text
frontend/
├── public/
│   └── fonts/
├── src/
│   ├── __tests__/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── theme/
│   ├── components/
│   │   ├── BlogGrid.tsx
│   │   ├── BlogGridCard.tsx
│   │   ├── BlogList.tsx
│   │   ├── BlogListCard.tsx
│   │   ├── BlogView.tsx
│   │   ├── CollectionPageLayout.tsx
│   │   ├── FloatingAlert.tsx
│   │   ├── Footer.tsx
│   │   ├── GenericGrid.tsx
│   │   ├── GenericList.tsx
│   │   ├── ImageWithFallback.tsx
│   │   ├── LoadingSpinner.tsx
│   │   ├── Navbar.tsx
│   │   ├── Pagination.tsx
│   │   ├── ProductionGrid.tsx
│   │   ├── ProductionList.tsx
│   │   ├── ProductionView.tsx
│   │   ├── carousel/
│   │   ├── chips/
│   │   ├── entity/
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
│   │   ├── BlogDetailPage.tsx
│   │   ├── BlogsPage.tsx
│   │   ├── HomePage.tsx
│   │   ├── NotFoundPage.tsx
│   │   ├── ProductionDetailPage.tsx
│   │   ├── ProductionsPage.tsx
│   │   ├── SeriesDetailPage.tsx
│   │   └── SeriesPage.tsx
│   ├── services/
│   │   ├── Api.ts
│   │   ├── ApiErrorMapper.ts
│   │   ├── ApiParams.ts
│   │   ├── ApiTypes.ts
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
│   │   ├── muiPalette.ts
│   │   ├── styles.ts
│   │   └── tokens.ts
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

## Core Files

### `src/main.tsx`

Bootstraps the React app, imports global styles, and mounts `<App />`.

### `src/App.tsx`

Owns the top-level MUI `ThemeProvider` and theme mode persistence.

### `src/router.tsx`

Defines the route tree, shared layout, redirect aliases, and the 404 fallback.

### `src/i18n.ts`

Configures i18next and loads the English and Dutch translation bundles.

## Component Areas

### `src/components/`

Reusable UI components and shared layout primitives live here.

- `Navbar.tsx` and `Footer.tsx` provide the site shell.
- `CollectionPageLayout.tsx` standardizes collection pages with search, sort, sidebar, loading, error, empty, and pagination UI.
- `BlogView.tsx` and `ProductionView.tsx` switch between list and grid rendering based on layout and viewport.
- `searchbar/` contains the search input, search controls, and URL state hook.
- `series/`, `series_details/`, `production/`, and `productions/` hold feature-specific cards, headers, and detail-page helpers.
- `chips/`, `carousel/`, `entity/`, and `skeletons/` contain smaller presentational pieces.

### `src/pages/`

Each route maps to a page component.

- `HomePage.tsx` - landing page
- `ProductionsPage.tsx` - archive listing
- `ProductionDetailPage.tsx` - production detail view
- `SeriesPage.tsx` - series overview
- `SeriesDetailPage.tsx` - series detail view
- `BlogsPage.tsx` - blogs overview
- `BlogDetailPage.tsx` - blog detail view
- `NotFoundPage.tsx` - 404 page

### `src/services/`

API clients are grouped by domain rather than by technical layer.

- Shared transport helpers: `Api.ts`, `ApiErrorMapper.ts`, `ApiParams.ts`, `ApiTypes.ts`
- Feature folders: `blogs/`, `productions/`, `series/`, `media/`, `media_files/`, `locations/`, `pricing/`, `tags/`, `genres/`, `halls/`, `languages/`, `events/`, `spaces/`

### `src/theme/`

The design system is split into:

- `tokens.ts` for raw values
- `muiPalette.ts` for the MUI theme factory
- `styles.ts` for shared `sx` patterns

### `src/__tests__/`

The test tree mirrors the source tree so component, page, service, and theme tests stay easy to find.

## Practical Notes

- The canonical public route for the archive is `/archive`.
- `/productions` and `/media` remain as redirects for compatibility.
- Keep new code close to the feature folder it belongs to so imports stay manageable.
- Add or update tests in the matching `__tests__` subfolder when behavior changes.

## Configuration Files

Key frontend configuration files and their purpose:

- `package.json`: dependency and script management
- `vite.config.ts`: dev server and build behavior
- `tsconfig.json`: app compiler configuration
- `tsconfig.node.json`: tooling-side TypeScript config
- `tsconfig.jest.json`: test TypeScript config
- `eslint.config.cjs`: lint rules and plugin setup
- `jest.config.cjs`: test runtime and mapping config
- `.prettierrc.json`: formatting policy

## Resources

- [Vite Documentation](https://vite.dev/)
- [React Documentation](https://react.dev/)
- [TypeScript Documentation](https://www.typescriptlang.org/docs/)
- [Material UI Documentation](https://mui.com/)
- [React Router Documentation](https://reactrouter.com/)
