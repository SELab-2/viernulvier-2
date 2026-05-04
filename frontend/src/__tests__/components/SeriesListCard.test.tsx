import { ThemeProvider, createTheme } from '@mui/material/styles'
import { act, render, screen } from '@testing-library/react'
import { I18nextProvider } from 'react-i18next'
import { MemoryRouter } from 'react-router-dom'

import SeriesListCard from '../../components/series/SeriesListCard'
import i18n from '../../i18n'
import { toLocalizedPath } from '../../utils/localizedRoutes'

import type { Tag } from '../../types/Tags'

const renderCard = (tag: Tag) =>
  render(
    <MemoryRouter>
      <I18nextProvider i18n={i18n}>
        <ThemeProvider theme={createTheme()}>
          <SeriesListCard tag={tag} />
        </ThemeProvider>
      </I18nextProvider>
    </MemoryRouter>,
  )

const buildTag = (): Tag => ({
  id: 10,
  url: '',
  source: 'system',
  type: 'series',
  is_enabled: true,
  image: 'https://example.test/series.jpg',
  display_name: 'Reeks Alpha',
  display_short_description: 'Een reeks voor testing',
  display_excerpt: 'Een korte samenvatting',
  display_url_title: null,
  first_production_start: '2026-01-01T19:00:00Z',
  last_production_end: '2026-01-31T20:00:00Z',
  name: { nl: 'Reeks Alpha', en: 'Series Alpha' },
  excerpt: { nl: 'Een korte samenvatting', en: 'A short summary' },
  short_description: { nl: 'Een reeks voor testing', en: 'A series for testing' },
  url_title: null,
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
    renderCard(buildTag())

    expect(screen.getByRole('heading', { name: 'Reeks Alpha' })).toBeInTheDocument()
    expect(screen.getByText('Een korte samenvatting')).toBeInTheDocument()
    expect(screen.getByText('1 jan 2026 - 31 jan 2026')).toBeInTheDocument()
    expect(screen.getByRole('link')).toHaveAttribute('href', toLocalizedPath('/series/10', 'nl'))
    expect(screen.getByRole('img', { name: 'Reeks Alpha' })).toHaveAttribute(
      'src',
      'https://example.test/series.jpg',
    )
  })
})
