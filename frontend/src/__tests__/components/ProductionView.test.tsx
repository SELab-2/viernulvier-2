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
