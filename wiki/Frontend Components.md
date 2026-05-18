# Frontend Components

This page documents the main frontend components and how they fit together. The focus is on the reusable UI parts in `frontend/src/shared/` and `src/features/`, and the shared patterns that power the archive, blog, series, and media pages.

For the folder layout and configuration files, see [Frontend folder Structure](./Frontend%20folder%20Structure.md). For the tech stack, routing, styling system, and API layer, see [Frontend](./Frontend.md).

---

## Components by Feature

### Productions

The productions feature lives in `frontend/src/features/productions/` and covers both the archive listing page and the production detail page.

**Pages:**

`ProductionsPage.tsx` is the main archive listing. It uses `CollectionPageLayout` with a sidebar filter panel, fetches genres and tags on mount for filter metadata, and supports filtering by attendance mode, performer type, genre IDs, tag IDs, and date range. Results are sorted with matching genres prioritized. It renders items through `CollectionView` using `ProductionGridCard` or `ProductionListCard` depending on the selected layout. The page size is 12.

`ProductionDetailPage.tsx` fetches a single production with events, related productions, and blogs included. It renders a two-column layout: the left column shows breadcrumbs, a hero image (preferring the `FE3_header` crop, then `hd_ready`, then the first available crop), and the description; the right column shows the `MetaPanel` and `EventList`. Below, it shows media (videos and gallery via `MediaList`), related productions, and related blogs. Invalid IDs, 429 rate limiting, and general errors are all handled - the page shows `ProductionDetailPageSkeleton` while loading.

**Cards:**

`ProductionGridCard.tsx` and `ProductionListCard.tsx` render individual production items in grid and list form respectively. Each card displays the production title, artist name, date range, a thumbnail image via `ImageWithFallback`, and genre/tag chips. Clicking navigates to the production detail page.

**Grid and List wrappers:**

`ProductionGrid.tsx` and `ProductionList.tsx` are thin layout wrappers that map over an array of production items and delegate to the corresponding card component. They use the shared `gridContainer` common style or a vertical stack.

**Detail sub-components (under `components/detail/`):**

`Breadcrumbs.tsx` renders navigation breadcrumbs showing the path from the archive to the current production.

`Description.tsx` shows the production teaser and full description. Both fields are rendered through `HtmlText` for safe HTML output, with a fallback message when content is empty.

`EventList.tsx` displays the list of events associated with a production, including dates, times, hall names, pricing information, and availability status.

`MediaList.tsx` renders the production's media gallery - both videos and images - using a responsive layout. It handles the case where there are no media items gracefully.

`MetaPanel.tsx` is the sidebar on the detail page showing structured metadata: genres (as `GenreAndTagChip` links), tags (as chips linking to filtered archive views), location/venue information, attendance mode (offline/online), and performer type (solo/group).

`RelatedBlogs.tsx` renders a horizontal list of blog cards that link to the associated blog detail pages.

`RelatedProductions.tsx` renders a horizontal scrolling list of production cards that are related to the current one, with links to their detail pages.

**Filter panel (under `components/filter-panel/`):**

`FilterPanel.tsx` is the full sidebar filter component used on the archive page. It accepts props for all filter state (attendance mode, performer type, date range, genre IDs, tag IDs), the full lists of genres and tags for rendering, and callbacks for toggling each filter. It wraps everything in a `LocalizationProvider` (for MUI date pickers with dayjs), has a "Clear filters" button that's disabled when no filters are active, and renders a mobile "Apply" button when used inside a dialog on small screens. Props also include `headerActions` and `onMobileApply` which are injected by `CollectionPageLayout` on mobile.

`ChipFilterSection.tsx` renders a searchable, scrollable list of `GenreAndTagChip` components for either genre or tag filtering. It accepts an array of `ChipOption` objects (each with id, name, labels, and chipType), the currently selected IDs, and a toggle callback. When the list is empty, it shows a localized "no results" label.

`FilterSection.tsx` is a collapsible section wrapper with a title and expand/collapse toggle, used to group related filters together within `FilterPanel`.

`FilterCheckbox.tsx` is a styled checkbox used for binary or enum filter options like performer type (solo/group) and attendance mode (online/offline).

`FilterDatePicker.tsx` is a date picker input for the "events starting after" and "events starting before" date range filters, using MUI's `DatePicker` with dayjs adapter.

