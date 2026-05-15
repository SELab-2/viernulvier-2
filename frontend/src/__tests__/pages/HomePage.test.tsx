import { beforeEach, describe, expect, it, jest } from '@jest/globals'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import React from 'react'
import { I18nextProvider } from 'react-i18next'
import { MemoryRouter, useLocation } from 'react-router-dom'

import i18n from '../../i18n'
import HomePage from '../../pages/HomePage'
import { getLandingStats } from '../../services/productions/Productions'

// Mock

jest.mock('../../services/productions/Productions', () => ({
  getLandingStats: jest.fn(),
}))

const mockedGetLandingStats = getLandingStats as jest.MockedFunction<typeof getLandingStats>

// Helpers

const LocationProbe = () => {
  const location = useLocation()
  return <div data-testid="location-probe">{`${location.pathname}${location.search}`}</div>
}

const renderPage = (initialPath = '/nl') =>
  render(
    <MemoryRouter initialEntries={[initialPath]}>
      <I18nextProvider i18n={i18n}>
        <ThemeProvider theme={createTheme()}>
          <HomePage />
          <LocationProbe />
        </ThemeProvider>
      </I18nextProvider>
    </MemoryRouter>,
  )

/** Wait until the API response has been painted. */
const waitForStats = () => screen.findByText('1.200+')

// Suite

