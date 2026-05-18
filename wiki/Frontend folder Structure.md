# Frontend Folder Structure

## Overview

The frontend is organized around reusable UI building blocks, feature-specific services, and route-level pages. The structure balances discoverability with scalability.

## Complete Directory Layout

```
frontend/
├── public/
│   └── fonts/                    # Custom font files
├── src/
│   ├── __mocks__/
│   │   └── react-pdf.ts          # jest mock for react-pdf
│   ├── __tests__/                # mirrors src/ structure
│   │   ├── App.test.tsx
│   │   ├── Footer.test.tsx
│   │   ├── Navbar.test.tsx
│   │   ├── router.test.tsx
│   │   ├── contexts/
│   │   │   └── NotificationContext.test.tsx
│   │   ├── features/
│   │   │   ├── blogs/
│   │   │   │   ├── BlogGridCard.test.tsx
│   │   │   │   ├── BlogGrid.test.tsx
│   │   │   │   ├── BlogListCard.test.tsx
│   │   │   │   ├── BlogList.test.tsx
│   │   │   │   ├── BlogDetailPage.test.tsx
│   │   │   │   └── BlogsPage.test.tsx
│   │   │   ├── media-files/
│   │   │   │   ├── MediaFileGridCard.test.tsx
│   │   │   │   ├── MediaFileGrid.test.tsx
│   │   │   │   ├── MediaFileListCard.test.tsx
│   │   │   │   ├── MediaFileList.test.tsx
│   │   │   │   ├── MediaFilePreview.test.tsx
│   │   │   │   ├── MediaFileUtils.test.tsx
│   │   │   │   └── MediaFilesPage.test.tsx
│   │   │   ├── productions/
│   │   │   │   └── ProductionsPage.test.tsx
│   │   │   └── series/
│   │   │       └── SeriesPage.test.tsx
│   │   ├── pages/
│   │   │   └── HomePage.test.tsx
│   │   ├── services/
│   │   │   ├── Api.test.tsx
│   │   │   ├── ApiErrorMapper.test.ts
│   │   │   ├── ApiParams.test.ts
│   │   │   ├── Blogs.test.ts
│   │   │   ├── Events.test.ts
│   │   │   ├── Genres.test.ts
│   │   │   ├── Halls.test.ts
│   │   │   ├── Languages.test.ts
│   │   │   ├── Locations.test.ts
│   │   │   ├── Media.test.ts
│   │   │   ├── MediaFiles.test.ts
│   │   │   ├── Pricing.test.ts
│   │   │   ├── Productions.test.ts
│   │   │   ├── Spaces.test.ts
│   │   │   └── Tags.test.ts
│   │   ├── shared/
│   │   │   ├── Navbar.test.tsx
│   │   │   └── components/
│   │   │       ├── Carousel.test.tsx
│   │   │       ├── ChipFilterSection.test.tsx
│   │   │       ├── FloatingAlert.test.tsx
│   │   │       ├── FloatingAlertStack.test.tsx
│   │   │       ├── GenericGrid.test.tsx
│   │   │       ├── GenreAndTagChip.test.tsx
│   │   │       ├── HtmlText.test.tsx
│   │   │       ├── ImageWithFallback.test.tsx
│   │   │       ├── LoadingSpinner.test.tsx
│   │   │       ├── Pagination.test.tsx
│   │   │       ├── SearchBar.test.tsx
│   │   │       ├── SearchControlsBar.test.tsx
│   │   │       ├── CollectionResultsSkeleton.test.tsx
│   │   │       └── search/
│   │   │           └── useSearchBarUrlState.test.tsx
│   │   ├── theme/
│   │   │   ├── muiPalette.test.ts
│   │   │   ├── styles.test.ts
│   │   │   └── tokens.test.ts
│   │   └── utils/
│   │       ├── dateUtils.test.ts
│   │       ├── localization.test.ts
│   │       ├── localizedRoutes.test.ts
│   │       ├── locations.test.ts
│   │       ├── mediaFileUrls.test.ts
│   │       ├── SanitizeHtml.test.ts
│   │       └── translations.test.ts
│   ├── contexts/
│   │   ├── NotificationContext.tsx         # global notification provider
│   │   └── notificationContextShared.tsx   # context shape, types, fallback
│   ├── features/                           # domain-driven feature folders
│   │   ├── blogs/
│   │   │   ├── components/
│   │   │   │   ├── BlogGrid.tsx            # grid layout for blog collection
│   │   │   │   ├── BlogGridCard.tsx        # blog card in grid view
│   │   │   │   ├── BlogList.tsx            # list layout for blog collection
│   │   │   │   └── BlogListCard.tsx        # blog card in list view
│   │   │   └── pages/
│   │   │       ├── BlogDetailPage.tsx      # single blog post page
│   │   │       ├── BlogDetailPageSkeleton.tsx # loading skeleton for blog detail
│   │   │       └── BlogsPage.tsx           # blog listing page
│   │   ├── media-files/
│   │   │   ├── components/
│   │   │   │   ├── MediaFileGrid.tsx       # grid layout for media files
│   │   │   │   ├── MediaFileGridCard.tsx   # media file card in grid view
│   │   │   │   ├── MediaFileList.tsx       # list layout for media files
│   │   │   │   ├── MediaFileListCard.tsx   # media file card in list view
│   │   │   │   ├── MediaFilePreview.tsx    # PDF/image preview overlay
│   │   │   │   ├── MediaFileUtils.tsx      # shared media file helpers
│   │   │   │   └── MediaFileView.tsx       # grid/list toggle wrapper
│   │   │   └── pages/
│   │   │       └── MediaFilesPage.tsx      # media files listing page
│   │   ├── productions/
│   │   │   ├── components/
│   │   │   │   ├── cards/
│   │   │   │   │   ├── ProductionGridCard.tsx  # production card in grid view
│   │   │   │   │   └── ProductionListCard.tsx  # production card in list view
│   │   │   │   ├── detail/
│   │   │   │   │   ├── Breadcrumbs.tsx          # detail page breadcrumbs
│   │   │   │   │   ├── Description.tsx          # production teaser + description
│   │   │   │   │   ├── EventList.tsx            # events/dates timeline
│   │   │   │   │   ├── MediaList.tsx            # media gallery (videos + images)
│   │   │   │   │   ├── MetaPanel.tsx            # metadata sidebar (genres, tags, locations)
│   │   │   │   │   ├── RelatedBlogs.tsx         # related blog posts section
│   │   │   │   │   └── RelatedProductions.tsx   # related productions section
│   │   │   │   ├── filter-panel/
│   │   │   │   │   ├── ChipFilterSection.tsx    # genre/tag chip filter section
│   │   │   │   │   ├── FilterCheckbox.tsx       # checkbox filter (solo/group, online/offline)
│   │   │   │   │   ├── FilterDatePicker.tsx     # date range picker for event filters
│   │   │   │   │   ├── FilterPanel.tsx          # full sidebar filter panel
│   │   │   │   │   └── FilterSection.tsx         # collapsible filter section wrapper
│   │   │   │   ├── ProductionGrid.tsx       # grid layout for productions
│   │   │   │   └── ProductionList.tsx       # list layout for productions
│   │   │   └── pages/
│   │   │       ├── ProductionDetailPage.tsx        # single production page
│   │   │       ├── ProductionDetailPageSkeleton.tsx # loading skeleton
│   │   │       └── ProductionsPage.tsx             # archive listing page
│   │   └── series/
│   │       ├── components/
│   │       │   ├── SeriesGridCard.tsx       # series card in grid view
│   │       │   ├── SeriesHeader.tsx         # series detail header (title, metadata)
│   │       │   ├── SeriesListCard.tsx       # series card in list view
│   │       │   └── SeriesStats.tsx          # series statistics (editions, period, type)
│   │       └── pages/
│   │           ├── SeriesDetailPage.tsx      # single series page
│   │           ├── SeriesDetailPageSkeleton.tsx # loading skeleton for series detail
│   │           └── SeriesPage.tsx           # series listing page
│   ├── locales/
│   │   ├── en/
│   │   │   └── translation.json              # English translations (333 lines)
│   │   └── nl/
│   │       └── translation.json              # Dutch translations (333 lines)
│   ├── pages/
│   │   ├── HomePage.tsx                      # landing page with hero, stats, cards
│   │   └── NotFoundPage.tsx                   # 404 fallback page
│   ├── services/                              # API clients by feature
│   │   ├── Api.ts                             # shared Axios instance + interceptors
│   │   ├── ApiErrorMapper.ts                  # error normalization (HTTP -> ApiError)
│   │   ├── ApiParams.ts                       # query param builders (pagination + filters)
│   │   ├── ApiTypes.ts                        # shared interfaces (ApiError, FilteredListOptions)
│   │   ├── blogs/
│   │   │   ├── BlogOptions.ts                 # blog filter/option types
│   │   │   └── Blogs.ts                       # blog API client (getBlog, getBlogs)
│   │   ├── events/
│   │   │   ├── EventOptions.ts                # event filter/option types
│   │   │   └── Events.ts                      # event API client (getEvent, getEvents)
│   │   ├── genres/
│   │   │   ├── GenreOptions.ts                # genre filter/option types
│   │   │   └── Genres.ts                      # genre API client (getGenre, getGenres)
│   │   ├── halls/
│   │   │   ├── HallOptions.ts                 # hall filter/option types
│   │   │   └── Halls.ts                       # hall API client (getHall, getHalls)
│   │   ├── languages/
│   │   │   ├── LanguageOptions.ts              # language filter/option types
│   │   │   └── Languages.ts                   # language API client (getLanguage, getLanguages)
│   │   ├── locations/
│   │   │   ├── LocationOptions.ts             # location filter/option types
│   │   │   └── Locations.ts                   # location API client (getLocation, getLocations)
│   │   ├── media/
│   │   │   ├── MediaOptions.ts                # media filter/option types
│   │   │   └── Media.ts                       # media API client (galleries + items)
│   │   ├── media_files/
│   │   │   ├── MediaFileOptions.ts            # media file filter/option types
│   │   │   └── MediaFiles.ts                  # media file API client (getMediaFiles, getMediaFile)
│   │   ├── pricing/
│   │   │   ├── PricingOptions.ts              # pricing filter/option types
│   │   │   └── Pricing.ts                     # pricing API client (prices + price ranks)
│   │   ├── productions/
│   │   │   ├── ProductionOptions.ts           # production filter/option types
│   │   │   └── Productions.ts                 # production API client (getProduction, getProductions, getLandingStats)
│   │   ├── spaces/
│   │   │   ├── SpaceOptions.ts                # space filter/option types
│   │   │   └── Spaces.ts                       # space API client (getSpace, getSpaces)
│   │   └── tags/
│   │       ├── TagOptions.ts                  # tag filter/option types
│   │       └── Tags.ts                        # tag API client (getTag, getTags)
│   ├── shared/
│   │   ├── Footer.tsx                         # site footer (contact, nav, social)
│   │   ├── Navbar.tsx                         # site navbar (branding, nav links, toggle)
│   │   ├── components/
│   │   │   ├── Carousel.tsx                   # embla-carousel wrapper
│   │   │   ├── CollectionView.tsx             # grid/list toggle + responsive layout
│   │   │   ├── FloatingAlert.tsx              # dismissible floating notification
│   │   │   ├── FloatingAlertStack.tsx          # stack of floating alerts by position
│   │   │   ├── GenericGrid.tsx                # reusable grid wrapper with empty state
│   │   │   ├── GenericList.tsx                 # reusable list wrapper with spacing
│   │   │   ├── HtmlText.tsx                   # safe HTML renderer (DOMPurify)
│   │   │   ├── ImageWithFallback.tsx           # image with branded fallback
│   │   │   ├── LoadingSpinner.tsx              # loading indicator (inline/overlay)
│   │   │   ├── Pagination.tsx                 # page navigation controls
│   │   │   ├── chips/
│   │   │   │   ├── GenreAndTagChip.tsx        # context-aware genre/tag chip
│   │   │   │   ├── genreAndTagChipStyles.ts   # chip style factory function
│   │   │   │   └── genreAndTagChipUtils.ts    # chip utility (query key mapping)
│   │   │   ├── search/
│   │   │   │   ├── SearchBar.tsx              # search input component
│   │   │   │   ├── SearchControlsBar.tsx      # search bar + sort + view toggle toolbar
│   │   │   │   └── types.ts                  # SearchSortTarget, SearchSortDirection, SearchViewMode
│   │   │   └── skeletons/
│   │   │       └── CollectionResultsSkeleton.tsx # card-shaped skeleton loader
│   │   ├── hooks/
│   │   │   ├── useCollectionPageNotification.ts # page-level error notification helper
│   │   │   ├── useCollectionQuery.ts          # paginated fetching with error/retry
│   │   │   ├── useFloatingAlertOnce.ts        # one-time alert from router state
│   │   │   ├── useSearchBarUrlState.ts        # URL-synced search/filter/pagination state
│   │   │   └── useSearchDraft.ts              # ephemeral search input state
│   │   └── layouts/
│   │       └── CollectionPageLayout.tsx        # common collection page shell (search, filters, pagination)
│   ├── theme/
│   │   ├── muiPalette.ts                     # MUI theme factory (createAppTheme)
│   │   ├── muiPalette.d.ts                   # TypeScript augmentation (accent color)
│   │   ├── styles.ts                         # shared sx recipes (navbar, common, homepage)
│   │   └── tokens.ts                          # design system source of truth
│   ├── types/
│   │   ├── Blogs.ts                            # BlogCardData, Blog, BlogListResponse
│   │   ├── Events.ts                           # Event, EventPrice, EventListResponse
│   │   ├── FloatingAlertConfig.ts              # FloatingAlertSeverity, FloatingAlertProps, ALERT_SEVERITIES
│   │   ├── GenreAndTagChip.ts                  # chip types, contexts, toggle interfaces
│   │   ├── Genres.ts                           # Genre, GenreListResponse
│   │   ├── Halls.ts                            # Hall, HallListResponse
│   │   ├── Languages.ts                        # Language, LanguageListResponse
│   │   ├── Locations.ts                        # Location, LocationListResponse
│   │   ├── Media.ts                            # MediaItem, MediaItemCrop, MediaGallery, list responses
│   │   ├── MediaFiles.ts                       # MediaFile, MediaFileListResponse
│   │   ├── Pricing.ts                          # Price, PriceRank, list responses
│   │   ├── Productions.ts                      # Production, ProductionRelated, ProductionListResponse, etc.
│   │   ├── SeriesCardProps.ts                   # SeriesCardProps (tag-based)
│   │   ├── Spaces.ts                           # Space, SpaceListResponse
│   │   ├── Tags.ts                             # Tag, TagListResponse
│   │   └── Theme.ts                            # AppThemeMode, ModeToggleProps
│   ├── utils/
│   │   ├── SanitizeHtml.ts                   # DOMPurify wrapper + HTML-to-plain-text
│   │   ├── dateUtils.ts                      # date/datetime formatting helpers
│   │   ├── hall.ts                           # hall display name resolver
│   │   ├── localization.ts                   # getLocalizedValue for Record<string,string>
│   │   ├── localizedRoutes.ts               # URL slug localization + route helpers
│   │   ├── locations.ts                      # venue name resolution
│   │   ├── mediaFileUrls.ts                  # media file URL construction
│   │   ├── navigation.ts                     # floating alert state helpers for router
│   │   └── translations.ts                   # i18n translation record helpers
│   ├── App.tsx                               # top-level app (theme mode + router)
│   ├── bootstrap.tsx                         # micro shell: idle-deferred app mount
│   ├── i18n.ts                               # i18next setup (EN, NL)
│   ├── index.css                             # global styles (font-face, resets, utilities)
│   ├── main.tsx                              # React DOM render + deferred CSS loading
│   ├── router.tsx                            # route tree, layouts, redirects
│   ├── setupTests.ts                         # Jest polyfills/mocks
│   └── vite-env.d.ts                         # TypeScript Vite type declarations
├── .dockerignore
├── .env                                      # local environment variables
├── .gitignore
├── .prettierignore
├── .prettierrc.json                          # Prettier config (no semicolons, single quotes)
├── Dockerfile                                 # container build
├── eslint.config.cjs                          # ESLint flat config
├── index.html                                # HTML entry (loads bootstrap.tsx)
├── jest.config.cjs                            # Jest config
├── lighthouserc.json                          # Lighthouse CI config
├── package.json                               # dependencies and scripts
├── package-lock.json                          # locked dependency versions
├── tsconfig.jest.json                         # TypeScript for tests
├── tsconfig.json                              # TypeScript app config
├── tsconfig.node.json                         # TypeScript for tooling
└── vite.config.ts                             # Vite build config
```

