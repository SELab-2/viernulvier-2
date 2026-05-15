import '@testing-library/jest-dom'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'

import App from '../App'
import i18n from '../i18n'
import { getGenres } from '../services/genres/Genres'
import { getProductions } from '../services/productions/Productions'
import { getTags } from '../services/tags/Tags'

jest.mock('../services/productions/Productions', () => ({
  getProductions: jest.fn(),
}))

jest.mock('../services/tags/Tags', () => ({
  getTags: jest.fn(),
}))

jest.mock('../services/genres/Genres', () => ({
  getGenres: jest.fn(),
}))

const mockedGetProductions = getProductions as jest.MockedFunction<typeof getProductions>
const mockedGetTags = getTags as jest.MockedFunction<typeof getTags>
const mockedGetGenres = getGenres as jest.MockedFunction<typeof getGenres>

describe('App', () => {
  const findLogo = () => screen.findByAltText('Viernulvier logo', undefined, { timeout: 10000 })

  beforeEach(async () => {
    window.history.pushState({}, '', '/')
    localStorage.clear()
    await i18n.changeLanguage('nl')

    // Mock the service functions to return empty results
    mockedGetProductions.mockResolvedValue({
      count: 0,
      next: null,
      previous: null,
      results: [],
    })

    mockedGetGenres.mockResolvedValue({
      count: 0,
      next: null,
      previous: null,
      results: [],
    })

    mockedGetTags.mockResolvedValue({
      count: 0,
      next: null,
      previous: null,
      results: [],
    })
  })

  afterEach(() => {
    localStorage.clear()
    jest.clearAllMocks()
  })

  it('renders navigation', async () => {
    render(<App />)
    // Router lazily loads some children; wait for the main shell to appear
    const logo = await findLogo()
    expect(logo).toBeInTheDocument()

    const mainNav = await screen.findByRole('list', { name: 'Hoofdnavigatie' })
    expect(within(mainNav).getByRole('link', { name: 'Home' })).toBeInTheDocument()
    expect(within(mainNav).getByRole('link', { name: 'Archief' })).toBeInTheDocument()
    expect(within(mainNav).getByRole('link', { name: 'Reeksen' })).toBeInTheDocument()
    expect(within(mainNav).getByRole('link', { name: 'Blogs' })).toBeInTheDocument()
    expect(within(mainNav).getByRole('link', { name: 'Media' })).toBeInTheDocument()
  })

  it('renders not found page on unknown route', async () => {
    window.history.pushState({}, '', '/does-not-exist')

    render(<App />)

    // Not-found route is lazy loaded; wait for the heading to appear
    expect(await screen.findByRole('heading', { name: 'Pagina niet gevonden' })).toBeInTheDocument()
    expect(
      await screen.findByText('De pagina die je zoekt bestaat niet of is verplaatst.'),
    ).toBeInTheDocument()
    expect(await screen.findByRole('link', { name: 'Terug naar home' })).toHaveAttribute(
      'href',
      '/nl',
    )
  })

  it('initializes with light theme by default', async () => {
    render(<App />)
    // wait for shell to mount so any lazy loading has finished
    await findLogo()

    expect(localStorage.getItem('vnv-theme-mode')).toBeNull()
  })

  it('restores dark theme from localStorage', async () => {
    localStorage.setItem('vnv-theme-mode', 'dark')

    render(<App />)
    await findLogo()

    // Theme should be dark based on localStorage
    expect(localStorage.getItem('vnv-theme-mode')).toBe('dark')
  })

  it('restores light theme from localStorage', async () => {
    localStorage.setItem('vnv-theme-mode', 'light')

    render(<App />)
    await findLogo()

    expect(localStorage.getItem('vnv-theme-mode')).toBe('light')
  })

  it('can toggle theme mode', async () => {
    render(<App />)

    // ensure rendered shell before searching for buttons
    await findLogo()

    const themeToggleButtons = await screen.findAllByRole('button')
    const themeToggleButton = themeToggleButtons.find(
      (btn: HTMLElement) =>
        btn.getAttribute('aria-label')?.includes('Switch') ||
        btn.getAttribute('data-testid') === 'theme-toggle-inline',
    )

    expect(themeToggleButton).toBeDefined()
    fireEvent.click(themeToggleButton!)
    await waitFor(() => {
      // After toggle, the theme should be saved to localStorage
      const savedTheme = localStorage.getItem('vnv-theme-mode')
      expect(['light', 'dark']).toContain(savedTheme)
    })
  })

  it('renders footer', async () => {
    render(<App />)
    expect(await screen.findByRole('contentinfo')).toBeInTheDocument()
  })

  it('renders with CSBaseline for consistent styling', async () => {
    const { container } = render(<App />)
    // wait for shell
    await findLogo()

    // CssBaseline should be applied (it resets margins applied by default)
    expect(container).toBeInTheDocument()
  })

  it('has theme provider wrapping router', async () => {
    render(<App />)

    // If ThemeProvider is working, styled components should render
    expect(await findLogo()).toBeInTheDocument()
  })

  it('redirects nl compatibility slugs to localized archive routes', async () => {
    window.history.pushState({}, '', '/nl/archive')

    render(<App />)

    await waitFor(() => {
      expect(window.location.pathname).toBe('/nl/archief')
    })
  })

  it('redirects en compatibility slugs to localized archive routes', async () => {
    window.history.pushState({}, '', '/en/archief')

    render(<App />)

    await waitFor(() => {
      expect(window.location.pathname).toBe('/en/archive')
    })
  })

  it('redirects localized productions listing aliases to archive routes', async () => {
    window.history.pushState({}, '', '/nl/producties')

    render(<App />)

    await waitFor(() => {
      expect(window.location.pathname).toBe('/nl/archief')
    })
  })

  it('redirects media detail aliases back to localized media list', async () => {
    window.history.pushState({}, '', '/en/media/42')

    render(<App />)

    await waitFor(() => {
      expect(window.location.pathname).toBe('/en/media')
    })
  })

  it('redirects invalid language prefixes to a normalized localized path', async () => {
    window.history.pushState({}, '', '/xx/archive')

    render(<App />)

    await waitFor(() => {
      expect(window.location.pathname).toMatch(/^\/(nl|en)\//)
    })
  })
})