**Skeleton:**

`ProductionDetailPageSkeleton.tsx` renders a placeholder skeleton matching the layout of the real detail page, so the transition from loading to loaded content is visually smooth.

---

### Blogs

The blogs feature lives in `frontend/src/features/blogs/`.

**Pages:**

`BlogsPage.tsx` is the blog listing page. It uses `CollectionPageLayout` without a sidebar, with a page size of 12. The default sort is by name (`title_sort`) or date (`published_at`), and it filters to only published blogs. Items are rendered through `CollectionView` with `BlogListCard` or `BlogGridCard`.

`BlogDetailPage.tsx` fetches a single blog by its ID, validates that the ID is numeric, and handles 429 and other errors. If the blog is unpublished, it redirects back to the listing. The page renders breadcrumbs, the publication date, a hero image, the blog title, and the body content (teaser and full text through `HtmlText`). If the blog has associated productions, it shows a `RelatedProductions` section. While loading, `BlogDetailPageSkeleton` is shown.

**Cards:**

`BlogGridCard.tsx` renders a blog item in card form within a grid layout. It shows the blog title, a localized excerpt (via `HtmlText`), the featured image (via `ImageWithFallback`), and the publication date.

`BlogListCard.tsx` renders the same information in a horizontal list layout.

**Layout wrappers:**

`BlogGrid.tsx` and `BlogList.tsx` iterate over blog items and delegate to `BlogGridCard` or `BlogListCard` respectively. They use the shared grid/list common styles.

**Skeleton:**

`BlogDetailPageSkeleton.tsx` renders a skeleton matching the blog detail page layout.

---

### Series

The series feature lives in `frontend/src/features/series/`.

**Pages:**

`SeriesPage.tsx` is the series listing page. Unlike other collection pages, it fetches all enabled tags and sorts them in-memory rather than relying on backend sorting. It forces sort target to "name" only, with a page size of 12 for client-side pagination. Items are rendered through `CollectionView` with `SeriesListCard` or `SeriesGridCard`.

`SeriesDetailPage.tsx` fetches a single tag's metadata and the first page of productions for that series. It shows a `SeriesHeader` with the tag name and description, `SeriesStats` with aggregated statistics (number of editions, time period, series type), and a timeline-style grouping of productions by year. A "Load more" button enables pagination through the series' productions. The page handles invalid IDs, 429 errors, and general fetch errors. While loading, `SeriesDetailPageSkeleton` is shown.

**Cards:**

`SeriesGridCard.tsx` and `SeriesListCard.tsx` both accept a `SeriesCardProps` which wraps a `Tag` object. They render the series tag name, a localized excerpt, and a production count badge. Clicking navigates to the series detail page.

**Detail components:**

`SeriesHeader.tsx` renders the top section of the series detail page: the localized tag name as a heading, the description rendered through `HtmlText`, and a subtitle with additional context.

`SeriesStats.tsx` shows aggregated statistics about the series: the number of editions (productions), the time period spanned, and the series type. It uses localized date formatting.

**Skeleton:**

`SeriesDetailPageSkeleton.tsx` renders a skeleton matching the series detail page layout.

---

### Media Files

The media files feature lives in `frontend/src/features/media-files/`.

**Pages:**

`MediaFilesPage.tsx` is a collection page without a sidebar. It uses `CollectionPageLayout` with a page size of 12, sorting by name (filename) or date (created_at). Items are rendered through `MediaFileView`.

**Components:**

`MediaFileGridCard.tsx` and `MediaFileListCard.tsx` render individual media file items in grid and list form. They show the file name, type (image/PDF/other), file size (formatted via `MediaFileUtils`), a thumbnail for images, and an icon for PDFs and other files.

`MediaFileGrid.tsx` and `MediaFileList.tsx` iterate over media file items and delegate to the corresponding card component.

`MediaFileView.tsx` is a wrapper that selects between `MediaFileGrid` and `MediaFileList` based on the current layout mode (`SearchViewMode`).

`MediaFilePreview.tsx` renders a full-screen overlay for previewing media files - images are shown inline and PDFs are rendered using `react-pdf`. It supports previous/next navigation between files in the collection and a download button. Close and navigation controls are accessible via keyboard.

