import { render, screen, waitFor } from '@testing-library/react'

import Router from '../router'

jest.mock('../components/Navbar', () => ({
  __esModule: true,
  default: () => <div data-testid="navbar-mock" />,
}))

jest.mock('../components/Footer', () => ({
  __esModule: true,
  default: () => <div data-testid="footer-mock" />,
}))

jest.mock('../pages/HomePage', () => ({
  __esModule: true,
  default: () => <div data-testid="home-page-mock" />,
}))

jest.mock('../features/productions/pages/ProductionsPage', () => ({
  __esModule: true,
  default: () => <div data-testid="productions-page-mock" />,
}))

jest.mock('../features/productions/pages/ProductionDetailPage', () => ({
  __esModule: true,
  default: () => <div data-testid="production-detail-page-mock" />,
}))

jest.mock('../features/series/pages/SeriesPage', () => ({
  __esModule: true,
  default: () => <div data-testid="series-page-mock" />,
}))

jest.mock('../features/series/pages/SeriesDetailPage', () => ({
  __esModule: true,
  default: () => <div data-testid="series-detail-page-mock" />,
}))

jest.mock('../features/blogs/pages/BlogsPage', () => ({
  __esModule: true,
  default: () => <div data-testid="blogs-page-mock" />,
}))

jest.mock('../features/blogs/pages/BlogDetailPage', () => ({
  __esModule: true,
  default: () => <div data-testid="blog-detail-page-mock" />,
}))

jest.mock('../features/media-files/pages/MediaFilesPage', () => ({
  __esModule: true,
  default: () => <div data-testid="media-files-page-mock" />,
}))

jest.mock('../pages/NotFoundPage', () => ({
  __esModule: true,
  default: () => <div data-testid="not-found-page-mock" />,
}))

describe('Router', () => {
  beforeEach(() => {
    window.scrollTo = jest.fn()
  })

  it('redirects root to the default localized home path', async () => {
    window.history.pushState({}, '', '/')

    render(<Router mode="light" onToggleMode={jest.fn()} />)

    await waitFor(() => {
      expect(window.location.pathname).toBe('/nl')
    })
    expect(screen.getByTestId('home-page-mock')).toBeInTheDocument()
  })

  it('redirects invalid language prefixes to inferred localized paths', async () => {
    window.history.pushState({}, '', '/xx/archive')

    render(<Router mode="light" onToggleMode={jest.fn()} />)

    await waitFor(() => {
      expect(window.location.pathname).toBe('/en/archive')
    })
    expect(screen.getByTestId('productions-page-mock')).toBeInTheDocument()
  })

  it('localizes unprefixed paths through the global language redirect', async () => {
    window.history.pushState({}, '', '/archive')

    render(<Router mode="light" onToggleMode={jest.fn()} />)

    await waitFor(() => {
      expect(window.location.pathname).toBe('/en/archive')
    })
    expect(screen.getByTestId('productions-page-mock')).toBeInTheDocument()
  })

  it('redirects production detail compatibility alias to localized productions detail route', async () => {
    window.history.pushState({}, '', '/nl/productions/42')

    render(<Router mode="light" onToggleMode={jest.fn()} />)

    await waitFor(() => {
      expect(window.location.pathname).toBe('/nl/producties/42')
    })
    expect(screen.getByTestId('production-detail-page-mock')).toBeInTheDocument()
  })

  it('redirects Dutch series aliases to English series detail route', async () => {
    window.history.pushState({}, '', '/en/reeksen/5')

    render(<Router mode="light" onToggleMode={jest.fn()} />)

    await waitFor(() => {
      expect(window.location.pathname).toBe('/en/series/5')
    })
    expect(screen.getByTestId('series-detail-page-mock')).toBeInTheDocument()
  })

  it('normalizes invalid language-only roots and falls through to not-found', async () => {
    window.history.pushState({}, '', '/xx')

    render(<Router mode="light" onToggleMode={jest.fn()} />)

    await waitFor(() => {
      expect(window.location.pathname).toBe('/en/xx')
    })
    expect(screen.getByTestId('not-found-page-mock')).toBeInTheDocument()
  })
})
