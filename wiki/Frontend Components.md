# Frontend Components

## Purpose

This page documents the main frontend components and how they fit together. The focus is on reusable UI parts in `frontend/src/components` and the shared patterns that power the archive, blog, and series pages.

## Component Overview

| Component | File | Responsibility |
| --- | --- | --- |
| Navbar | `frontend/src/components/Navbar.tsx` | Shared top-level navigation with branding, theme toggle, language toggle, and responsive mobile menu |
| Footer | `frontend/src/components/Footer.tsx` | Shared footer with contact details, route links, social links, and newsletter CTA |
| CollectionPageLayout | `frontend/src/components/CollectionPageLayout.tsx` | Common shell for paginated collection pages with search, sort, view mode, sidebar, loading, error, empty, and pagination states |
| GenericGrid / GenericList | `frontend/src/components/GenericGrid.tsx` and `frontend/src/components/GenericList.tsx` | Reusable render wrappers for card/list collections |
| ImageWithFallback | `frontend/src/components/ImageWithFallback.tsx` | Safe image renderer with fallback behavior |
| SearchControlsBar | `frontend/src/components/searchbar/SearchControlsBar.tsx` | Search input, sorting controls, view toggle, and result count display |
| SearchBar | `frontend/src/components/searchbar/SearchBar.tsx` | Reusable base search input used by search control flows |
| useSearchBarUrlState | `frontend/src/components/searchbar/useSearchBarUrlState.ts` | Synchronizes search, sort, view, and pagination state with URL query parameters |
| ProductionGrid / ProductionList | `frontend/src/components/ProductionGrid.tsx` and `frontend/src/components/ProductionList.tsx` | Archive collection containers that render production cards in grid/list mode |
| ProductionView | `frontend/src/components/ProductionView.tsx` | Chooses list or grid rendering for archive results based on layout and viewport |
| BlogView | `frontend/src/components/BlogView.tsx` | Chooses list or grid rendering for blog results based on layout and viewport |
| Series cards | `frontend/src/components/series/` | Grid/list cards and series header/stat helpers used by the series pages |
| Production cards | `frontend/src/components/productions/` | Production grid/list card components |
| Production detail helpers | `frontend/src/components/production/` | Breadcrumbs, description, events, media, metadata panel, and related productions |
| Entity components | `frontend/src/components/entity/` | Generic entity list/grid/view renderers |
| Blog cards | `frontend/src/components/BlogGridCard.tsx` and `frontend/src/components/BlogListCard.tsx` | Grid/list card renderers for blog entries |
| FloatingAlert | `frontend/src/components/FloatingAlert.tsx` | Dismissible floating error/notification banner |
| LoadingSpinner | `frontend/src/components/LoadingSpinner.tsx` | Shared loading indicator |
| CollectionResultsSkeleton | `frontend/src/components/skeletons/CollectionResultsSkeleton.tsx` | Shared skeleton loader for collection pages |
| Pagination | `frontend/src/components/Pagination.tsx` | Shared pagination control used across collection pages |
| Carousel | `frontend/src/components/carousel/Carousel.tsx` | Generic carousel wrapper used for horizontally scrolling content blocks |

---

## Navbar

**File:** `frontend/src/components/Navbar.tsx`

### Behavior

- Desktop links are shown inline in the top bar.
- Mobile navigation collapses into a slide-down panel opened with a menu button.
- The active route is highlighted via `aria-current="page"`.
- The theme toggle switches between light and dark mode.
- The language toggle switches between English and Dutch.
- The primary nav items are Home, Archive, Series, Blogs, and Media.

## Footer

**File:** `frontend/src/components/Footer.tsx`

### Behavior

- Renders the organization contact block and route links.
- Exposes social links for Facebook, Instagram, TikTok, YouTube, and LinkedIn.
- Includes a newsletter CTA that opens the external subscription page.

## CollectionPageLayout

**File:** `frontend/src/components/CollectionPageLayout.tsx`

### Usage