## Core Files (alphabetical)

### `src/App.tsx`

Top-level app component. Owns:
- Theme mode state (`light`/`dark`) persisted to `localStorage` under key `'vnv-theme-mode'`
- `getInitialMode()`: restores last selected mode on reload, defaults to `'light'`
- `toggleMode()`: flips between `'light'` and `'dark'`, persists to `localStorage`
- Wraps the app in `<ThemeProvider theme={theme}>` + `<CssBaseline />`
- Preloads `/vnv_archive_logo.webp` via `react-dom/preload`
- Passes `mode` and `onToggleMode` to `<Router />`

### `src/bootstrap.tsx`

Minimal bootstrap that renders an empty `<React.StrictMode>` into `#root` immediately. Stores the React root globally as `window.__vnv_root__` and `window.__reactRoot`. Uses `scheduleAppLoad()` which:
1. Prefers `requestIdleCallback` (with 1500ms timeout) for deferred loading
2. Falls back to `requestAnimationFrame`, then `setTimeout(0)`
3. Dynamically imports `./main` during idle time, deferring the heavy bundle

This ensures the initial HTML renders fast (TTI optimization), and the full app loads after the browser is idle.

### `src/i18n.ts`

Configures i18next:
- Loads EN and NL translation bundles
- Default language: `'nl'` (via `DEFAULT_LANGUAGE` from `localizedRoutes.ts`)
- Fallback language: `'nl'`
- Supported languages: `['en', 'nl']`
- `load: 'languageOnly'`, `escapeValue: false`

