import { ThemeProvider, createTheme } from '@mui/material/styles'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import ProductionView from '../../components/ProductionView'

import type { Production } from '../../types/Productions'

// Mock child layout components so tests only cover ProductionView's routing logic,
// not the rendering details of the cards themselves.
jest.mock('../../components/ProductionGrid', () => ({
  __esModule: true,
  default: ({
    productions,
    selectedGenreIds,
  }: {
    productions: Array<{ id: number }>
    selectedGenreIds?: number[]
  }) => (
    <div data-selected-genres={selectedGenreIds?.join(',') ?? ''} data-testid="production-grid">
      {productions.map((production) => production.id).join(',')}
    </div>
  ),
}))

jest.mock('../../components/ProductionList', () => ({
  __esModule: true,
  default: ({
    productions,
    selectedGenreIds,
  }: {
    productions: Array<{ id: number }>
    selectedGenreIds?: number[]
  }) => (
    <div data-selected-genres={selectedGenreIds?.join(',') ?? ''} data-testid="production-list">
      {productions.map((production) => production.id).join(',')}
    </div>
  ),
}))

const accentTheme = createTheme({
  palette: {
    mode: 'light',
    accent: { main: '#8224E3', contrastText: '#ffffff' },
  },
})

const baseProduction = (overrides: Partial<Production> = {}): Production => ({
  id: 1,
  attendance_mode: 'offline',
  performer_type: 'solo',
  media_gallery: { id: 0, name: null, media_items: [] },
  uit_database_type: null,
  display_title: null,
  display_artist_name: null,
  first_event_start: null,
  last_event_end: null,
  title: { nl: 'Voorstelling', en: 'Production' },
  artist_name: { nl: 'Artiest', en: 'Artist' },
  tagline: {},
  teaser: {},
  description: {},
  tags: [],
  genres: [],
  events: [],
  ...overrides,
})

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

    it('sorts productions with selected genres to the front and passes selection through', () => {
      renderView({
        productions: [
          baseProduction({
            id: 1,
            genres: [
              { id: 1, type: 'theme', name: { nl: 'Dans' }, display_name: 'Dans', vendor_id: null },
            ],
          }),
          baseProduction({
            id: 2,
            genres: [
              {
                id: 2,
                type: 'theme',
                name: { nl: 'Theater' },
                display_name: 'Theater',
                vendor_id: null,
              },
            ],
          }),
          baseProduction({ id: 3, genres: [] }),
        ],
        selectedGenreIds: [2],
      })

      expect(screen.getByTestId('production-list')).toHaveTextContent('2,1,3')
      expect(screen.getByTestId('production-list')).toHaveAttribute('data-selected-genres', '2')
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
