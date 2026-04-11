## Overview

The frontend follows a modular, feature-based structure that promotes maintainability, scalability, and clear separation of concerns.

```text
frontend/
├── src/
│   ├── __tests__/       # Test files
│   ├── components/      # Reusable UI components
│   ├── constants/       # App-wide constants
│   ├── contexts/        # React Context providers
│   ├── hooks/           # Custom React hooks
│   ├── locales/         # i18n translation files
│   ├── pages/           # Page-level route components
│   ├── services/        # API calls and external services
│   ├── styles/          # Global styles and themes
│   ├── types/           # TypeScript type definitions
│   ├── utils/           # Utility functions and helpers
│   ├── router.tsx       # Route definitions
│   ├── i18n.ts          # i18next configuration
│   ├── main.tsx         # Application entry point
│   └── App.tsx          # Root component
├── public/              # Static assets
├── package.json         # Dependencies and scripts
├── vite.config.ts       # Vite configuration
├── tsconfig.json        # TypeScript configuration
├── jest.config.cjs      # Jest test configuration
├── eslint.config.cjs    # ESLint configuration
└── .prettierrc.json     # Prettier configuration
```

---

## Core Files

### `src/main.tsx`
**Purpose**: Application entry point

- Initializes React
- Wraps app with theme provider
- Imports global styles
- Imports i18n configuration
- Renders root `<App />` component

**Example**:
```tsx
import ReactDOM from 'react-dom/client'
import { ThemeProvider } from '@mui/material'
import App from './App'
import './i18n'
import './index.css'
```

### `src/App.tsx`
**Purpose**: Root component

- Renders the router
- Can include global layouts or providers
- Currently minimal, delegates routing to `router.tsx`

### `src/router.tsx`
**Purpose**: Route definitions and configuration

- Contains all application routes
- Imports page components
- Includes layout components (e.g., Navbar)
- Uses React Router v7

**Structure**:
```tsx
<BrowserRouter>
  <Navbar />
  <Routes>
    <Route path="/" element={<HomePage />} />
    <Route path="/series" element={<SeriesPage />} />
    <Route path="/artists" element={<ArtistsPage />} />
    <Route path="/blogs" element={<BlogsPage />} />
    {/* ... */}
  </Routes>
</BrowserRouter>
```

### `src/i18n.ts`
**Purpose**: Internationalization setup

- Configures i18next
- Imports translation files
- Sets default language
- Defines supported languages

---

## Directories

### `src/components/`
**Purpose**: Reusable UI components used across multiple pages

**Guidelines**:
- Components should be generic and reusable
- Each component should have a single responsibility
- Can include sub-components if needed
- May have co-located styles or tests

**Current components**:
- `Navbar.tsx` - Navigation bar with language switcher

**Naming convention**: PascalCase (e.g., `Button.tsx`, `Card.tsx`)

**Example structure for complex components**:
```text
components/
├── Navbar.tsx
├── Card/
│   ├── Card.tsx
│   ├── Card.test.tsx
│   └── index.ts
```

---

### `src/pages/`
**Purpose**: Page-level components mapped to routes

**Guidelines**:
- One component per route
- Should compose smaller components
- Handle page-specific logic and state
- Named after the route/feature

**Current pages**:
- `HomePage.tsx` - Landing page (`/`)
- `SeriesPage.tsx` - Series list (`/series`)
- `SeriesDetailPage.tsx` - Single series (`/series/:id`)
- `ArtistsPage.tsx` - Artists list (`/artists`)
- `BlogsPage.tsx` - Blogs list (`/blogs`)
- `ProductionDetailPage.tsx` - Single production (`/productions/:id`)

**Naming convention**: PascalCase with "Page" suffix (e.g., `EventsPage.tsx`)

---

### `src/hooks/`
**Purpose**: Custom React hooks for reusable logic

**Use cases**:
- Data fetching logic
- Form state management
- Local storage access
- Window size detection
- Authentication state

**Example**:
```tsx
// useApi.ts
export const useApi = <T,>(url: string) => {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(false)
  
  useEffect(() => {
    // fetch logic
  }, [url])
  
  return { data, loading }
}
```

**Naming convention**: camelCase with "use" prefix (e.g., `useAuth.ts`, `useFetch.ts`)

---

### `src/services/`
**Purpose**: API calls and external service integrations

