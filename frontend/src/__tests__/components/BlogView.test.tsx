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

jest.mock('../../features/blogs/components/BlogGrid', () => ({
  __esModule: true,
  default: ({ blogs }: { blogs: Array<{ id: number }> }) => (
    <div data-testid="blog-grid">grid:{blogs.length}</div>
  ),
}))

jest.mock('../../features/blogs/components/BlogList', () => ({
  __esModule: true,
  default: ({ blogs }: { blogs: Array<{ id: number }> }) => (
    <div data-testid="blog-list">list:{blogs.length}</div>
  ),
}))

import BlogView from '../../shared/components/BlogView'

describe('BlogView', () => {
  it('renders list on wide viewports when layout=list', () => {
    useMediaQueryMock.mockReturnValue(false)

    render(<BlogView blogs={[{ id: 1 } as never]} layout="list" />)

    expect(screen.getByTestId('blog-list')).toHaveTextContent('list:1')
    expect(screen.queryByTestId('blog-grid')).not.toBeInTheDocument()
  })

  it('renders grid when layout=grid on wide viewports', () => {
    useMediaQueryMock.mockReturnValue(false)

    render(<BlogView blogs={[{ id: 1 }, { id: 2 }] as never} layout="grid" />)

    expect(screen.getByTestId('blog-grid')).toHaveTextContent('grid:2')
  })

  it('forces grid on small screens and defaults layout to list otherwise', () => {
    useMediaQueryMock.mockReturnValue(true)
    const { rerender } = render(<BlogView blogs={[{ id: 1 } as never]} layout="list" />)

    expect(screen.getByTestId('blog-grid')).toBeInTheDocument()

    useMediaQueryMock.mockReturnValue(false)
    rerender(<BlogView blogs={[{ id: 1 } as never]} />)
    expect(screen.getByTestId('blog-list')).toBeInTheDocument()
  })
})