`MediaFileUtils.tsx` contains shared utility functions and components for the media file feature: file type icon mapping (image, PDF, other), human-readable file size formatting, and MIME type labeling.

---

## Page Components

### HomePage

**File:** `frontend/src/pages/HomePage.tsx`

The landing page renders a hero section with a background image, gradient overlays, and a fade-up animation. It includes a search bar that navigates to `/archive?q=...`, three CTA buttons ("Open archive", "Browse series", "Visit official website"), and a stats bar that fetches `getLandingStats()` on mount to show counts for productions, series, years, and blogs. Below, a grid of four photo cards links to the archive, series, blogs, and media sections with hover effects. Mode-aware styling comes from `createHomePageStyles(theme)`, and error handling uses `useCollectionPageNotification`.

### NotFoundPage

**File:** `frontend/src/pages/NotFoundPage.tsx`

A centered card displaying a 404 title, a description message, and a "Back to home" button. Routing is language-aware so the button navigates to the localized home path.

---

## Shell Components

### Navbar

**File:** `frontend/src/shared/Navbar.tsx`

The site-wide top navigation bar accepts `ModeToggleProps` (the current theme mode and a toggle callback). On desktop, navigation links are shown inline alongside the branding, language switch (EN ↔ NL), and a light/dark toggle. On mobile, the links collapse into a hamburger menu that slides down on tap. Active routes are highlighted with `aria-current="page"`, and all paths are localized. The component uses `ResizeObserver` to publish `--navbar-height` as a CSS variable so other components (like `FloatingAlert`) can account for the navbar height. Styling comes from `createNavbarStyles()`.

### Footer

**File:** `frontend/src/shared/Footer.tsx`

The site-wide footer is divided into three sections: contact information (organization name, street address, postal code/city, phone numbers, email, VAT number), navigation links (Home, Archive, Series, Blogs, Media), and a social/newsletter section. Social media icons link to Facebook, Instagram, TikTok, YouTube, and LinkedIn (rendered with custom SVGs). A newsletter CTA links to the external viernulvier.gent subscription page. All routes are language-aware, and external links open in a new tab. Styling comes from `createCommonStyles(theme)`.

---

## Layout Components

### CollectionPageLayout

**File:** `frontend/src/shared/layouts/CollectionPageLayout.tsx`

This is the primary layout shell for all paginated collection pages (archive, blogs, series, media). It manages the entire user experience flow: search, filtering, sorting, view toggling, loading, error, empty state, and pagination.

The component accepts a large props interface (`CollectionPageLayoutProps`) covering search controls (placeholder, value, change/submit callbacks), sort controls (target, direction, options), view mode (list/grid), result count, sidebar content, loading/error/empty states, and pagination (page, page size, total items, page change callback). On desktop, the sidebar (when `showSidebar` is true) is rendered inline to the left. On mobile, it's rendered inside a full-screen Material UI Dialog that slides in from the left, with `headerActions` and an `onMobileApply` callback injected into the sidebar content via `cloneElement`.

The loading state shows a spinner by default, or custom `loadingContent` (like `CollectionResultsSkeleton`) if provided. The error state shows a `FloatingAlert` with a retry button. The empty state shows a centered `Paper` with a title and description. When there are results, it renders `resultsContent` inside the main area, with `Pagination` below. The layout dynamically adjusts its max-width based on viewport size, the number of card columns, and whether the sidebar is visible.

### CollectionView

**File:** `frontend/src/shared/components/CollectionView.tsx`

A generic layout toggle component that renders items in either list or grid mode. It accepts a `CollectionViewProps<T>` generic type with `items`, an optional `layout` (defaults to grid), `getKey`/`renderListItem`/`renderGridItem` render functions, optional `transformItems` and `sortItems` callbacks, and `listSpacing`. On mobile (below the `md` breakpoint), it always forces grid layout. It delegates rendering to `GenericList` or `GenericGrid`.

---

## Shared Components

### Search Controls

`SearchBar.tsx` is a controlled MUI TextField with a search icon submit button. It accepts `placeholder`, `searchValue`, `onSearchChange`, and an optional `onSearchSubmit` callback.

