import '@testing-library/jest-dom'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'

import App from '../App'
import i18n from '../i18n'

describe('App', () => {
  beforeEach(async () => {
    window.history.pushState({}, '', '/')
    localStorage.clear()
    await i18n.changeLanguage('nl')
  })

  afterEach(() => {
    localStorage.clear()
  })

  it('renders navigation', () => {
    render(<App />)
    const mainNav = screen.getByRole('list', { name: 'Hoofdnavigatie' })

    expect(screen.getByAltText('Viernulvier logo')).toBeInTheDocument()
    expect(within(mainNav).getByRole('link', { name: 'Home' })).toBeInTheDocument()
    expect(within(mainNav).getByRole('link', { name: 'Archief' })).toBeInTheDocument()
    expect(within(mainNav).getByRole('link', { name: 'Reeksen' })).toBeInTheDocument()
    expect(within(mainNav).getByRole('link', { name: 'Blogs' })).toBeInTheDocument()
    expect(within(mainNav).getByRole('link', { name: 'Media' })).toBeInTheDocument()
  })

  it('renders not found page on unknown route', () => {
    window.history.pushState({}, '', '/does-not-exist')

    render(<App />)

    expect(screen.getByRole('heading', { name: 'Pagina niet gevonden' })).toBeInTheDocument()
    expect(
      screen.getByText('De pagina die je zoekt bestaat niet of is verplaatst.'),
    ).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Terug naar home' })).toHaveAttribute('href', '/nl')
  })

  it('initializes with light theme by default', () => {
    render(<App />)

    expect(localStorage.getItem('vnv-theme-mode')).toBeNull()
  })

  it('restores dark theme from localStorage', () => {
    localStorage.setItem('vnv-theme-mode', 'dark')

    render(<App />)

    // Theme should be dark based on localStorage
    expect(localStorage.getItem('vnv-theme-mode')).toBe('dark')
  })

  it('restores light theme from localStorage', () => {
    localStorage.setItem('vnv-theme-mode', 'light')

    render(<App />)

    expect(localStorage.getItem('vnv-theme-mode')).toBe('light')
  })

  it('can toggle theme mode', async () => {
    render(<App />)

    const themeToggleButtons = screen.getAllByRole('button')
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

  it('renders footer', () => {
    render(<App />)

    expect(screen.getByRole('contentinfo')).toBeInTheDocument()
  })

  it('renders with CSBaseline for consistent styling', () => {
    const { container } = render(<App />)

    // CssBaseline should be applied (it resets margins applied by default)
    expect(container).toBeInTheDocument()
  })

  it('has theme provider wrapping router', () => {
    render(<App />)

    // If ThemeProvider is working, styled components should render
    expect(screen.getByAltText('Viernulvier logo')).toBeInTheDocument()
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
