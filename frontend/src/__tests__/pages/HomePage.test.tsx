import { beforeEach, describe, expect, it, jest } from '@jest/globals'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import { render, screen } from '@testing-library/react'
import React from 'react'
import { I18nextProvider } from 'react-i18next'
import { MemoryRouter } from 'react-router-dom'

import i18n from '../../i18n'
import HomePage from '../../pages/HomePage'
import { getLandingStats } from '../../services/productions/Productions'

jest.mock('../../services/productions/Productions', () => ({
  getLandingStats: jest.fn(),
}))

const mockedGetLandingStats = getLandingStats as jest.MockedFunction<typeof getLandingStats>

const renderPage = () =>
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
      blogs: 120,
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
      '/nl/archief',
    )
    expect(screen.getByRole('link', { name: 'Bekijk reeksen' }).getAttribute('href')).toBe(
      '/nl/reeksen',
    )
    expect(screen.getByRole('link', { name: 'Lees blogs' }).getAttribute('href')).toBe('/nl/blogs')
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
      blogs: 121,
    })

    renderPage()

    expect(await screen.findByText('1.234+')).toBeTruthy()
    expect(screen.getByText('81+')).toBeTruthy()
    expect(screen.getByText('36+')).toBeTruthy()
    expect(screen.getByText('121+')).toBeTruthy()
  })
})