### `src/index.css`

Global styles:
- `@font-face` declarations for ABC Monument Grotesk (Regular, Medium, Bold, Light, Heavy)
- CSS custom properties for runtime theming
- Global CSS reset and base rules
- Utility classes

### `src/main.tsx`

React DOM bootstrap:
- Imports `App` and `./i18n` (side-effect import to initialize i18next)
- Implements deferred CSS loading: `loadIndexCssDeferred()` creates a `<link>` element, preloads it, then switches `rel` to `'stylesheet'` on load
- Reuses existing React root from `window.__reactRoot` (set by `bootstrap.tsx`) to avoid calling `createRoot()` twice
- Renders `<App />` inside `<React.StrictMode>`

### `src/router.tsx`

Route tree and localization layout:
- `BrowserRouter` wrapper with `NotificationProvider` wrapping all routes
- `ScrollToTop`: scrolls to top on every `pathname`/`search` change via `useLayoutEffect`
- `LanguagePathRedirect`: detects language from pathname, redirects to properly localized path
- `AliasDetailRedirect`: redirects alias slug paths to canonical localized detail routes (e.g., `/producties/:id` -> `/:lang/producties/:id`)
- `LocalizedLayout`: main route layout with `/:lang/*` pattern
  - Normalizes language from URL params, syncs i18n
  - Renders `<Navbar />`, main `<Routes>`, and `<Footer />`
  - Routes:
    - `/` -> `HomePage`
    - `{archiveSlug}` -> `ProductionsPage`
    - `{productionsSlug}` -> redirect to archive
    - `{productionsSlug}/:id` -> `ProductionDetailPage`
    - `{seriesSlug}` -> `SeriesPage`
    - `{seriesSlug}/:id` -> `SeriesDetailPage`
    - `{blogsSlug}` -> `BlogsPage`
    - `{blogsSlug}/:id` -> `BlogDetailPage`
    - `{mediaSlug}` -> `MediaFilesPage`
    - `{mediaSlug}/:id` -> redirect with error alert
    - Compatibility alias routes for untranslated slugs (`archive`, `archief`, `productions`, `producties`, `series`, `reeksen`, `blogs`, `media`) with redirects to localized equivalents
    - `*` -> `NotFoundPage`
