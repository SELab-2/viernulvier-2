import { ThemeProvider, createTheme } from '@mui/material/styles'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import type React from 'react'
import EntityView, { type EntityViewProps } from '../../components/entity/EntityView'

const renderView = <T,>(props: EntityViewProps<T>, matches = false) => {
  window.matchMedia = jest.fn().mockImplementation((query: string) => ({
    matches,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  }))

  return render(
    <MemoryRouter>
      <ThemeProvider theme={createTheme()}>
        <EntityView {...props} />
      </ThemeProvider>
    </MemoryRouter>,
  )
}

describe('EntityView', () => {
  afterEach(() => {
    jest.clearAllMocks()
  })

  it('renders the list renderer on wide viewports when layout is list', () => {
    renderView({
      items: [1, 2],
      layout: 'list',
      getKey: (item) => item,
      renderListItem: (item) => <div data-testid={`list-${item}`}>{item}</div>,
      renderGridItem: (item) => <div data-testid={`grid-${item}`}>{item}</div>,
    })

    expect(screen.getByTestId('list-1')).toBeInTheDocument()
    expect(screen.getByTestId('list-2')).toBeInTheDocument()
    expect(screen.queryByTestId('grid-1')).not.toBeInTheDocument()
  })

  it('renders the grid renderer on wide viewports when layout is grid', () => {
    renderView({
      items: [1, 2],
      layout: 'grid',
      getKey: (item) => item,
      renderListItem: (item) => <div data-testid={`list-${item}`}>{item}</div>,
      renderGridItem: (item) => <div data-testid={`grid-${item}`}>{item}</div>,
    })

    expect(screen.getByTestId('grid-1')).toBeInTheDocument()
    expect(screen.getByTestId('grid-2')).toBeInTheDocument()
    expect(screen.queryByTestId('list-1')).not.toBeInTheDocument()
  })

  it('forces the grid renderer on narrow viewports', () => {
    renderView(
      {
        items: [1],
        layout: 'list',
        getKey: (item) => item,
        renderListItem: (item) => <div data-testid={`list-${item}`}>{item}</div>,
        renderGridItem: (item) => <div data-testid={`grid-${item}`}>{item}</div>,
      },
      true,
    )

    expect(screen.getByTestId('grid-1')).toBeInTheDocument()
    expect(screen.queryByTestId('list-1')).not.toBeInTheDocument()
  })
})
