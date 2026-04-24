import '@testing-library/jest-dom'
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
    }),
    useMediaQuery: () => useMediaQueryMock(),
  }
})

jest.mock('../../../components/media-files/MediaFileGrid', () => ({
  __esModule: true,
  default: ({ mediaFiles }: { mediaFiles: Array<{ id: number }> }) => (
    <div data-testid="grid-view">grid:{mediaFiles.length}</div>
  ),
}))

jest.mock('../../../components/media-files/MediaFileList', () => ({
  __esModule: true,
  default: ({ mediaFiles }: { mediaFiles: Array<{ id: number }> }) => (
    <div data-testid="list-view">list:{mediaFiles.length}</div>
  ),
}))

import MediaFileView from '../../../components/media-files/MediaFileView'

describe('MediaFileView', () => {
  it('renders the requested list layout on desktop', () => {
    useMediaQueryMock.mockReturnValue(false)

    render(<MediaFileView mediaFiles={[{ id: 1 } as never]} layout="list" />)

    expect(screen.getByTestId('list-view')).toHaveTextContent('list:1')
  })

  it('renders the grid layout when explicitly requested on desktop', () => {
    useMediaQueryMock.mockReturnValue(false)

    render(<MediaFileView mediaFiles={[{ id: 1 }, { id: 2 }] as never} layout="grid" />)

    expect(screen.getByTestId('grid-view')).toHaveTextContent('grid:2')
  })

  it('defaults to list layout on desktop when no layout is provided', () => {
    useMediaQueryMock.mockReturnValue(false)

    render(<MediaFileView mediaFiles={[{ id: 1 } as never]} />)

    expect(screen.getByTestId('list-view')).toHaveTextContent('list:1')
  })

  it('forces grid layout on small screens even when list is requested', () => {
    useMediaQueryMock.mockReturnValue(true)

    render(<MediaFileView mediaFiles={[{ id: 1 } as never]} layout="list" />)

    expect(screen.getByTestId('grid-view')).toBeInTheDocument()
    expect(screen.queryByTestId('list-view')).not.toBeInTheDocument()
  })
})
