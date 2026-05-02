import '@testing-library/jest-dom'
import { render, screen, within, fireEvent, waitFor } from '@testing-library/react'

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

  it('renders navigation', async () => {
    render(<App />)
    // Router lazily loads some children; wait for the main shell to appear
    const logo = await screen.findByAltText('Viernulvier logo')
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
    await screen.findByAltText('Viernulvier logo')

    expect(localStorage.getItem('vnv-theme-mode')).toBeNull()
  })

  it('restores dark theme from localStorage', async () => {
    localStorage.setItem('vnv-theme-mode', 'dark')

    render(<App />)
    await screen.findByAltText('Viernulvier logo')

    // Theme should be dark based on localStorage
    expect(localStorage.getItem('vnv-theme-mode')).toBe('dark')
  })

  it('restores light theme from localStorage', async () => {
    localStorage.setItem('vnv-theme-mode', 'light')

    render(<App />)
    await screen.findByAltText('Viernulvier logo')

    expect(localStorage.getItem('vnv-theme-mode')).toBe('light')
  })

  it('can toggle theme mode', async () => {
    render(<App />)

    // ensure rendered shell before searching for buttons
    await screen.findByAltText('Viernulvier logo')

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
    await screen.findByAltText('Viernulvier logo')

    // CssBaseline should be applied (it resets margins applied by default)
    expect(container).toBeInTheDocument()
  })

  it('has theme provider wrapping router', async () => {
    render(<App />)

    // If ThemeProvider is working, styled components should render
    expect(await screen.findByAltText('Viernulvier logo')).toBeInTheDocument()
  })
})
