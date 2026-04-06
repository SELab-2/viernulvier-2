import { ThemeProvider, createTheme } from '@mui/material/styles'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import ProductionView from '../../components/ProductionView'
import type { Production } from '../../types/Productions'

// Mock child layout components so tests only cover ProductionView's routing logic,
// not the rendering details of the cards themselves.
jest.mock('../../components/ProductionGrid', () => ({
  __esModule: true,
  default: () => <div data-testid="production-grid" />,
}))

jest.mock('../../components/ProductionList', () => ({
  __esModule: true,
  default: () => <div data-testid="production-list" />,
}))

const accentTheme = createTheme({
  palette: {
    mode: 'light',
    accent: { main: '#8224E3', contrastText: '#ffffff' },
  },
})

const baseProduction = (overrides: Partial<Production> = {}): Production => {
  return {
    id: 1,
    attendance_mode: 'offline',
    performer_type: 'solo',
    media_gallery: { id: 0, name: null, media_items: [] },
    uit_database_theme: null,
    uit_database_type: null,
    display_title: null,
    display_artist_name: null,
    title: { nl: 'Voorstelling', en: 'Production' },
    artist_name: { nl: 'Artiest', en: 'Artist' },
    tagline: {},
    teaser: {},
    description: {},
    tags: [],
    genres: [],
    events: [],
    ...overrides,
    first_event_start: overrides.first_event_start ?? null,
    last_event_end: overrides.last_event_end ?? null,
  }
}

const renderView = (props: Parameters<typeof ProductionView>[0]) =>
  render(
    <MemoryRouter>
      <ThemeProvider theme={accentTheme}>
        <ProductionView {...props} />
      </ThemeProvider>
    </MemoryRouter>,
  )

// setupTests.ts mocks window.matchMedia with matches: false, so useMediaQuery returns
// false by default (wide viewport). Override per-test to simulate a narrow viewport.
const mockNarrowViewport = () => {
  window.matchMedia = jest.fn().mockImplementation((query: string) => ({
    matches: true,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  }))
}

const mockWideViewport = () => {
  window.matchMedia = jest.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  }))
}

afterEach(() => {
  mockWideViewport()
})

describe('ProductionView', () => {
  describe('wide viewport', () => {
    it('renders the list layout when layout="list"', () => {
      renderView({ productions: [baseProduction()], layout: 'list' })

      expect(screen.getByTestId('production-list')).toBeInTheDocument()
      expect(screen.queryByTestId('production-grid')).not.toBeInTheDocument()
    })

    it('renders the grid layout when layout="grid"', () => {
      renderView({ productions: [baseProduction()], layout: 'grid' })

      expect(screen.getByTestId('production-grid')).toBeInTheDocument()
      expect(screen.queryByTestId('production-list')).not.toBeInTheDocument()
    })

    it('defaults to the list layout when layout is omitted', () => {
      renderView({ productions: [baseProduction()] })

      expect(screen.getByTestId('production-list')).toBeInTheDocument()
      expect(screen.queryByTestId('production-grid')).not.toBeInTheDocument()
    })
  })

  describe('narrow viewport (below md breakpoint)', () => {
    beforeEach(() => {
      mockNarrowViewport()
    })

    it('always renders the grid layout regardless of layout="list"', () => {
      renderView({ productions: [baseProduction()], layout: 'list' })

      expect(screen.getByTestId('production-grid')).toBeInTheDocument()
      expect(screen.queryByTestId('production-list')).not.toBeInTheDocument()
    })

    it('renders the grid layout when layout="grid"', () => {
      renderView({ productions: [baseProduction()], layout: 'grid' })

      expect(screen.getByTestId('production-grid')).toBeInTheDocument()
      expect(screen.queryByTestId('production-list')).not.toBeInTheDocument()
    })

    it('overrides the default list layout and renders the grid', () => {
      renderView({ productions: [baseProduction()] })

      expect(screen.getByTestId('production-grid')).toBeInTheDocument()
      expect(screen.queryByTestId('production-list')).not.toBeInTheDocument()
    })
  })
})
