import { describe, expect, it, jest } from '@jest/globals'
import { render, screen } from '@testing-library/react'

const useMediaQueryMock = jest.fn()

jest.mock('@mui/material', () => {
  const actual = jest.requireActual('@mui/material') as Record<string, unknown>
  return {
    ...actual,
    useTheme: () => ({
      breakpoints: {
        down: jest.fn(() => 'mocked-breakpoint'),
      },
      palette: {
        divider: '#e0e0e0',
        background: {
          paper: '#ffffff',
        },
      },
    }),
    useMediaQuery: () => useMediaQueryMock(),
  }
})

import CollectionView from '../../../shared/components/CollectionView'

describe('CollectionView (media files)', () => {
  it('renders the requested list layout on desktop', () => {
    useMediaQueryMock.mockReturnValue(false)

    render(
      <CollectionView
        items={[{ id: 1 } as never]}
        layout="list"
        getKey={(item: { id: number }) => item.id}
        renderListItem={(item: { id: number }) => <div data-testid="list-view">list:{item.id}</div>}
        renderGridItem={(item: { id: number }) => <div data-testid="grid-view">grid:{item.id}</div>}
      />,
    )

    expect(screen.getByTestId('list-view')).toHaveTextContent('list:1')
  })

  it('renders the grid layout when explicitly requested on desktop', () => {
    useMediaQueryMock.mockReturnValue(false)

    render(
      <CollectionView
        items={[{ id: 1 }, { id: 2 }] as never}
        layout="grid"
        getKey={(item: { id: number }) => item.id}
        renderListItem={(item: { id: number }) => <div data-testid="list-view">list:{item.id}</div>}
        renderGridItem={(item: { id: number }) => <div data-testid="grid-view">grid:{item.id}</div>}
      />,
    )

    expect(screen.getAllByTestId('grid-view')).toHaveLength(2)
    expect(screen.getAllByTestId('grid-view')[0]).toHaveTextContent('grid:1')
  })

  it('defaults to list layout on desktop when no layout is provided', () => {
    useMediaQueryMock.mockReturnValue(false)

    render(
      <CollectionView
        items={[{ id: 1 } as never]}
        getKey={(item: { id: number }) => item.id}
        renderListItem={(item: { id: number }) => <div data-testid="list-view">list:{item.id}</div>}
        renderGridItem={(item: { id: number }) => <div data-testid="grid-view">grid:{item.id}</div>}
      />,
    )

    expect(screen.getByTestId('list-view')).toHaveTextContent('list:1')
  })

  it('forces grid layout on small screens even when list is requested', () => {
    useMediaQueryMock.mockReturnValue(true)

    render(
      <CollectionView
        items={[{ id: 1 } as never]}
        layout="list"
        getKey={(item: { id: number }) => item.id}
        renderListItem={(item: { id: number }) => <div data-testid="list-view">list:{item.id}</div>}
        renderGridItem={(item: { id: number }) => <div data-testid="grid-view">grid:{item.id}</div>}
      />,
    )

    expect(screen.getByTestId('grid-view')).toBeInTheDocument()
    expect(screen.queryByTestId('list-view')).not.toBeInTheDocument()
  })
})