**Guidelines**:
- Centralize API communication
- Abstract fetch/axios calls
- Handle request/response formatting
- Can include error handling
- Group by feature or resource

**Example structure**:
```text
services/
├── api.ts           # Base API configuration
├── events.ts        # Event-related API calls
├── productions.ts   # Production-related API calls
└── auth.ts          # Authentication API
```

**Example**:
```tsx
// services/events.ts
export const getEvents = async () => {
  const response = await fetch('/api/events')
  return response.json()
}

export const getEventById = async (id: string) => {
  const response = await fetch(`/api/events/${id}`)
  return response.json()
}
```

---

### `src/contexts/`
**Purpose**: React Context providers for global state

**Use cases**:
- Authentication state
- Theme (if not using MUI theme directly)
- User preferences
- Shopping cart
- Notification system

**Example**:
```tsx
// contexts/AuthContext.tsx
export const AuthContext = createContext(...)

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  
  return (
    <AuthContext.Provider value={{ user, setUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
```

**Naming convention**: PascalCase with "Context" suffix (e.g., `AuthContext.tsx`)

---

### `src/types/`
**Purpose**: TypeScript type and interface definitions

**Guidelines**:
- Share types across multiple files
- Can mirror backend models
- Include API response types
- Organize by domain/feature

**Example structure**:
```text
types/
├── index.ts         # Re-export all types
├── event.ts         # Event-related types
├── production.ts    # Production-related types
├── api.ts           # API response types
└── common.ts        # Shared types
```

**Example**:
```tsx
// types/event.ts
export interface Event {
  id: string
  title: string
  date: string
  location: string
}

export interface EventListResponse {
  events: Event[]
  total: number
}
```

**Naming convention**: PascalCase for types/interfaces (e.g., `Event`, `EventResponse`)

---

### `src/utils/`
**Purpose**: Pure utility functions and helpers

**Guidelines**:
- No React dependencies
- Pure functions (same input → same output)
- Easily testable
- Organize by category

**Use cases**:
- Date formatting
- String manipulation
- Array/object transformations
- Validation functions
- Number formatting

**Example structure**:
```text
utils/
├── date.ts          # Date utilities
├── format.ts        # Formatting functions
├── validators.ts    # Validation helpers
└── index.ts         # Re-export utilities
```

**Example**:
```tsx
// utils/date.ts
export const formatDate = (date: Date): string => {
  return new Intl.DateTimeFormat('en-US').format(date)
}

export const isDateInPast = (date: Date): boolean => {
  return date < new Date()
}
```

---

### `src/constants/`
**Purpose**: Application-wide constants

**Use cases**:
- API endpoints
- Configuration values
- Magic numbers
- Enums
- Route paths

**Example**:
```tsx
// constants/routes.ts
export const ROUTES = {
  HOME: '/',
  EVENTS: '/events',
  EVENT_DETAIL: '/events/:id',
  PRODUCTIONS: '/productions',
  PRODUCTION_DETAIL: '/productions/:id',
} as const

// constants/api.ts
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

export const ENDPOINTS = {
  EVENTS: '/events',
  PRODUCTIONS: '/productions',
} as const
```

**Naming convention**: UPPER_SNAKE_CASE for constants

---

### `src/locales/`
**Purpose**: Internationalization translation files

**Structure**:
```text
locales/
├── en/
│   └── translation.json
└── nl/
    └── translation.json
```

**Guidelines**:
- One folder per language (ISO 639-1 codes)
- JSON format for translations
- Nested structure for organization
- Use descriptive keys

**Example**:
```json
{
  "nav": {
    "home": "Home",
    "events": "Events"
  },
  "events": {
    "title": "Events",
    "listPlaceholder": "Events list will be displayed here."
  }
}
```

---

### `src/styles/`
**Purpose**: Global styles, CSS modules, and theme customizations

**Use cases**:
- Global CSS
- MUI theme overrides
- CSS variables
- Shared style utilities

**Example structure**:
```text
styles/
├── theme.ts         # MUI theme configuration
├── global.css       # Global styles
└── variables.css    # CSS custom properties
```

**Example**:
```tsx
// styles/theme.ts
import { createTheme } from '@mui/material'

export const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
  },
  typography: {
    fontFamily: 'Roboto, Arial, sans-serif',
  },
})
```