`SearchControlsBar.tsx` composes a full search toolbar: the `SearchBar` on the left, a sort target dropdown (`Select`), a sort direction toggle button (ascending/descending), a view mode toggle (`ToggleButtonGroup` for list/grid), a result count label, and any `extraControls` passed as a ReactNode. It's used inside `CollectionPageLayout`.

`types.ts` defines the shared search types: `SearchSortTarget` (`'name' | 'date'`), `SearchSortDirection` (`'asc' | 'desc'`), `SearchViewMode` (`'list' | 'grid'`), and `DEFAULT_SORT_TARGET_OPTIONS`.

### FloatingAlert and FloatingAlertStack

`FloatingAlert.tsx` renders a dismissible floating notification banner. It supports four severity levels (error, warning, info, success) with color coding. The `position` prop (`{ vertical, horizontal }`) places it at any corner or edge of the screen. In standalone mode (when `disableFloatingWrapper` is true), it auto-closes after a timeout. Top-positioned alerts account for the navbar height by reading the `--navbar-height` CSS variable.

`FloatingAlertStack.tsx` is a fixed-position container that renders multiple `FloatingAlert` instances grouped by screen position. It's used by `NotificationProvider` to display all active alerts. Each alert has an `id` so it can be individually dismissed.

### LoadingSpinner

A reusable loading indicator using MUI's `CircularProgress`. It supports two modes: inline (renders a small spinner within the content flow) and full-screen (renders a fixed overlay with a centered spinner). An optional `label` provides accessible text. The `size` and `color` props map to MUI's CircularProgress props.

### ImageWithFallback

Renders an image with a branded fallback. If the `src` fails to load, it displays the `/vnv_logo.webp` placeholder image. In dark mode, the fallback image is inverted using CSS filters. It extends MUI's `Box` props (minus `component`, `src`, and `alt`) for layout flexibility.

### HtmlText

A safe HTML renderer that sanitizes content through `sanitizeHtml()` from `SanitizeHtml.ts` before rendering via `dangerouslySetInnerHTML`. It accepts an `html` string, an optional `fallback` (a ReactNode shown when the content is empty), a `variant` for MUI typography, a `component` for the HTML element, and `sx` for styling. This component is used throughout the app for production descriptions, blog excerpts, series descriptions, and any field that may contain HTML from the CMS.

### Pagination

A shared pagination control with First/Prev/Page Input/Of N/Next/Last buttons, using i18n for all labels. It accepts `page`, `pageSize`, `totalItems`, an `onPageChange` callback, an optional `disabled` flag, and an `i18nKeyPrefix` that defaults to `'productions.pagination'`. It automatically hides itself when there's only one page or fewer.

### GenericGrid and GenericList

`GenericGrid` and `GenericList` are thin mapping wrappers that accept an array of items, a `getKey` function, and a `renderItem` function. `GenericGrid` uses the shared `gridContainer` common style for CSS Grid layout. `GenericList` uses MUI's `Stack` with configurable `spacing`. Both handle the empty state by rendering a localized "no results" message.

### CollectionResultsSkeleton

A skeleton loader that renders placeholder cards matching the dimensions of real content cards. It accepts `layout` (list or grid), `isMobile`, and an optional `cards` count. In list mode, it renders stacked `Paper` components with text `Skeleton` placeholders. In grid mode, it renders card-shaped placeholders with image and text areas. This gives users a visual indication that content is loading without layout shift.

### Carousel

A generic carousel/slider component built on Embla Carousel with wheel gesture support. It renders a horizontal scrolling area with optional prev/next arrow buttons (revealed on hover), dot navigation, and keyboard/touch interaction. Props include `ariaLabel` for accessibility, `loop` for infinite scrolling, `showArrows`/`showDots` toggles, customizable button labels, and an `sx` style prop. The active dot scrolls into view automatically.

### GenreAndTagChip

A context-aware chip component that changes behavior based on its `context` prop. In `"search"` context, it toggles as a filter (clicking adds or removes the chip from the active filters, and a selected chip shows a close icon). In `"description"` context, it links to the archive page with the chip name as a search query. In `"series"` context, it links to the series detail page. In `"static"` context, it's a non-interactive display chip. The chip's color is determined by `chipType` - `"genre"` chips use the accent color (purple), while `"seriesTag"` chips use the series color (blue). Styling is handled by `genreAndTagChipStyles.ts`, which returns MUI `sx` styles based on theme, selected state, context, and chip type. The utility file `genreAndTagChipUtils.ts` exports `getQueryKeyForChipType()` which maps genre to the URL parameter `'g'` and seriesTag to `'t'`.