describe('HomePage', () => {
  beforeEach(async () => {
    mockedGetLandingStats.mockResolvedValue({
      productions: 1200,
      series: 80,
      years: 35,
      blogs: 120,
    })
    await i18n.changeLanguage('nl')
  })

  // Hero

  describe('hero section', () => {
    it('renders the eyebrow label', async () => {
      renderPage()
      await waitForStats()
      expect(screen.getByText('VIERNULVIER-ARCHIEF')).toBeTruthy()
    })

    it('renders the h1 title', async () => {
      renderPage()
      await waitForStats()
      expect(
        screen.getByRole('heading', { level: 1, name: 'Het levende archief van VIERNULVIER.' }),
      ).toBeTruthy()
    })

    it('renders the description', async () => {
      renderPage()
      await waitForStats()
      expect(screen.getByText(/Verken decennia aan voorstellingen/)).toBeTruthy()
    })

    it('primary CTA links to the localized archive', async () => {
      renderPage()
      await waitForStats()
      // Exact name match finds only the hero button - the archive card link's
      // accessible name includes eyebrow + title + cta combined.
      expect(screen.getByRole('link', { name: 'Open het archief' }).getAttribute('href')).toBe(
        '/nl/archief',
      )
    })

    it('series CTA links to the localized series page', async () => {
      renderPage()
      await waitForStats()
      expect(screen.getByRole('link', { name: 'Bekijk reeksen' }).getAttribute('href')).toBe(
        '/nl/reeksen',
      )
    })

    it('website CTA links to viernulvier.gent and opens in a new tab', async () => {
      renderPage()
      await waitForStats()
      const link = screen.getByRole('link', { name: /Bezoek de officiële website/ })
      expect(link.getAttribute('href')).toBe('https://www.viernulvier.gent/')
      expect(link.getAttribute('target')).toBe('_blank')
      expect(link.getAttribute('rel')).toBe('noopener noreferrer')
    })
  })

  // Search

  describe('search', () => {
    it('navigates to the archive with the encoded query', async () => {
      renderPage()
      await waitForStats()

      fireEvent.change(screen.getByRole('textbox'), {
        target: { value: '  opera voor morgen  ' },
      })
      fireEvent.click(screen.getByRole('button', { name: 'Zoeken' }))

      await waitFor(() => {
        expect(screen.getByTestId('location-probe').textContent).toBe(
          '/nl/archief?q=opera%20voor%20morgen',
        )
      })
    })

    it('strips surrounding whitespace before encoding the query', async () => {
      renderPage()
      await waitForStats()

      fireEvent.change(screen.getByRole('textbox'), { target: { value: '   dans   ' } })
      fireEvent.click(screen.getByRole('button', { name: 'Zoeken' }))

      await waitFor(() => {
        expect(screen.getByTestId('location-probe').textContent).toBe('/nl/archief?q=dans')
      })
    })

    it('navigates to the archive root when the query is blank', async () => {
      renderPage()
      await waitForStats()

      fireEvent.click(screen.getByRole('button', { name: 'Zoeken' }))

      await waitFor(() => {
        expect(screen.getByTestId('location-probe').textContent).toBe('/nl/archief')
      })
    })

    it('navigates to the archive root when the query is only whitespace', async () => {
      renderPage()
      await waitForStats()

      fireEvent.change(screen.getByRole('textbox'), { target: { value: '   ' } })
      fireEvent.click(screen.getByRole('button', { name: 'Zoeken' }))

      await waitFor(() => {
        expect(screen.getByTestId('location-probe').textContent).toBe('/nl/archief')
      })
    })
  })

  // Stats bar

  describe('stats bar', () => {
    it('shows a dash placeholder while the API call is in flight', () => {
      // Never resolve so we observe the loading state
      mockedGetLandingStats.mockReturnValue(new Promise(() => {}))
      renderPage()
      // archiveStats starts as {} so every value is undefined -> '-'
      expect(screen.getAllByText('-')).toHaveLength(4)
    })

    it('displays live counts from the API formatted with the nl-BE locale', async () => {
      mockedGetLandingStats.mockResolvedValueOnce({
        productions: 1234,
        series: 81,
        years: 36,
        blogs: 121,
      })
      renderPage()

      // nl-BE uses a period as the thousands separator
      expect(await screen.findByText('1.234+')).toBeTruthy()
      expect(screen.getByText('81+')).toBeTruthy()
      expect(screen.getByText('36+')).toBeTruthy()
      expect(screen.getByText('121+')).toBeTruthy()
    })

    it('shows a dash for any stat value that is zero or negative', async () => {
      mockedGetLandingStats.mockResolvedValueOnce({
        productions: 0,
        series: -1,
        years: 0,
        blogs: 0,
      })
      renderPage()

      await waitFor(() => expect(mockedGetLandingStats).toHaveBeenCalledTimes(1))
      // All four cells <= 0 -> '-'; '0+' or '-1+' must never appear
      expect(screen.getAllByText('-')).toHaveLength(4)
      expect(screen.queryByText('0+')).toBeNull()
      expect(screen.queryByText('-1+')).toBeNull()
    })

    it('shows a dash for all stats when the API call fails', async () => {
      mockedGetLandingStats.mockRejectedValueOnce(new Error('stats down'))
      renderPage()

      // On error archiveStats resets to {} -> all undefined -> '-'
      await waitFor(() => expect(mockedGetLandingStats).toHaveBeenCalledTimes(1))
      expect(screen.getAllByText('-')).toHaveLength(4)
    })

    it('renders all four translated stat labels', async () => {
      renderPage()
      await waitForStats()

      expect(screen.getByText('Producties')).toBeTruthy()
      expect(screen.getByText('Reeksen')).toBeTruthy()
      expect(screen.getByText('Gedocumenteerde jaren')).toBeTruthy()
      expect(screen.getByText('Blogs')).toBeTruthy()
    })
  })

  // Cards section

  describe('cards section', () => {
    it('renders the section h2 heading', async () => {
      renderPage()
      await waitForStats()
      expect(screen.getByRole('heading', { level: 2, name: 'Ontdek de collectie' })).toBeTruthy()
    })

    it('renders all four card h3 headings', async () => {
      renderPage()
      await waitForStats()

      expect(screen.getByRole('heading', { level: 3, name: 'Verken het archief' })).toBeTruthy()
      expect(screen.getByRole('heading', { level: 3, name: 'Ontdek reeksen' })).toBeTruthy()
      expect(screen.getByRole('heading', { level: 3, name: 'Lees de blogs' })).toBeTruthy()
      expect(screen.getByRole('heading', { level: 3, name: 'Ontdek drukwerk' })).toBeTruthy()
    })

    it('renders exactly four card links', async () => {
      const { container } = renderPage()
      await waitForStats()
      // Each card is an <a> wrapping an <h3>
      expect(container.querySelectorAll('a[href] h3')).toHaveLength(4)
    })

    it.each([
      ['Verken het archief', '/nl/archief'],
      ['Ontdek reeksen', '/nl/reeksen'],
      ['Lees de blogs', '/nl/blogs'],
      ['Ontdek drukwerk', '/nl/media'],
    ])('"%s" card links to %s', async (cardTitle, expectedHref) => {
      renderPage()
      await waitForStats()
      // Traverse from h3 to its wrapping <a> - avoids brittle accessible-name
      // matching because the link includes eyebrow + title + cta all combined.
      const heading = screen.getByRole('heading', { level: 3, name: cardTitle })
      expect(heading.closest('a')?.getAttribute('href')).toBe(expectedHref)
    })

    it('card images carry alt text matching their card title', async () => {
      renderPage()
      await waitForStats()

      expect(screen.getByAltText('Verken het archief')).toBeTruthy()
      expect(screen.getByAltText('Ontdek reeksen')).toBeTruthy()
      expect(screen.getByAltText('Lees de blogs')).toBeTruthy()
      expect(screen.getByAltText('Ontdek drukwerk')).toBeTruthy()
    })
  })
})
