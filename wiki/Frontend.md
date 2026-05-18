# Frontend

## Mockups (Figma)

[![Figma Design](https://img.shields.io/badge/Bekijk%20in-Figma-F24E1E?logo=figma)](https://www.figma.com/proto/NO5K1na6jzQBVNDxNWuFHu/selab?node-id=0-1&t=s3LbIfzwLgKREpvT-1)

## Overview

The frontend is a **Vite** + **React** + **TypeScript** application. It uses **Material UI** for components, **i18next** for translations, and **React Router v7** for client-side navigation.

At app startup, `bootstrap.tsx` renders an empty shell immediately for fast TTI, then `main.tsx` loads the full app during idle time. `App.tsx` restores the persisted theme mode from `localStorage`, creates the theme with `createAppTheme`, applies `CssBaseline`, and renders the router.

### Key Responsibilities

- Present localized site content and detail pages (productions, series, blogs, media files).
- Provide search, filters, pagination, and list/grid view toggles for collection pages.
- Centralize API access and error handling via shared services.
- Expose a comprehensive design system (`tokens`, `muiPalette`, `styles`) for consistent UI across light/dark modes.
- Handle language-aware routing with slug localization (EN `/archive` <-> NL `/archief`).
- Normalize API errors and display them via i18n translation.
- Support deferred loading (bootstrap shell -> idle main load) for performance.

## Tech Stack

### Core

- **Vite 8** for dev/build tooling with fast HMR
- **React 19** for UI composition
- **TypeScript 6** for type safety

### UI and Styling

- **Material UI** v9 (`@mui/material`, `@mui/icons-material`, `@mui/system`, `@mui/x-date-pickers`)
- **Emotion** v11 (`@emotion/react`, `@emotion/styled`) - MUI's CSS-in-JS foundation

### Routing and i18n

- **react-router-dom v7** for client-side routing with lazy code-splitting
- **i18next v26** + **react-i18next v17** for multi-language support (EN, NL)

### Data and Utility Libraries

- **axios v1** for API requests with custom interceptors
- **dompurify v3** for safe HTML sanitization
- **embla-carousel-react v8** + **embla-carousel-wheel-gestures v8** for carousels
- **react-pdf v10** for PDF viewing (mocked in tests)
- **dayjs v1** for date manipulation
- **pdfjs-dist v5** for PDF rendering
- **react-icons v5** for icon sets
- **simple-icons v16** for brand/social icons

## Styling System

Styling is intentionally split into **layers**:

### Layer 0: Global CSS (`src/index.css`)

- `@font-face` declarations (ABC Monument Grotesk: Regular, Medium, Bold, Light, Heavy)
- CSS custom properties for runtime theming
- Global CSS reset rules and base styles
- Utility classes

### Layer 1: Design Tokens (`src/theme/tokens.ts`)

**Source of truth** for all reusable values - exported as a single `tokens` constant:
- **Colors**: accent (`#8224E3` family: main/light/dark/contrastText), series (`#1976d2` family), light (background/surface/text/textMuted/border/divider/hover), dark (background/surface/text/textMuted/border/divider/hover), neutral (black/white/gray50–gray900), overlay (black05/white05/footerBorder/mediaNavDark/mediaNavLight/modalBackdropDark/modalBackdropLight), media (darkBackground/lightBackground), semantic (success/error/warning/info)
- **Spacing**: `xs` (4px) to `3xl` (64px) in string and numeric variants (0.5 through 8 in 8px units)
- **Typography**: fontFamily (`'ABC Monument Grotesk', Helvetica, Arial, sans-serif`), weights (light=300, regular=400, medium=500, bold=700, heavy=900), sizes (xs=12px through 5xl=48px), lineHeights (tight=1.2, normal=1.5, relaxed=1.7)
- **Shadows**: subtle, sm, md, lg, xl, navbar, mediaControl
- **Border radius**: none through full (`9999px`)
- **Transitions**: fast (150ms), base (200ms), slow (300ms), verySlow (500ms) - all `ease`
- **Z-index**: hide (-1), base (0), dropdown (1000), sticky (1050), modal (1060), overlay (1070), tooltip (1080)
- **Breakpoints**: xs (0px), sm (600px), md (960px), lg (1264px), xl (1920px)
- **Component-specific**: navbar (minHeight=64), card (borderRadius=4, padding=3, borderRadiusPx=16px, paddingPx=24px, gridCardWidthPx=350), chip (borderRadius=2, paddingY=1, paddingX=2)

### Layer 2: MUI Theme Factory (`src/theme/muiPalette.ts`)

Converts tokens into a Material UI `Theme` supporting light/dark modes via `createAppTheme(mode)`.

Includes:
- Palette generation (light: primary=black, dark: primary=white; accent=`#8224E3` family; background, text, divider, action)
- Typography scale mapping (h1–h6, body1, body2, button)
- Responsive breakpoint values (parsed from tokens)
- Shape: borderRadius=8, spacing: 8px base
- Shadows: 25 entries (mostly `'none'` except indices 1–4)
- Component-level overrides (MuiButton: no textTransform, md borderRadius; MuiCard: lg borderRadius + border; MuiPaper: no backgroundImage; MuiChip: md borderRadius)
- Custom accent color augmentation via `muiPalette.d.ts` (extends `Palette` + `PaletteOptions` with `accent` and `ButtonPropsColorOverrides`)

### Layer 3: Shared Styles (`src/theme/styles.ts`)

Reusable `sx` recipe factories:
- `createNavbarStyles()`: returns `{ activeLink, navLink, brandLink, brandLogo, brandArchiveText }`
- `createCommonStyles(theme)`: returns `{ cardBase, gridContainer, navbar, footer, responseImage, linkHover, chipBase, container, stack, textTruncate, centerContent }`
- `createHomePageStyles(theme)`: returns extensive mode-aware style map for the landing page (hero overlays, search input colors, button styles, stat bar colors, card overlays, etc.)

## Routing

Routes are defined in `frontend/src/router.tsx` with a **language-first strategy**:

### Routing Strategy

1. **Language-prefixed URLs**: all routes use `/:lang/...` where `lang` is `nl` or `en`
2. **Language inference**: paths like `/archive` are inferred to specific languages (`/archief` -> NL, `/archive` -> EN)
3. **Fallback resolution**: if no slug-specific inference, use browser i18n language or default (NL)
4. **Compatibility aliases**: old routes like `/productions`, `/producties` redirect to canonical localized equivalents
5. **Deferred loading**: `bootstrap.tsx` renders empty shell immediately; `main.tsx` loads full app via `requestIdleCallback`

### Route Components

- `ScrollToTop`: scrolls to top on every `pathname`/`search` change via `useLayoutEffect`
- `LanguagePathRedirect`: detects language from pathname, redirects to properly localized path
- `AliasDetailRedirect`: redirects alias slug detail paths to canonical localized routes
- `LocalizedLayout`: main layout with `/:lang/*` pattern - renders Navbar, Routes, Footer
- `Router`: root component with `BrowserRouter` and `NotificationProvider`

### Route Table

| Route | Component | Notes |
| --- | --- | --- |
| `/:lang` | `HomePage` | Landing page with hero, stats, cards |
| `/en/archive`, `/nl/archief` | `ProductionsPage` | Archive listing with filter panel |
| `/en/productions`, `/nl/producties` | (redirect) | Redirects to archive listing |
| `/en/productions/:id`, `/nl/producties/:id` | `ProductionDetailPage` | Production detail page |
| `/en/series`, `/nl/reeksen` | `SeriesPage` | Series listing |
| `/en/series/:id`, `/nl/reeksen/:id` | `SeriesDetailPage` | Series detail with productions timeline |
| `/en/blogs`, `/nl/blogs` | `BlogsPage` | Blog listing |
| `/en/blogs/:id`, `/nl/blogs/:id` | `BlogDetailPage` | Blog detail page |
| `/en/media`, `/nl/media` | `MediaFilesPage` | Media files listing |
| `/en/media/:id`, `/nl/media/:id` | (redirect) | Redirects to media listing with error alert |
| `/en/*`, `/nl/*` | `NotFoundPage` | 404 fallback |
| `/` and unprefixed paths | (redirect) | Normalized to `/:lang/...` via `LanguagePathRedirect` |

### Router Features

- Lazy-loads `Navbar`, `Footer`, and all route pages with Suspense
- `ScrollToTop` scrolls to top on route changes
- Renders `NotificationProvider` for global floating alerts
- Supports redirect aliases for old slug names
- `AliasDetailRedirect` redirects untranslated detail URLs

## Data Access

Frontend API logic is grouped by **feature** under `frontend/src/services/`:

### Shared Transport

- `Api.ts` - shared Axios instance with `baseURL: '/api/v1'`, `Content-Type: application/json` header, `X-API-Key` from `process.env.PUBLIC_API_KEY`; request interceptor adds `Accept-Language` from i18n; response interceptor rejects all errors through `normalizeApiError()`
- `ApiErrorMapper.ts` - normalizes HTTP errors to typed `ApiError` with i18n-translated messages
- `ApiParams.ts` - converts `FilteredListOptions` to backend query params (`pageSize` -> `page_size`, array values comma-separated, scalar values passed directly)
- `ApiTypes.ts` - `ApiError` class (extends Error with `status: number`, `message: string`), `PaginationOptions`, `CommonListFilters` (search, ordering, external_id), `FilteredListOptions<TFilters>` (extends PaginationOptions with filters)

### Error Handling

Common HTTP status codes map to i18n keys:
- `400` -> `apiErrors.status.400`
- `401`, `403`, `404`, `429`, `500` -> status-specific keys
- Network errors (status 0) -> `apiErrors.network`
- Unknown codes -> `apiErrors.status.genericWithCode` (with `{status}` placeholder)

### Feature Clients

Each service folder contains `<Domain>Options.ts` (filter types) and `<Domain>.ts` (API functions):

| Service | Functions | Filter type |
|---------|-----------|-------------|
| `blogs/` | `getBlog(id)`, `getBlogs(options?)` | `BlogFilters { production?, published?, slug?, title? }` |
| `events/` | `getEvent(id)`, `getEvents(options?)` | `EventFilters { production?, hall?, location?, starts_at_after?, starts_at_before?, ends_at_after?, ends_at_before? }` |
| `genres/` | `getGenre(id)`, `getGenres(options?)` | `GenreFilters { type?, vendor_id?, name? }` |
| `halls/` | `getHall(id)`, `getHalls(options?)` | `HallFilters { space?, location?, seat_selection?, open_seating?, name? }` |
| `languages/` | `getLanguage(code)`, `getLanguages(options?)` | `LanguageFilters { code?, name?, is_active? }` |
| `locations/` | `getLocation(id)`, `getLocations(options?)` | `LocationFilters { city?, country?, postal_code?, is_own_location?, name? }` |
| `media/` | `getMediaGalleries(options?)`, `getMediaGallery(id)`, `getMediaItems(options?)`, `getMediaItem(id)` | `MediaGalleryFilters { name? }`, `MediaItemFilters { gallery?, type?, file_format?, original_filename? }` |
| `media_files/` | `getMediaFiles(options?)`, `getMediaFile(id)` | `MediaFileFilters { file_type?, mime_type?, filename?, description? }` |
| `pricing/` | `getPrice(id)`, `getPrices(options?)`, `getPriceRank(id)`, `getPriceRanks(options?)` | `PriceFilters { type?, visibility?, membership?, cineville_box?, description? }`, `PriceRankFilters { position?, position_gte?, position_lte?, description? }` |
| `productions/` | `getProduction(id, include?)`, `getProductions(options?)`, `getLandingStats()` | `ProductionFilters { attendance_mode?, performer_type?, uit_database_type?, genre?, tag?, has_media?, title?, artist_name?, first_event_start_after?, first_event_start_before? }` |
| `spaces/` | `getSpace(id)`, `getSpaces(options?)` | `SpaceFilters { location?, name? }`. Internal type `HallInSpaceResponse` maps nested halls to set `space: null`. |
| `tags/` | `getTag(id)`, `getTags(options?)` | `TagFilters { type?, source?, is_enabled?, name? }` |

### API Client Details

```typescript
const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY,
  },
})

api.interceptors.request.use((config) => {
  const lang = (i18n.resolvedLanguage || i18n.language || 'nl').split('-', 1)[0]
  config.headers.set('Accept-Language', lang)
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(normalizeApiError(error, axios.isAxiosError))
)
```

## Types

All domain model types live in `src/types/`. Key types:

| Type | File | Description |
|------|------|-------------|
| `AppThemeMode` | `Theme.ts` | `'light' \| 'dark'` |
| `ModeToggleProps` | `Theme.ts` | `{ mode: AppThemeMode; onToggleMode: () => void }` |
| `FloatingAlertSeverity` | `FloatingAlertConfig.ts` | `'error' \| 'warning' \| 'info' \| 'success'` |
| `FloatingAlertProps` | `FloatingAlertConfig.ts` | Alert props (open, onClose, message, title, severity, position, etc.) |
| `AttendanceMode` | `Productions.ts` | `'offline' \| 'online'` |
| `PerformerType` | `Productions.ts` | `'group' \| 'solo'` |
| `Production` | `Productions.ts` | Full production model with events, related, genres, blogs |
| `Blog` | `Blogs.ts` | Full blog model (extends `BlogCardData` with body and productions) |
| `Event` | `Events.ts` | Event with production, hall, dates, prices |
| `Tag` | `Tags.ts` | Tag with multilingual name/excerpt/description |
| `Genre` | `Genres.ts` | Genre with type, name, vendor_id |
| `MediaFile` | `MediaFiles.ts` | File with type ('image'\|'pdf'\|'other'), mime_type, size |
| `GenreAndTagChipContext` | `GenreAndTagChip.ts` | `'search' \| 'description' \| 'series' \| 'static'` |
| `GenreAndTagChipType` | `GenreAndTagChip.ts` | `'genre' \| 'seriesTag'` |
| `SearchSortTarget` | `search/types.ts` | `'name' \| 'date'` |
| `SearchSortDirection` | `search/types.ts` | `'asc' \| 'desc'` |
| `SearchViewMode` | `search/types.ts` | `'list' \| 'grid'` |

## Installation

### Prerequisites

- **Node.js LTS** (v20+ recommended)
- **npm**

### Steps

```bash
cd frontend
npm ci
```

Use `npm ci` for exact version reproducibility (recommended for CI).

## Available Scripts

### Development

```bash
npm run dev
```

Starts Vite dev server at `http://localhost:5173` with:
- Fast HMR (hot module reloading)
- Dev proxy for `/api`, `/admin`, `/static`, `/media` -> `http://localhost:8000`

### Build

```bash
npm run build
```

Type-checks (tsc) and builds optimized production assets into `frontend/dist/`.

### Preview

```bash
npm run preview
```

Previews the production build locally.

### Testing

```bash
npm test              # run once
npm run test:watch   # watch mode
```

### Linting and Formatting

```bash
npm run lint            # check all (ESLint, zero warnings)
npm run lint:fix        # auto-fix
npm run format:check    # Prettier check
npm run format:fix      # Prettier auto-format
```

## Testing

Frontend tests use **Jest 30** + **jsdom** + **React Testing Library**.

### Test Setup

- `jest.config.cjs` - ts-jest preset, jsdom environment, setup file `setupTests.ts`, maps `react-pdf` to mock
- `tsconfig.jest.json` - TS config for tests (CommonJS module, Node resolution, includes test files)
- `src/setupTests.ts` - Registers testing-library matchers, polyfills (TextEncoder, TextDecoder, ResizeObserver, IntersectionObserver, matchMedia), mocks axios, sets `process.env.PUBLIC_API_KEY = 'test-api-key'`, suppresses XMLHttpRequest console.error

### Test Structure

```
src/__tests__/
├── App.test.tsx
├── Footer.test.tsx
├── Navbar.test.tsx
├── router.test.tsx
├── contexts/
│   └── NotificationContext.test.tsx
├── features/
│   ├── blogs/         # BlogGridCard, BlogGrid, BlogListCard, BlogList, BlogDetailPage, BlogsPage
│   ├── media-files/   # MediaFileGridCard, MediaFileGrid, MediaFileListCard, MediaFileList, MediaFilePreview, MediaFileUtils, MediaFilesPage
│   ├── productions/   # ProductionsPage
│   └── series/        # SeriesPage
├── pages/
│   └── HomePage.test.tsx
├── services/
│   ├── Api.test.tsx
│   ├── ApiErrorMapper.test.ts
│   ├── ApiParams.test.ts
│   └── (feature service tests: Blogs, Events, Genres, Halls, Languages, Locations, Media, MediaFiles, Pricing, Productions, Spaces, Tags)
├── shared/
│   ├── Navbar.test.tsx
│   └── components/
│       ├── Carousel.test.tsx
│       ├── ChipFilterSection.test.tsx
│       ├── FloatingAlert.test.tsx
│       ├── FloatingAlertStack.test.tsx
│       ├── GenericGrid.test.tsx
│       ├── GenreAndTagChip.test.tsx
│       ├── HtmlText.test.tsx
│       ├── ImageWithFallback.test.tsx
│       ├── LoadingSpinner.test.tsx
│       ├── Pagination.test.tsx
│       ├── SearchBar.test.tsx
│       ├── SearchControlsBar.test.tsx
│       ├── CollectionResultsSkeleton.test.tsx
│       └── search/
│           └── useSearchBarUrlState.test.tsx
├── theme/
│   ├── muiPalette.test.ts
│   ├── styles.test.ts
│   └── tokens.test.ts
└── utils/
    ├── dateUtils.test.ts
    ├── localization.test.ts
    ├── localizedRoutes.test.ts
    ├── locations.test.ts
    ├── mediaFileUrls.test.ts
    ├── SanitizeHtml.test.tsx
    └── translations.test.ts
```

### Test Conventions

- Use React Testing Library for component tests
- Mock external modules in `__mocks__/`
- Wrap with `MemoryRouter`, `ThemeProvider`, and i18n when needed
- `setupTests.ts` provides global mocks for axios, IntersectionObserver, ResizeObserver, matchMedia

### Example Component Test

```typescript
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { ThemeProvider } from '@mui/material/styles'
import { createAppTheme } from '../theme/muiPalette'

test('renders correctly', () => {
  render(
    <MemoryRouter>
      <ThemeProvider theme={createAppTheme('light')}>
        <MyComponent />
      </ThemeProvider>
    </MemoryRouter>
  )
  expect(screen.getByText(/expected text/i)).toBeInTheDocument()
})
```

## Configuration Files

### `package.json`

Name: `viernulvier-frontend`, private, ES module. Key scripts: `dev`, `build` (tsc + vite), `preview`, `lint` (ESLint, zero warnings), `lint:fix`, `format:check`, `format:fix`, `test`, `test:watch`.

### `vite.config.ts`

Configures:
- React plugin for JSX/TSX
- Environment variable loading from `../infrastructure` (`envDir`, `envPrefix: 'PUBLIC_'`)
- Defines `process.env.PUBLIC_API_KEY`
- Dev server proxy (`/api`, `/admin`, `/static`, `/media` -> `http://localhost:8000`)

### TypeScript Configurations

- `tsconfig.json` - App code (ES2020 target, ESNext module, Bundler resolution, `react-jsx`, strict mode)
- `tsconfig.node.json` - Tooling only (Vite config): composite, ESNext, Bundler resolution
- `tsconfig.jest.json` - Tests (CommonJS module, Node resolution, includes test files)

### `eslint.config.cjs`

Flat config using:
- `@typescript-eslint/parser` and plugin
- `eslint-plugin-react`, `eslint-plugin-react-hooks`, `eslint-plugin-react-refresh`
- `eslint-plugin-import` for import ordering
- `eslint-config-prettier` and `eslint-plugin-prettier`
- Enforces: consistent type imports (`verbatimModuleSyntax`), import ordering, MUI sx over inline style, strict React rules
- Zero warnings policy (`--max-warnings 0`)

### `jest.config.cjs`

- ts-jest preset, jsdom environment
- Setup file: `setupTests.ts`
- Maps `react-pdf` to mock
- Coverage collection from `src/`

### `.prettierrc.json`

```json
{
  "semi": false,
  "singleQuote": true,
  "trailingComma": "all",
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "bracketSpacing": true,
  "bracketSameLine": false,
  "arrowParens": "always",
  "endOfLine": "lf"
}
```

### `index.html`

Entry point loads `/src/bootstrap.tsx` as module script. Contains meta description and title "Archive".

### `lighthouserc.json`

Lighthouse CI config: static dist dir, 3 runs, assertions for performance (warn >= 1), accessibility (error >= 1), best-practices (error >= 1), SEO (warn >= 0.5).

## HTML Support in Text Sections

Text sections (descriptions, excerpts, teaser text) support safe HTML rendering via `HtmlText` component.

### How It Works

- `HtmlText` component wraps `sanitizeHtml` utility from `SanitizeHtml.ts`
- All HTML is sanitized with **DOMPurify** (prevents XSS)
- Default rules: `USE_PROFILES.html`, `FORBID_TAGS [br, script]`, `ADD_TAGS [img]`, `ADD_ATTR [alt, height, src, style, title, width]`, `FORBID_ATTR [onblur, onclick, onerror, onfocus, onkeydown, onkeypress, onkeyup, onmouseleave, onmouseenter, onmouseover, onload]`
- Additional rules available: `forbidImagesRule` (removes images), `sanitizeImagesStrictRule` (removes style/width/height/align attributes), `forbidEmbedsRule` (removes iframes)
- `htmlToPlainText()`: decodes HTML entities, replaces block tags with spaces, extracts textContent
- Empty content shows optional fallback message

### Components Using HTML Rendering

| Component | Field | Notes |
| --- | --- | --- |
| `BlogGridCard` | `excerpt` | Blog excerpt in grid |
| `BlogListCard` | `excerpt` | Blog excerpt in list |
| `SeriesGridCard` | `description` | Series description in grid |
| `SeriesListCard` | `description` | Series description in list |
| `SeriesHeader` | `description` | Series description on detail page |
| `Description` (production) | `teaser`, `description` | Production teaser and description |

### Usage Example

```typescript
import HtmlText from '../components/HtmlText'

export const MyComponent = ({ content }) => {
  return <HtmlText html={content} fallback="No description available" />
}
```

## Troubleshooting

### Dev Server Port Conflict

```bash
npm run dev -- --port 3000
```

### Test Environment Errors (browser APIs)

Check `src/setupTests.ts` for polyfills. If adding new browser APIs to components, add corresponding mocks for: TextEncoder, TextDecoder, ResizeObserver, IntersectionObserver, matchMedia, scrollTo.

### ESLint Issues After Updates

```bash
npm run lint          # check (zero warnings policy)
npm run lint:fix      # auto-fix
```

Verify plugin compatibility in `eslint.config.cjs`.

### Build or TS Errors

```bash
npm run build
```

Check `tsconfig*.json` consistency across configs.

### Missing Translation Keys

Add to both:
- `src/locales/en/translation.json`
- `src/locales/nl/translation.json`

Keys are hierarchical (nested objects). Key sections: `nav`, `landing`, `searchbar`, `apiErrors`, `genreChip`, `events`, `archive.home`, `productions`, `blogs.home`, `blog`, `notFound`, `footer`, `series`, `media`.

### API Proxy Issues in Dev

Verify `vite.config.ts` server proxy config. Default routes:
- `/api` -> `http://localhost:8000/api`
- `/admin` -> `http://localhost:8000/admin`
- `/static` -> `http://localhost:8000/static`
- `/media` -> `http://localhost:8000/media`

Ensure backend dev server runs on `:8000`.

## Resources

- [Vite Documentation](https://vite.dev/)
- [React Docs](https://react.dev/)
- [Material UI](https://mui.com/)
- [React Router](https://reactrouter.com/)
- [react-i18next](https://react.i18next.com/)
- [Jest](https://jestjs.io/)
- [React Testing Library](https://testing-library.com/react)
- [DOMPurify](https://github.com/cure53/DOMPurify)
- [Axios](https://axios-http.com/)