---

## Hooks

### useCollectionQuery

**File:** `frontend/src/shared/hooks/useCollectionQuery.ts`

The central data-fetching hook for all paginated collection pages. It accepts a `CollectionQueryOptions` object with a `deps` dependency array (re-fetches when the JSON serialization changes), a `fetcher` function (the API call), a `select` function (to transform the response into `{ items, count }`), optional `mapError` and `mapFloatingMessage` callbacks, and optional `initialItems`/`initialCount`.

It returns `{ isLoading, items, count, error, floatingAlert, retry }`. The `error` state includes both a `message` and a `showFallback` flag. The `floatingAlert` state includes `isOpen`, `message`, and a `close` callback. Calling `retry()` increments an internal key that triggers a re-fetch.

On fetch start, it sets `isLoading` to true and clears the error. On success, it populates `items` and `count`. On failure, it calls `mapError` to determine the error state and `mapFloatingMessage` for the alert text, then sets `showFallback: true` and opens the floating alert. An internal `isActive` flag prevents state updates after the component unmounts.

### useSearchBarUrlState

**File:** `frontend/src/shared/hooks/useSearchBarUrlState.ts`

This hook synchronizes all search, filter, sort, view, and pagination state with URL query parameters. It uses `useSearchParams` with `replace: true` so that filter changes don't pollute the browser history.

The URL parameter encoding is compact: `q` for query, `st` for sort target (`n`=name, `d`=date), `sd` for sort direction (`a`=asc, `d`=desc), `v` for view mode (`l`=list, `g`=grid), `p` for page, `am` for attendance mode (`of`=offline, `on`=online), `pt` for performer type (`g`=group, `s`=solo), `fa` and `fb` for date range filters (YYYY-MM-DD), `g` for genre IDs (dash-separated), `t` for tag IDs (dash-separated). All defaults are omitted from the URL to keep it clean.

The hook returns a comprehensive `SearchBarUrlState` object with all current values, individual setters, and toggle functions. Every setter that changes a filter or sort automatically resets the page to 1. On mobile, the view mode is always forced to `'grid'` and the `v` parameter is removed from the URL. The `clearFilters()` method resets attendance mode, performer type, genres, tags, and date range to their defaults.

### useSearchDraft

**File:** `frontend/src/shared/hooks/useSearchDraft.ts`

Manages ephemeral search input state - the text the user is typing before they commit it. It tracks a `draft` string separately from the committed value, exposing `isDirty` (whether the draft differs from committed) and `displayedValue` (the committed value, or the draft if dirty). The `submit()` function calls `onCommit` when the draft differs, or `onSameQuery` when it matches. Queries are normalized (trimmed and lowercased) before comparison. The `reset()` function reverts the draft to the last committed value.

### useFloatingAlertOnce

**File:** `frontend/src/shared/hooks/useFloatingAlertOnce.ts`

Reads a `floatingAlert` payload from React Router's navigation state and shows it exactly once. After displaying, it clears the alert from the browser history state so that it doesn't re-appear on subsequent renders. Returns `{ isOpen, message, close }`.

### useCollectionPageNotification

**File:** `frontend/src/shared/hooks/useCollectionPageNotification.ts`

A convenience hook for collection pages that want a consistent error notification pattern. It accepts a `messageKey` (an i18n translation key) and returns `{ showFloatingAlert, clearFloatingAlert }`. When called with an error, it checks if it's an `ApiError` with status 429 (rate limited) and shows it as a warning; all other errors are shown with error severity using the translated message as fallback.

---

## Contexts

### NotificationProvider

**File:** `frontend/src/contexts/NotificationContext.tsx`

Wraps the entire app and provides a floating alert API through React context. It manages an array of `FloatingAlertEntry` objects (each with an auto-incremented ID). The `showFloatingAlert(payload)` method adds a new alert, `clearFloatingAlert()` removes all alerts, and `closeFloatingAlert(id)` removes a single alert. The provider also listens to `location.state.floatingAlert` from React Router navigation state - if a route transition includes alert data, it automatically shows it once and then clears it from the history state. All alerts are grouped by position and rendered through `FloatingAlertStack` components.