- `Router` root: redirects `/` to default localized path, `*` falls through to `LanguagePathRedirect`

### `src/setupTests.ts`

Jest configuration for tests:
- Imports `@testing-library/jest-dom/jest-globals` and `@testing-library/jest-dom`
- Sets global `TextEncoder`/`TextDecoder`
- Sets `process.env.PUBLIC_API_KEY = 'test-api-key'`
- Fully mocks `axios` with interceptors, headers, and default resolved values
- Mocks `IntersectionObserver`, `ResizeObserver`, `window.matchMedia`, `window.scrollTo`
- Suppresses `XMLHttpRequest` console.error noise

## Component Areas

### `src/shared/`

Reusable UI building blocks and layout primitives.

- **Shell components:** `Navbar.tsx`, `Footer.tsx`
- **Layout containers:** `CollectionPageLayout.tsx` (in `layouts/`), `CollectionView.tsx`
- **Primitives:** `ImageWithFallback`, `LoadingSpinner`, `FloatingAlert`, `FloatingAlertStack`, `Pagination`, `GenericGrid`, `GenericList`, `HtmlText`
- **Search UI:** `SearchBar`, `SearchControlsBar`, `useSearchBarUrlState`, `types.ts`
- **Carousel:** `Carousel`
- **Chips:** `GenreAndTagChip` (with style/utils sub-modules)
- **Skeletons:** `CollectionResultsSkeleton`
- **Hooks:** `useCollectionQuery`, `useSearchDraft`, `useFloatingAlertOnce`, `useCollectionPageNotification`, `useSearchBarUrlState`

