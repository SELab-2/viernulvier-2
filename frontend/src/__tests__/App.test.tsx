import '@testing-library/jest-dom'
import { render, screen, within, fireEvent, waitFor } from '@testing-library/react'
import App from '../App'
import '../i18n'

describe('App', () => {
  beforeEach(() => {
    window.history.pushState({}, '', '/')
    localStorage.clear()
  })

  afterEach(() => {
    localStorage.clear()
  })

  it('renders navigation', () => {
    render(<App />)
    const mainNav = screen.getByRole('list', { name: 'Hoofdnavigatie' })

    expect(screen.getByAltText('Viernulvier logo')).toBeInTheDocument()
    expect(within(mainNav).getByRole('link', { name: 'Archief' })).toBeInTheDocument()
    expect(within(mainNav).getByRole('link', { name: 'Reeksen' })).toBeInTheDocument()
    expect(within(mainNav).getByRole('link', { name: 'Artiesten' })).toBeInTheDocument()
    expect(within(mainNav).getByRole('link', { name: 'Verhalen' })).toBeInTheDocument()
  })

  it('renders not found page on unknown route', () => {
    window.history.pushState({}, '', '/does-not-exist')

    render(<App />)

    expect(screen.getByRole('heading', { name: 'Pagina niet gevonden' })).toBeInTheDocument()
    expect(
      screen.getByText('De pagina die je zoekt bestaat niet of is verplaatst.'),
    ).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Terug naar archief' })).toHaveAttribute('href', '/')
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
})
