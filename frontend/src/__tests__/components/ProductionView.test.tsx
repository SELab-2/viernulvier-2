import { ThemeProvider, createTheme } from '@mui/material/styles'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import CollectionView, { type CollectionViewProps } from '../../components/CollectionView'

const accentTheme = createTheme({
  palette: {
    mode: 'light',
    accent: { main: '#8224E3', contrastText: '#ffffff' },
  },
})

const renderView = (props: CollectionViewProps<number>) =>
  render(
    <MemoryRouter>
      <ThemeProvider theme={accentTheme}>
        <CollectionView {...props} />
      </ThemeProvider>
    </MemoryRouter>,
  )

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

describe('CollectionView', () => {
  it('applies transformItems before rendering list items', () => {
    renderView({
      items: [1, 2, 3],
      layout: 'list',
      getKey: (item) => item,
      renderListItem: (item) => <div data-testid="list-item">{item}</div>,
      renderGridItem: (item) => <div data-testid="grid-item">{item}</div>,
      transformItems: (items) => [...items].sort((a, b) => b - a),
    })

    const listItems = screen.getAllByTestId('list-item').map((node) => node.textContent)
    expect(listItems).toEqual(['3', '2', '1'])
  })

  it('renders the grid layout when layout="grid"', () => {
    renderView({
      items: [1],
      layout: 'grid',
      getKey: (item) => item,
      renderListItem: (item) => <div data-testid="list-item">{item}</div>,
      renderGridItem: (item) => <div data-testid="grid-item">{item}</div>,
    })

    expect(screen.getByTestId('grid-item')).toBeInTheDocument()
    expect(screen.queryByTestId('list-item')).not.toBeInTheDocument()
  })

  it('defaults to the list layout when layout is omitted', () => {
    renderView({
      items: [1],
      getKey: (item) => item,
      renderListItem: (item) => <div data-testid="list-item">{item}</div>,
      renderGridItem: (item) => <div data-testid="grid-item">{item}</div>,
    })

    expect(screen.getByTestId('list-item')).toBeInTheDocument()
    expect(screen.queryByTestId('grid-item')).not.toBeInTheDocument()
  })

  it('sorts items with a matching id to the front via transformItems', () => {
    // Mirrors the sortProductionsBySelectedGenres logic in ProductionsPage:
    // items whose id is in the selected set bubble to the top.
    const selectedIds = new Set([2])
    const transformItems = (items: number[]) =>
      [...items].sort((a, b) => {
        const aMatch = selectedIds.has(a) ? 0 : 1
        const bMatch = selectedIds.has(b) ? 0 : 1
        return aMatch - bMatch
      })

    renderView({
      items: [1, 2, 3],
      layout: 'list',
      getKey: (item) => item,
      renderListItem: (item) => <div data-testid="list-item">{item}</div>,
      renderGridItem: (item) => <div data-testid="grid-item">{item}</div>,
      transformItems,
    })

    const listItems = screen.getAllByTestId('list-item').map((node) => node.textContent)
    expect(listItems).toEqual(['2', '1', '3'])
  })

  it('forces the grid layout on narrow viewports', () => {
    mockNarrowViewport()

    renderView({
      items: [1],
      layout: 'list',
      getKey: (item) => item,
      renderListItem: (item) => <div data-testid="list-item">{item}</div>,
      renderGridItem: (item) => <div data-testid="grid-item">{item}</div>,
    })

    expect(screen.getByTestId('grid-item')).toBeInTheDocument()
    expect(screen.queryByTestId('list-item')).not.toBeInTheDocument()
  })
})