### `src/features/`

Domain-specific feature folders, each with `components/` and `pages/` subdirectories:

- **blogs/** - Blog listing and detail (grid/list cards, skeleton, pages)
- **media-files/** - Media file listing (grid/list cards, preview, utils, view)
- **productions/** - Archive page with filter panel, production detail (cards, detail components, filter-panel, skeletons, pages)
- **series/** - Series listing and detail (grid/list cards, header, stats, page)

### Feature detail structure (productions example):

```
productions/
├── components/
│   ├── cards/                    # collection card components
│   │   ├── ProductionGridCard.tsx
│   │   └── ProductionListCard.tsx
│   ├── detail/                   # detail page sub-components
│   │   ├── Breadcrumbs.tsx
│   │   ├── Description.tsx
│   │   ├── EventList.tsx
│   │   ├── MediaList.tsx
│   │   ├── MetaPanel.tsx
│   │   ├── RelatedBlogs.tsx
│   │   └── RelatedProductions.tsx
│   ├── filter-panel/             # filter sidebar components
│   │   ├── ChipFilterSection.tsx
│   │   ├── FilterCheckbox.tsx
│   │   ├── FilterDatePicker.tsx
│   │   ├── FilterPanel.tsx
│   │   └── FilterSection.tsx
│   ├── ProductionGrid.tsx
│   └── ProductionList.tsx
└── pages/
    ├── ProductionDetailPage.tsx
    ├── ProductionDetailPageSkeleton.tsx
    └── ProductionsPage.tsx
```

## Pages

### `src/pages/`

Route-level page components:
- `HomePage.tsx` - landing page with hero, stats bar, photo cards, search CTA
- `NotFoundPage.tsx` - 404 fallback page

All feature pages live under `src/features/<feature>/pages/`:
- `features/blogs/pages/BlogsPage.tsx`
- `features/blogs/pages/BlogDetailPage.tsx`
- `features/productions/pages/ProductionsPage.tsx`
- `features/productions/pages/ProductionDetailPage.tsx`
- `features/series/pages/SeriesPage.tsx`
- `features/series/pages/SeriesDetailPage.tsx`
- `features/media-files/pages/MediaFilesPage.tsx`

## Services

### `src/services/`

API clients and transport layer.

**Shared helpers:**
- `Api.ts` - Axios instance with `baseURL: '/api/v1'`, `Content-Type` and `X-API-Key` headers; request interceptor adds `Accept-Language`; response interceptor normalizes errors via `ApiErrorMapper`
- `ApiErrorMapper.ts` - normalizes HTTP errors to typed `ApiError` with i18n-translated messages (400, 401, 403, 404, 429, 500, network errors)
- `ApiParams.ts` - converts `FilteredListOptions` to backend query params (`pageSize`   > `page_size`, array values comma-separated)
- `ApiTypes.ts` - `ApiError` class (extends Error with `status`), `PaginationOptions`, `CommonListFilters`, `FilteredListOptions<TFilters>`

**Feature clients (each folder has `*Options.ts` for filter types and `*.ts` for the API functions):**

| Folder | Client file | Functions | Filter types |
|--------|-------------|-----------|-------------|
| `blogs/` | `Blogs.ts` | `getBlog(id)`, `getBlogs(options?)` | `BlogFilters` (production, published, slug, title) |
| `events/` | `Events.ts` | `getEvent(id)`, `getEvents(options?)` | `EventFilters` (production, hall, location, starts_at_after/before, ends_at_after/before) |
| `genres/` | `Genres.ts` | `getGenre(id)`, `getGenres(options?)` | `GenreFilters` (type, vendor_id, name) |
| `halls/` | `Halls.ts` | `getHall(id)`, `getHalls(options?)` | `HallFilters` (space, location, seat_selection, open_seating, name) |
| `languages/` | `Languages.ts` | `getLanguage(code)`, `getLanguages(options?)` | `LanguageFilters` (code, name, is_active) |
| `locations/` | `Locations.ts` | `getLocation(id)`, `getLocations(options?)` | `LocationFilters` (city, country, postal_code, is_own_location, name) |
| `media/` | `Media.ts` | `getMediaGalleries(options?)`, `getMediaGallery(id)`, `getMediaItems(options?)`, `getMediaItem(id)` | `MediaGalleryFilters` (name), `MediaItemFilters` (gallery, type, file_format, original_filename) |
| `media_files/` | `MediaFiles.ts` | `getMediaFiles(options?)`, `getMediaFile(id)` | `MediaFileFilters` (file_type, mime_type, filename, description) |
| `pricing/` | `Pricing.ts` | `getPrice(id)`, `getPrices(options?)`, `getPriceRank(id)`, `getPriceRanks(options?)` | `PriceFilters` (type, visibility, membership, cineville_box, description), `PriceRankFilters` (position, position_gte, position_lte, description) |
| `productions/` | `Productions.ts` | `getProduction(id, include?)`, `getProductions(options?)`, `getLandingStats()` | `ProductionFilters` (attendance_mode, performer_type, uit_database_type, genre, tag, has_media, title, artist_name, first_event_start_after/before) |
| `spaces/` | `Spaces.ts` | `getSpace(id)`, `getSpaces(options?)` | `SpaceFilters` (location, name). Maps nested halls to set `space: null`. |
| `tags/` | `Tags.ts` | `getTag(id)`, `getTags(options?)` | `TagFilters` (type, source, is_enabled, name) |

## Theme

### `src/theme/tokens.ts`

Design system source of truth.

Defines as a single `tokens` export:
- **Colors:** `accent` (`#8224E3` family: main/light/dark/contrastText), `series` (`#1976d2` family: main/light/dark/contrastText), `light` (background/surface/text/textMuted/border/divider/hover), `dark` (background/surface/text/textMuted/border/divider/hover), `neutral` (black/white/gray50-gray900), `overlay` (black05/white05/footerBorder/mediaNavDark/mediaNavLight/modalBackdropDark/modalBackdropLight), `media` (darkBackground/lightBackground), `semantic` (success/error/warning/info)
- **Spacing:** `xs` (4px) through `3xl` (64px), with numeric variants (0.5 through 8 in 8px units)
- **Typography:** fontFamily (`'ABC Monument Grotesk', Helvetica, Arial, sans-serif`), weights (light=300, regular=400, medium=500, bold=700, heavy=900), sizes (xs=12px through 5xl=48px), lineHeights (tight=1.2, normal=1.5, relaxed=1.7)
- **Shadows:** subtle, sm, md, lg, xl, navbar, mediaControl
- **Border radius:** none through full (`9999px`)
- **Transitions:** fast (150ms), base (200ms), slow (300ms), verySlow (500ms) - all `ease`
- **Z-index:** hide (-1), base (0), dropdown (1000), sticky (1050), modal (1060), overlay (1070), tooltip (1080)
- **Breakpoints:** xs (0px), sm (600px), md (960px), lg (1264px), xl (1920px)
- **Component-specific:** `navbar` (minHeight=64), `card` (borderRadius=4, padding=3, borderRadiusPx=16px, paddingPx=24px, gridCardWidthPx=350), `chip` (borderRadius=2, paddingY=1, paddingX=2)

### `src/theme/muiPalette.ts`

MUI Theme factory exporting `createAppTheme(mode: AppThemeMode = 'light')`. Returns a fully configured MUI Theme:
- Palette: mode-aware (light: primary=black, dark: primary=white; accent=`#8224E3` family)
- Typography: h1–h6, body1, body2, button (mapped from tokens)
- Breakpoints: parsed from tokens
- Shape: `borderRadius=8`
- Spacing: 8px base unit
- Shadows: 25 entries (mostly `'none'` except indices 1–4)
- Component overrides: MuiButton (no textTransform, md borderRadius), MuiCard (lg borderRadius, border), MuiPaper (no backgroundImage), MuiChip (md borderRadius)
- TypeScript augmentation via `muiPalette.d.ts` extends `Palette` + `PaletteOptions` with `accent` and `ButtonPropsColorOverrides` with `accent`

### `src/theme/styles.ts`

Shared `sx` recipe factories:
- `createNavbarStyles()`: returns `{ activeLink, navLink, brandLink, brandLogo, brandArchiveText }`
- `createCommonStyles(theme)`: returns `{ cardBase, gridContainer, navbar, footer, responseImage, linkHover, chipBase, container, stack, textTruncate, centerContent }`
- `createHomePageStyles(theme)`: returns mode-aware styles: `{ heroOverlay, heroOverlayVignette, heroFallbackGradient, heroEyebrowColor, heroTitleColor, heroDescriptionColor, searchIconColor, searchInputBg, searchInputText, searchInputPlaceholder, searchInputBorder, searchInputBorderHover, searchInputBorderFocus, searchButtonBg, searchButtonBgHover, searchButtonText, primaryButtonBg, primaryButtonText, primaryButtonBgHover, secondaryButtonBorder, secondaryButtonBorderHover, secondaryButtonBgHover, secondaryButtonText, tertiaryButtonText, tertiaryButtonTextHover, statBarBg, statValueColor, statLabelColor, cardOverlay, cardOverlayHover, inputBackground, tickerBackground, tickerText, subtleSurface, cardHoverBackground, cardHoverBorder, accentBorder }`

## Types

### `src/types/`

TypeScript interfaces for domain models. Each file exports typed interfaces and list-response types:

| File | Key exports |
|------|-----------|
| `Blogs.ts` | `BlogCardData`, `Blog`, `BlogListResponse` |
| `Events.ts` | `Event`, `EventPrice`, `EventListResponse` |
| `FloatingAlertConfig.ts` | `FloatingAlertSeverity`, `FloatingAlertProps`, `ALERT_SEVERITIES` |
| `GenreAndTagChip.ts` | `ChipLabels`, `GenreAndTagChipContext` (`'search' \| 'description' \| 'series' \| 'static'`), `GenreAndTagChipType` (`'genre' \| 'seriesTag'`), `GenreAndTagChipId`, `GenreAndTagChipToggle`, `GenreAndTagChipProps`, `SearchChipOption`, `GetGenreAndTagChipStylesInput` |
| `Genres.ts` | `Genre`, `GenreListResponse` |
| `Halls.ts` | `Hall`, `HallListResponse` |
| `Languages.ts` | `Language`, `LanguageListResponse` |
| `Locations.ts` | `Location`, `LocationListResponse` |
| `Media.ts` | `MediaItem`, `MediaItemCrop`, `MediaGallery`, `MediaGalleryListResponse`, `MediaItemListResponse` |
| `MediaFiles.ts` | `MediaFile`, `MediaFileListResponse` |
| `Pricing.ts` | `Price`, `PriceRank`, `PriceListResponse`, `PriceRankListResponse` |
| `Productions.ts` | `AttendanceMode` (`'offline' \| 'online'`), `PerformerType` (`'group' \| 'solo'`), `ProductionClassification`, `RelatedTag`, `RelatedProduction`, `ProductionRelated`, `Production`, `ProductionListResponse` |
| `SeriesCardProps.ts` | `SeriesCardProps` (tag-based) |
| `Spaces.ts` | `Space`, `SpaceListResponse` |
| `Tags.ts` | `Tag`, `TagListResponse` |
| `Theme.ts` | `DarkMode`, `LightMode`, `AppThemeMode`, `ModeToggleProps` |

## Utils

### `src/utils/`

Small, pure helper functions:

- **`SanitizeHtml.ts`** - DOMPurify wrapper. Exports: `SanitizeHtmlRule` (type), `forbidImagesRule`, `sanitizeImagesStrictRule`, `forbidEmbedsRule`, `htmlToPlainText()`, `sanitizeHtml()`. Default rules: `USE_PROFILES.html`, `FORBID_TAGS [br, script]`, `ADD_TAGS [img]`, `ADD_ATTR [alt, height, src, style, title, width]`, `FORBID_ATTR [onblur, onclick, onerror, onfocus, onkeydown, onkeypress, onkeyup, onmouseleave, onmouseenter, onmouseover, onload]`.
- **`dateUtils.ts`** - Date/datetime formatters: `formatDate()`, `formatBlogPublishedDate()`, `formatTime()`, `formatDateTime()`, `getProductionDateLabel()` (returns single date or range).
- **`hall.ts`** - `getHallDisplayName(event, lang)`: resolves hall name from `event.hall.name[locale]`, falls back to `event.hall_display`.
- **`localization.ts`** - `getLocalizedValue(obj, lang)`: returns `obj[lang]` or first available value; empty string for null/undefined.
- **`localizedRoutes.ts`** - URL slug localization. Exports: `SUPPORTED_LANGUAGES`, `SupportedLanguage`, `DEFAULT_LANGUAGE`, `normalizeLanguage()`, `getLanguageFromPathname()`, `resolveCurrentLanguage()`, `inferLanguageFromPathname()`, `stripLanguagePrefix()`, `toLocalizedPath()`, `getLocalizedSegment()`. Defines `CanonicalRouteSegment` type and maps canonical slugs to localized segments (en: archive, series, blogs, media, productions; nl: archief, reeksen, blogs, media, producties).
- **`locations.ts`** - Default export `getLocationName(hall, language)`: resolves venue label (location > space > hall name) using `getTranslatedRecord`.
- **`mediaFileUrls.ts`** - `getPublicMediaFileUrl(fileUrl)`: converts absolute URLs to same-origin; root-relative kept as-is; relative URLs get `/` prepended.
- **`navigation.ts`** - `createFloatingAlertState(alert)`: creates router state for floating alerts. Default export `redirectWithFloatingAlert(navigate, to, alert, options?)`: navigates with alert state.
- **`translations.ts`** - `getTranslatedRecord(record, language, fallback)`, `getLocalizedTagName(tag, language)`, `getLocalizedTagExcerpt(tag, language)`: normalize language, return translated fields with fallback.

## Contexts

### `src/contexts/NotificationContext.tsx`

Global notification management. Exports `NotificationProvider`:
- Manages `alerts: FloatingAlertEntry[]` state
- `showFloatingAlert(payload)`: adds alert with auto-incremented id
- `clearFloatingAlert()`: clears all alerts
- `closeFloatingAlert(id)`: removes single alert
- Listens for `location.state.floatingAlert` from router navigation and auto-shows alerts (consumes once per navigation key)
- Renders grouped `<FloatingAlertStack>` components per position

### `src/contexts/notificationContextShared.tsx`

Shared types and utilities for NotificationContext. Exports:
- `FloatingAlertPosition`, `FloatingAlertPayload`, `FloatingAlertEntry`
- `DEFAULT_FLOATING_ALERT_POSITION` (`{ vertical: 'top', horizontal: 'right' }`)
- `getFloatingAlertPositionKey()`, `groupAlertsByPosition()` helpers
- `NotificationContextValue` type: `{ showFloatingAlert, clearFloatingAlert, isFallback }`
- `NotificationContext`: React context
- `fallbackShowFloatingAlert`, `fallbackClearFloatingAlert`: creates a React root in `#notification-fallback-root` when context is unavailable (uses `requestIdleCallback` in production)
- `useNotification()`: returns context value or fallback

## Locales

### `src/locales/`

Two language bundles with identical key structure:

- `en/translation.json` - English translations
- `nl/translation.json` - Dutch translations

Key sections: `nav`, `landing` (hero, stats, cardsSection, cards), `searchbar` (search, filters, resultsFound with pluralization, sort, layout), `apiErrors` (network, status codes), `genreChip`, `events`, `archive.home` (loading, resultsRegionLabel, filterPanelLabel/Title/Placeholder, filters, empty, error, pagination), `productions` (title, home, detail, pagination), `blogs.home` (loading, searchPlaceholder, coverAltFallback, noExcerpt, unpublished, empty, error, pagination, detail), `blog` (couldNotLoad, invalidId), `notFound`, `footer` (address, nav, newsletter), `series` (backToSeries, listPlaceholder, allEditions, showMore, noDescription, noProductions, loading, invalidId, fetchError, untitled, untitledProduction, stats, home, pagination), `media` (couldNotLoad, searchPlaceholder, fileType, size, error, preview, empty, loading, resultsRegionLabel, noDescription).

## Practical Notes

### Folder Organization Principles

1. **Feature-first**: domain logic stays close together (e.g., all blog-related code under `features/blogs/`)
2. **Reusable blocks**: UI pieces used across features live in `shared/`
3. **Tests mirror source**: maintaining test file locations makes them easy to find
4. **Services by feature**: API clients grouped by domain, not by HTTP verb
5. **Avoid deep nesting**: keep the folder depth reasonable for import clarity

### When to Create a New Folder

- **Feature folder** under `src/features/<feature>/` when work is domain-specific (new archive section, new page type)
- **Shared component** under `src/shared/components/` when UI is reused across 2+ features
- **Service folder** under `src/services/<feature>/` when adding new API clients for a feature

### Adding Tests

1. Create a test file in `src/__tests__/` mirroring the source structure
2. Name it `ComponentName.test.tsx` or `functionName.test.ts`
3. Wrap components with `MemoryRouter`, `ThemeProvider`, i18n if needed
4. Use `@testing-library/react` utilities: `render`, `screen`, `userEvent`, etc.

### Linting and Formatting

- ESLint: `npm run lint` (configured in `eslint.config.cjs`)
- Prettier: `npm run format:fix` (configured in `.prettierrc.json`)
- Both are enforced in CI

## Configuration Files

### Root-level

- **`vite.config.ts`** - React plugin, `envDir: '../infrastructure'`, `envPrefix: 'PUBLIC_'`, defines `process.env.PUBLIC_API_KEY`, dev server proxy (`/api`, `/admin`, `/static`, `/media` -> `localhost:8000`)
- **`tsconfig.json`** - ES2020 target, ESNext module, Bundler resolution, `react-jsx`, strict mode, includes `src/`
- **`tsconfig.jest.json`** - CommonJS module, Node resolution, includes test files
- **`tsconfig.node.json`** - For `vite.config.ts` only: composite, ESNext, Bundler resolution
- **`package.json`** - Name: `viernulvier-frontend`, private, ES module. Scripts: `dev`, `build` (tsc + vite), `preview`, `lint`, `lint:fix`, `format:check`, `format:fix`, `test`, `test:watch`
- **`jest.config.cjs`** - ts-jest preset, jsdom environment, setup file `setupTests.ts`, maps `react-pdf` to mock
- **`eslint.config.cjs`** - Flat config with TypeScript, React, React Hooks, React Refresh, Prettier, Import plugins. Enforces: consistent type imports, import ordering, MUI sx over inline style, strict React rules
- **`.prettierrc.json`** - No semicolons (`semi: false`), single quotes, trailing commas, 100 char width, 2-space tabs, LF line endings
- **`index.html`** - Entry: `/src/bootstrap.tsx` (module script), meta description, title "Archive", root div
- **`.env`** - local environment variables

### Environment-Specific

- **`Dockerfile`** - container build for deployment
- **`.dockerignore`** - files to exclude from Docker build
- **`.gitignore`** - git ignore patterns
- **`.prettierignore`** - files to exclude from Prettier
- **`lighthouserc.json`** - Lighthouse CI config: static dist dir, 3 runs, assertions for performance, accessibility, best-practices, SEO thresholds

## Resources

- [Vite Documentation](https://vite.dev/)
- [React Documentation](https://react.dev/)
- [TypeScript Documentation](https://www.typescriptlang.org/docs/)
- [Material UI Documentation](https://mui.com/)
- [React Router Documentation](https://reactrouter.com/)
- [Jest Documentation](https://jestjs.io/)
- [React Testing Library](https://testing-library.com/react)
- [DOMPurify](https://github.com/cure53/DOMPurify)
- [Axios](https://axios-http.com/)