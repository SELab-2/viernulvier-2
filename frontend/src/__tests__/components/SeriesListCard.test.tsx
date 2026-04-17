import { ThemeProvider, createTheme } from '@mui/material/styles'
import { act, render, screen } from '@testing-library/react'
import { I18nextProvider } from 'react-i18next'
import { MemoryRouter } from 'react-router-dom'

import SeriesListCard from '../../components/series/SeriesListCard'
import i18n from '../../i18n'

import type { Series } from '../../types/Series'

const renderCard = (series: Series) =>
  render(
    <MemoryRouter>
      <I18nextProvider i18n={i18n}>
        <ThemeProvider theme={createTheme()}>
          <SeriesListCard series={series} />
        </ThemeProvider>
      </I18nextProvider>
    </MemoryRouter>,
  )

const buildSeries = (): Series => ({
  tag: {
    id: 10,
    url: '',
    source: 'system',
    type: 'series',
    is_enabled: true,
    display_name: 'Reeks Alpha',
    display_short_description: 'Een reeks voor testing',
    display_url_title: null,
    name: { nl: 'Reeks Alpha', en: 'Series Alpha' },
    short_description: { nl: 'Een reeks voor testing', en: 'A series for testing' },
    url_title: null,
  },
  firstProductionStart: '2026-01-01T19:00:00Z',
  lastProductionEnd: '2026-01-31T20:00:00Z',
  lastProductionImage: 'https://example.test/series.jpg',
})

describe('SeriesListCard', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('nl')
  })

  afterEach(async () => {
    await act(async () => {
      await i18n.changeLanguage('nl')
    })
  })

  it('renders the localized title, description, date range, image, and detail link', () => {
    renderCard(buildSeries())

    expect(screen.getByRole('heading', { name: 'Reeks Alpha' })).toBeInTheDocument()
    expect(screen.getByText('Een reeks voor testing')).toBeInTheDocument()
    expect(screen.getByText('1 jan 2026 - 31 jan 2026')).toBeInTheDocument()
    expect(screen.getByRole('link')).toHaveAttribute('href', '/series/10')
    expect(screen.getByRole('img', { name: 'Reeks Alpha' })).toHaveAttribute(
      'src',
      'https://example.test/series.jpg',
    )
  })
})