- Used by `SeriesPage`, `ProductionsPage` and `BlogsPage` to keep their search, loading, error, empty, and pagination states consistent.
- Optionally renders a sidebar on archive pages.
- Hides the view mode toggle on mobile while keeping the same search and sort controls.

## Search Controls

### `SearchControlsBar`

**File:** `frontend/src/components/searchbar/SearchControlsBar.tsx`

- Renders the search field, sort selector, sort direction button, result count, and list/grid toggle.
- Uses translation keys for labels so the same control set works in both languages.

### `SearchBar`

**File:** `frontend/src/components/searchbar/SearchBar.tsx`

- Encapsulates reusable search-input behavior used by higher-level search controls.

### `useSearchBarUrlState`

**File:** `frontend/src/components/searchbar/useSearchBarUrlState.ts`

- Reads the current query string and derives page, search, sort, and view state.
- Updates the URL when the user changes search or sorting options.
- Resets pagination to page 1 when the search or sort state changes.

## Collection Renderers

### `ProductionView`

**File:** `frontend/src/components/ProductionView.tsx`

- Renders `ProductionList` or `ProductionGrid` depending on the selected layout.
- Forces the grid layout on narrow screens so cards remain readable.

### `ProductionGrid` and `ProductionList`

**Files:** `frontend/src/components/ProductionGrid.tsx`, `frontend/src/components/ProductionList.tsx`

- Render archive collection items using a fixed layout strategy (grid or list).
- Delegate card details to the components in `components/productions/`.

### `BlogView`

**File:** `frontend/src/components/BlogView.tsx`

- Mirrors `ProductionView` for blogs.
- Uses the grid layout on mobile even if the desktop layout preference is list.

## Detail Helpers

### Series components

**Files:** `frontend/src/components/series/SeriesListCard.tsx`, `frontend/src/components/series/SeriesGridCard.tsx`, `frontend/src/components/series_details/SeriesHeader.tsx`, `frontend/src/components/series_details/SeriesStats.tsx`

- The card components render the series overview tiles.
- The detail helpers render the series title, metadata, and summary statistics.

### Production components

**Files:** `frontend/src/components/productions/ProductionGridCard.tsx`, `frontend/src/components/productions/ProductionListCard.tsx`, `frontend/src/components/production/Breadcrumbs.tsx`, `frontend/src/components/production/Description.tsx`, `frontend/src/components/production/EventList.tsx`, `frontend/src/components/production/MediaList.tsx`, `frontend/src/components/production/MetaPanel.tsx`, `frontend/src/components/production/RelatedProductions.tsx`

- Production cards render archive items in grid/list form.
- Production detail helpers render breadcrumbs, rich description, event timeline, media, metadata, and related productions.

### Entity components

**Files:** `frontend/src/components/entity/EntityGrid.tsx`, `frontend/src/components/entity/EntityList.tsx`, `frontend/src/components/entity/EntityView.tsx`

- Generic entity renderers used to keep list/grid/view patterns reusable across domains.

### Blog components

**Files:** `frontend/src/components/BlogGridCard.tsx`, `frontend/src/components/BlogListCard.tsx`, `frontend/src/components/BlogGrid.tsx`, `frontend/src/components/BlogList.tsx`

- The grid and list wrappers delegate to the matching card component for each blog entry.

## Supporting Components

- `FloatingAlert.tsx` is used for transient error messages.
- `Pagination.tsx` is shared by the archive and blog collection pages.
- `LoadingSpinner.tsx` and `skeletons/CollectionResultsSkeleton.tsx` provide loading states.
- `GenericGrid.tsx` and `GenericList.tsx` provide reusable mapping/wrapper patterns for collection rendering.
- `ImageWithFallback.tsx` centralizes image fallback behavior for cards and detail media.
- `carousel/Carousel.tsx` is used where horizontally paged content is needed.
- `chips/GenreAndTagChip.tsx` encapsulates the shared genre/tag pill behavior.

## Resources

- [Material UI Components](https://mui.com/material-ui/all-components/)
- [React Patterns](https://react.dev/learn)
