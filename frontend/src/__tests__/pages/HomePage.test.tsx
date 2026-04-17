import { beforeEach, describe, expect, it, jest } from '@jest/globals'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import { render, screen } from '@testing-library/react'
import { I18nextProvider } from 'react-i18next'
import { MemoryRouter } from 'react-router-dom'

import i18n from '../../i18n'
import HomePage from '../../pages/HomePage'
import { getLandingStats } from '../../services/productions/Productions'

jest.mock('../../services/productions/Productions', () => ({
  getLandingStats: jest.fn(),
}))

const mockedGetLandingStats = getLandingStats as jest.MockedFunction<typeof getLandingStats>

const buildProduction = (id: number): Production => ({
  id,
  attendance_mode: 'offline',
  performer_type: 'solo',
  first_event_start: '2026-01-01T19:00:00Z',
  last_event_end: '2026-01-01T20:00:00Z',
  media_gallery: { id: 0, name: null, media_items: [] },
  uit_database_type: null,
  display_title: `Production ${id}`,
  display_artist_name: null,
  title: { nl: `Productie ${id}` },
  artist_name: {},
  tagline: {},
  teaser: {},
  description: {},
  tags: [],
  genres: [],
})

const renderPage = (
  initialEntry:
    | string
    | { pathname: string; state?: { floatingAlert?: { open?: boolean; message?: string } } } = '/',
) =>
  render(
    <MemoryRouter>
      <I18nextProvider i18n={i18n}>
        <ThemeProvider theme={createTheme()}>
          <HomePage />
        </ThemeProvider>
      </I18nextProvider>
    </MemoryRouter>,
  )

describe('HomePage', () => {
  beforeEach(async () => {
    mockedGetLandingStats.mockResolvedValue({
      productions: 1200,
      series: 80,
      years: 35,
      stories: 120,
    })

    await i18n.changeLanguage('nl')
  })

  it('renders the landing hero and archive links', async () => {
    renderPage()

    expect(await screen.findByText('1.200+')).toBeTruthy()

    expect(
      screen.getByRole('heading', {
        name: 'Het levende archief van VIERNULVIER.',
      }),
    ).toBeTruthy()
    expect(screen.getByRole('link', { name: 'Open het archief' }).getAttribute('href')).toBe(
      '/archive',
    )
    expect(screen.getByRole('link', { name: 'Bekijk reeksen' }).getAttribute('href')).toBe(
      '/series',
    )
    expect(screen.getByRole('link', { name: 'Lees verhalen' }).getAttribute('href')).toBe('/blogs')
    expect(screen.getByRole('heading', { name: 'Ontdek reeksen' })).toBeTruthy()
  })

  it('renders equally tall entry cards', async () => {
    const { container } = renderPage()

    expect(await screen.findByText('1.200+')).toBeTruthy()

    const cardLinks = Array.from(container.querySelectorAll('a[href]')).filter((link) =>
      Boolean(link.querySelector('h3')),
    )

    expect(cardLinks).toHaveLength(4)
    cardLinks.forEach((link) => {
      expect(window.getComputedStyle(link).minHeight).toBe('200px')
    })
  })

  it('renders homepage stats from API data', async () => {
    mockedGetLandingStats.mockResolvedValueOnce({
      productions: 1234,
      series: 81,
      years: 36,
      stories: 121,
    })

    renderPage()

    expect(await screen.findByText('1.234+')).toBeTruthy()
    expect(screen.getByText('81+')).toBeTruthy()
    expect(screen.getByText('36+')).toBeTruthy()
    expect(screen.getByText('121+')).toBeTruthy()
  })
})