### Notification Context Shared

**File:** `frontend/src/contexts/notificationContextShared.tsx`

Contains all the shared types and utilities used by `NotificationContext`: `FloatingAlertPosition`, `FloatingAlertPayload`, `FloatingAlertEntry`, `DEFAULT_FLOATING_ALERT_POSITION` (top-right), grouping helpers, and the `NotificationContext` React context. It also provides a fallback implementation - if `NotificationProvider` is not present (e.g., in isolated tests), `fallbackShowFloatingAlert` creates a React root in the `#notification-fallback-root` DOM element and renders the alert there. This uses `requestIdleCallback` in production and synchronous rendering in test environments for reliability. The `useNotification()` hook returns the context value if available, or the fallback otherwise.

---

## Patterns and Best Practices

### Composition

Pages assemble small, testable components (cards, lists, filters). Business logic lives in hooks or service calls, not in presentational components. Reusable pieces go to `src/shared/`, domain-specific pieces stay in `src/features/<domain>/`. Feature components are organized into subfolders: `cards/`, `detail/`, `filter-panel/`.

### Reusability

When a UI piece is used in 2+ features, it moves to `src/shared/`. The `CollectionView` + `GenericGrid`/`GenericList` pattern provides the common grid/list rendering, and `CollectionPageLayout` provides the common page shell. Shared hooks like `useCollectionQuery` and `useSearchBarUrlState` standardize data fetching and URL state management across all collection pages.

### Styling

Prefer `sx` props using tokens from `src/theme/tokens.ts`. Avoid hard-coded colors and use the palette from the theme. Reference shadows, border radii, and spacing through tokens. Use the style factory functions (`createNavbarStyles`, `createCommonStyles`, `createHomePageStyles`) from `styles.ts` for shared component styles.

### Accessibility

Use semantic HTML (`<button>`, `<nav>`, `<article>`, etc.). Add `aria-*` attributes where needed (e.g., `aria-current="page"` on active nav links). All interactive controls should be keyboard-accessible, and `:focus`/`:focus-visible` states should be visible.

### URL State Management

Use `useSearchBarUrlState` for all collection pages - it syncs search, filters, pagination, and view mode to URL params. All parameter changes use `replace: true` to avoid history pollution. Mobile always forces grid view mode. The page resets to 1 whenever a filter, sort, or search value changes.

### Error Handling

Use `useCollectionQuery` for data fetching - it handles loading, error, and retry states. Use `useCollectionPageNotification` for page-level error alerts. Use `useFloatingAlertOnce` for one-time alerts from router state (e.g., redirect messages). Use `redirectWithFloatingAlert()` from `navigation.ts` for programmatic redirects that carry an alert. Status 429 errors show as warnings; all other errors show as error severity.

### Testing

Most shared components have dedicated tests in `src/__tests__/shared/`. Wrap components with `MemoryRouter`, `ThemeProvider`, and i18n when needed. Test behavior, not implementation. The `setupTests.ts` file provides global mocks for axios, `IntersectionObserver`, `ResizeObserver`, `matchMedia`, and `scrollTo`.

```typescript
test('renders and responds to clicks', () => {
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

---

## Examples (How to Build a New Feature)

### 1. Create a List Page for a New Domain

1. **Add API client** under `src/services/<domain>/` with both `*Options.ts` (filter types) and `*.ts` (fetch functions)
2. **Add types** in `src/types/<Domain>.ts` (model interfaces and list response)
3. **Create feature folder** `src/features/<domain>/pages/<Domain>Page.tsx` using `CollectionPageLayout`, `CollectionView`, `useSearchBarUrlState`, and `useCollectionQuery`
4. **Add route** in `src/router.tsx` with lazy loading
5. **Add translations** to both `src/locales/en/translation.json` and `nl/translation.json`
6. **Add tests** under `src/__tests__/features/<domain>/`
7. **Update this wiki** with a feature summary

---

## Resources

- [Material UI Components](https://mui.com/material-ui/all-components/)
- [React Patterns](https://react.dev/learn)
- [React Testing Library](https://testing-library.com/react)
- [Accessibility (a11y)](https://www.w3.org/WAI/WCAG21/quickref/)