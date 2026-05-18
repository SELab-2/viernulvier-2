import { beforeEach, describe, expect, it, jest } from '@jest/globals'
import { render, screen, waitFor } from '@testing-library/react'

import Router from '../router'

// Create mock page components
const createMockPage = (testid: string) => () => <div data-testid={testid} />

// Mock the navbar and footer (not lazy loaded in the actual app, but mocked in tests)
jest.mock('../shared/Navbar', () => ({
  __esModule: true,
  default: createMockPage('navbar-mock'),
}))

jest.mock('../shared/Footer', () => ({
  __esModule: true,
  default: createMockPage('footer-mock'),
}))

// Mock the lazily-loaded pages - these need to resolve properly for React.lazy()
jest.mock('../pages/HomePage', () => ({
  __esModule: true,
  default: createMockPage('home-page-mock'),
}))

jest.mock('../features/productions/pages/ProductionsPage', () => ({
  __esModule: true,
  default: createMockPage('productions-page-mock'),
}))

jest.mock('../features/productions/pages/ProductionDetailPage', () => ({
  __esModule: true,
  default: createMockPage('production-detail-page-mock'),
}))

jest.mock('../features/series/pages/SeriesPage', () => ({
  __esModule: true,
  default: createMockPage('series-page-mock'),
}))

jest.mock('../features/series/pages/SeriesDetailPage', () => ({
  __esModule: true,
  default: createMockPage('series-detail-page-mock'),
}))

jest.mock('../features/blogs/pages/BlogsPage', () => ({
  __esModule: true,
  default: createMockPage('blogs-page-mock'),
}))

jest.mock('../features/blogs/pages/BlogDetailPage', () => ({
  __esModule: true,
  default: createMockPage('blog-detail-page-mock'),
}))

jest.mock('../features/media-files/pages/MediaFilesPage', () => ({
  __esModule: true,
  default: createMockPage('media-files-page-mock'),
}))

jest.mock('../pages/NotFoundPage', () => ({
  __esModule: true,
  default: createMockPage('not-found-page-mock'),
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
    expect(await screen.findByTestId('home-page-mock')).toBeInTheDocument()
  })

  it('redirects invalid language prefixes to inferred localized paths', async () => {
    window.history.pushState({}, '', '/xx/archive')

    render(<Router mode="light" onToggleMode={jest.fn()} />)

    await waitFor(() => {
      expect(window.location.pathname).toBe('/en/archive')
    })
    expect(await screen.findByTestId('productions-page-mock')).toBeInTheDocument()
  })

  it('localizes unprefixed paths through the global language redirect', async () => {
    window.history.pushState({}, '', '/archive')

    render(<Router mode="light" onToggleMode={jest.fn()} />)

    await waitFor(() => {
      expect(window.location.pathname).toBe('/en/archive')
    })
    expect(await screen.findByTestId('productions-page-mock')).toBeInTheDocument()
  })

  it('redirects production detail compatibility alias to localized productions detail route', async () => {
    window.history.pushState({}, '', '/nl/productions/42')

    render(<Router mode="light" onToggleMode={jest.fn()} />)

    await waitFor(() => {
      expect(window.location.pathname).toBe('/nl/producties/42')
    })
    expect(await screen.findByTestId('production-detail-page-mock')).toBeInTheDocument()
  })

  it('redirects Dutch series aliases to English series detail route', async () => {
    window.history.pushState({}, '', '/en/reeksen/5')

    render(<Router mode="light" onToggleMode={jest.fn()} />)

    await waitFor(() => {
      expect(window.location.pathname).toBe('/en/series/5')
    })
    expect(await screen.findByTestId('series-detail-page-mock')).toBeInTheDocument()
  })

  it('normalizes invalid language-only roots and falls through to not-found', async () => {
    window.history.pushState({}, '', '/xx')

    render(<Router mode="light" onToggleMode={jest.fn()} />)

    await waitFor(() => {
      expect(window.location.pathname).toBe('/en/404')
    })
    expect(await screen.findByTestId('not-found-page-mock')).toBeInTheDocument()
  })

  it('redirects unknown localized routes to the localized 404 path', async () => {
    window.history.pushState({}, '', '/nl/does-not-exist')

    render(<Router mode="light" onToggleMode={jest.fn()} />)

    await waitFor(() => {
      expect(window.location.pathname).toBe('/nl/404')
    })
    expect(await screen.findByTestId('not-found-page-mock')).toBeInTheDocument()
  })
})