---

### `src/__tests__/`
**Purpose**: Test files (alternative to co-located tests)

**Options for test organization**:

1. **Centralized** (current): All tests in `__tests__/`
2. **Co-located**: Tests next to the file they test
3. **Hybrid**: Unit tests co-located, integration tests centralized

**Example structure**:
```text
__tests__/
├── App.test.tsx
├── components/
│   └── Navbar.test.tsx
├── pages/
│   ├── HomePage.test.tsx
│   └── EventsPage.test.tsx
└── utils/
    └── date.test.tsx
```

**Naming convention**: `*.test.tsx` or `*.test.ts`

---

## Configuration Files

### `package.json`
- Dependencies (production and dev)
- Scripts (`dev`, `build`, `test`, `lint`, etc.)
- Project metadata

### `vite.config.ts`
- Vite bundler configuration
- Plugin setup (React plugin)
- Build options
- Dev server settings

### `tsconfig.json`
- TypeScript compiler options
- Include/exclude patterns
- Module resolution settings

### `tsconfig.node.json`
- TypeScript config for Vite config files
- Separate from app config

### `tsconfig.jest.json`
- TypeScript config for Jest tests
- Includes Jest types

### `eslint.config.cjs`
- ESLint flat config format
- Rules and plugins
- Parser configuration

### `jest.config.cjs`
- Jest test runner configuration
- Test environment (jsdom)
- Module name mapping
- Setup files

### `.prettierrc.json`
- Code formatting rules
- Print width, quotes, semicolons, etc.

### `.prettierignore`
- Files/folders to skip formatting
- Similar to `.gitignore` syntax

---

## Best Practices

### File Organization

1. **Group by feature**: Consider grouping by feature for larger apps
2. **Co-locate related files**: Keep tests, styles, and types near the component
3. **Use index files**: Re-export from `index.ts` for cleaner imports
4. **Limit nesting**: Avoid deep folder hierarchies

### Naming Conventions

- **Components/Pages**: PascalCase (e.g., `EventCard.tsx`)
- **Hooks**: camelCase with `use` prefix (e.g., `useAuth.ts`)
- **Utils**: camelCase (e.g., `formatDate.ts`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `API_BASE_URL`)
- **Types**: PascalCase (e.g., `Event`, `ApiResponse`)

### Import Order

1. External libraries (React, MUI, etc.)
2. Internal absolute imports (using aliases if configured)
3. Internal relative imports
4. Styles

**Example**:
```tsx
import React from 'react'
import { Container, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'

import { useAuth } from '@/contexts/AuthContext'
import { formatDate } from '@/utils/date'

import { EventCard } from './EventCard'
import './EventsPage.css'
```

---

## Adding New Folders

When the app grows, consider adding:

### `src/layouts/`
**Purpose**: Layout components with shared structure

```tsx
// layouts/MainLayout.tsx
export const MainLayout = ({ children }) => (
  <div>
    <Navbar />
    <main>{children}</main>
    <Footer />
  </div>
)
```

### `src/features/`
**Purpose**: Feature-based organization for large apps

```text
features/
├── events/
│   ├── components/
│   ├── hooks/
│   ├── services/
│   └── pages/
└── productions/
    ├── components/
    ├── hooks/
    ├── services/
    └── pages/
```

### `src/assets/`
**Purpose**: Images, fonts, icons (if not in `public/`)

---

## Quick Reference

| Folder | Purpose | Example |
|--------|---------|---------|
| `components/` | Reusable UI | `Navbar.tsx` |
| `pages/` | Route components | `EventsPage.tsx` |
| `hooks/` | Custom hooks | `useApi.ts` |
| `services/` | API calls | `events.ts` |
| `contexts/` | Global state | `AuthContext.tsx` |
| `types/` | TypeScript types | `event.ts` |
| `utils/` | Pure functions | `formatDate.ts` |
| `constants/` | App constants | `routes.ts` |
| `locales/` | Translations | `en/translation.json` |
| `styles/` | Global styles | `theme.ts` |
| `__tests__/` | Test files | `App.test.tsx` |

---

## Migration Path

If restructuring an existing app:

1. **Create folders** one at a time
2. **Move files** gradually (start with utils/constants)
3. **Update imports** after each move
4. **Run tests** to ensure nothing broke
5. **Update documentation** as you go
