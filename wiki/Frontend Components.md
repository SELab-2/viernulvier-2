# Frontend Components

## Purpose

This page documents the most important frontend components and their responsibilities.
The focus is on reusable UI parts in `frontend/src/components` and how they interact with routing, i18n, and state.

## Component Overview

| Component | File | Responsibility |
|---|---|---|
| Navbar | `frontend/src/components/Navbar.tsx` | Main navigation with responsive slide-down mobile panel, branding, theme toggle, and language switch |
| CollectionPageLayout | `frontend/src/components/CollectionPageLayout.tsx` | Shared search/sort/layout shell for paginated collection pages (productions and blogs) |
| BlogView | `frontend/src/components/BlogView.tsx` | Responsive list/grid renderer for blog cards |

---

## Navbar

**File:** `frontend/src/components/Navbar.tsx`

### Props

| Prop | Type | Description |
|---|---|---|
| `mode` | `'light' \| 'dark'` | Current theme mode; controls which icon is shown on the theme toggle |
| `onToggleMode` | `() => void` | Callback fired when the user clicks the theme toggle |

### Behavior

- **Desktop (≥ lg breakpoint):** nav links display inline in the toolbar alongside the theme and language controls.
- **Mobile (< lg breakpoint):** nav links are hidden from the toolbar; a hamburger button appears. Clicking it slides a panel down below the navbar containing all nav links.
- **Hamburger/close icon:** toggles between `MenuIcon` and `CloseIcon` based on whether the panel is open.
- **`/ Archive` label:** hidden on `xs`/`sm` screens to prevent overflow.
- **Theme toggle:** single icon button showing the active mode icon (`DarkModeOutlinedIcon` / `LightModeOutlinedIcon`); calls `onToggleMode` on click.
- **Language toggle:** single button showing the current language code (`NL`/`EN`); switches to the other language on click.
- **Primary links:** includes Archive, Series, Artists, and Stories (`/blogs`).

---

## BlogView

**File:** `frontend/src/components/BlogView.tsx`

### Props

| Prop | Type | Description |
|---|---|---|
| `blogs` | `Blog[]` | Blog list to render |
| `layout` | `'list' \| 'grid'` | Preferred desktop layout; mobile always falls back to grid |

### Behavior

- Renders `BlogList` for desktop list mode.
- Renders `BlogGrid` for desktop grid mode.
- Enforces grid mode below the `md` breakpoint to keep cards readable on narrow screens.

---

## CollectionPageLayout

**File:** `frontend/src/components/CollectionPageLayout.tsx`

### Usage

- Used by `HomePage` and `BlogsPage` to keep a consistent page rhythm:
	- search + sort + layout controls
	- sidebar panel
	- loading/error/empty states
	- pagination block

### Mobile panel close triggers

| Trigger | Mechanism |
|---|---|
| Clicking the burger/close button | `toggleMobileMenu()` |
| Clicking a nav link inside the panel | `closeMobileMenu()` via `onClick` on each link |
| Navigating to a different route | `isEffectivelyOpen` derives `false` when `menuOpenedAtPath !== location.pathname` |
| Clicking outside the navbar area | `ClickAwayListener` wrapping the full container calls `closeMobileMenu()` |

### State

- `mobileMenuOpen` — plain boolean open/closed flag.
- `menuOpenedAtPath` — the `location.pathname` at the time the menu was opened, or `null` when closed. Used to derive `isEffectivelyOpen`, which is `false` if the user navigates away without explicitly closing.

---

## Guidelines for New Components

When adding a new component, add an entry to the Component Overview table and add a dedicated section below following the same format as Navbar above.
