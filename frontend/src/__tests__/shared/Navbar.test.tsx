import { beforeEach, describe, expect, it, jest } from '@jest/globals'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import Navbar from '../../shared/Navbar'
import i18n from '../../i18n'

const renderNavbar = (
  initialPath = '/',
  options: { mode?: 'light' | 'dark'; onToggleMode?: jest.Mock } = {},
) =>
  render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Navbar mode={options.mode ?? 'light'} onToggleMode={options.onToggleMode ?? jest.fn()} />
    </MemoryRouter>,
  )

beforeEach(() => {
  i18n.changeLanguage('nl')
})

describe('Navbar', () => {
  it('renders the brand logo and Archive label', () => {
    renderNavbar()
    expect(screen.getByAltText('Viernulvier logo')).toBeInTheDocument()
    expect(screen.getByText('/ Archive')).toBeInTheDocument()
  })

  it('renders all navigation links', () => {
    renderNavbar()
    expect(screen.getByRole('link', { name: 'Home' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Archief' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Reeksen' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Blogs' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Media' })).toBeInTheDocument()
  })

  it('marks the active route with aria-current="page"', () => {
    renderNavbar('/nl/archief')
    expect(screen.getByRole('link', { name: 'Archief' })).toHaveAttribute('aria-current', 'page')
    expect(screen.getByRole('link', { name: 'Home' })).not.toHaveAttribute('aria-current')
  })

  it('keeps Archive active on production detail routes', () => {
    renderNavbar('/nl/productions/123')
    expect(screen.getByRole('link', { name: 'Archief' })).toHaveAttribute('aria-current', 'page')
  })

  it('shows target language and toggles to it when clicking the language button', () => {
    renderNavbar()
    const langButton = screen.getByTestId('language-toggle-inline')
    expect(screen.getByRole('link', { name: 'Home' })).toHaveAttribute('href', '/nl')
    expect(langButton).toHaveTextContent('EN')
    fireEvent.click(langButton)
    expect(screen.getByRole('link', { name: 'Home' })).toHaveAttribute('href', '/en')
    expect(screen.getByTestId('language-toggle-inline')).toHaveTextContent('NL')
  })

  it('calls toggle callback when clicking inline theme switch', () => {
    const onToggleMode = jest.fn()
    renderNavbar('/', { onToggleMode })
    fireEvent.click(screen.getByTestId('theme-toggle-inline'))
    expect(onToggleMode).toHaveBeenCalledTimes(1)
  })

  it('opens the slide-down menu from the mobile trigger', () => {
    renderNavbar()
    expect(screen.queryByTestId('mobile-nav-panel')).not.toBeInTheDocument()
    fireEvent.click(screen.getByTestId('mobile-menu-trigger'))
    expect(screen.getByTestId('mobile-nav-panel')).toBeInTheDocument()
    expect(screen.getByTestId('mobile-menu-trigger')).toHaveAttribute('aria-label', 'Menu sluiten')
  })

  it('closes the mobile panel after navigating to another route', async () => {
    renderNavbar()
    fireEvent.click(screen.getByTestId('mobile-menu-trigger'))
    const mobilePanel = screen.getByTestId('mobile-nav-panel')
    fireEvent.click(within(mobilePanel).getByRole('link', { name: 'Reeksen' }))

    await waitFor(() => {
      expect(screen.getByTestId('mobile-menu-trigger')).toHaveAttribute('aria-label', 'Menu openen')
    })
    expect(
      screen.getAllByRole('link', { name: 'Reeksen', current: 'page' }).length,
    ).toBeGreaterThan(0)
  })
})
