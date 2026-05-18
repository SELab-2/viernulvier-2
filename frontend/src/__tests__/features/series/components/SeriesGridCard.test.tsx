import { ThemeProvider, createTheme } from '@mui/material/styles'
import { act, render, screen } from '@testing-library/react'
import { I18nextProvider } from 'react-i18next'
import { MemoryRouter } from 'react-router-dom'

import SeriesGridCard from '../../../../features/series/components/SeriesGridCard'
import i18n from '../../../../i18n'
import { toLocalizedPath } from '../../../../utils/localizedRoutes'

import type { Tag } from '../../../../types/Tags'

const renderCard = (tag: Tag) =>
  render(
    <MemoryRouter>
      <I18nextProvider i18n={i18n}>
        <ThemeProvider theme={createTheme()}>
          <SeriesGridCard tag={tag} />
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

describe('SeriesGridCard', () => {
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

  it('uses English labels and strips HTML from excerpts', async () => {
    await i18n.changeLanguage('en')

    renderCard({
      ...buildTag(),
      excerpt: { en: '<p>A <strong>short</strong> summary</p>' },
    })

    expect(screen.getByRole('heading', { name: 'Series Alpha' })).toBeInTheDocument()
    expect(screen.getByText('A short summary')).toBeInTheDocument()
    expect(screen.getByRole('link')).toHaveAttribute('href', toLocalizedPath('/series/10', 'en'))
  })

  it('falls back to display labels and hides missing optional metadata', () => {
    renderCard({
      ...buildTag(),
      image: null,
      name: null,
      excerpt: null,
      display_name: 'Display reeks',
      display_excerpt: null,
      first_production_start: null,
      last_production_end: null,
    })

    expect(screen.getByRole('heading', { name: 'Display reeks' })).toBeInTheDocument()
    expect(screen.getByAltText('Fallback image')).toBeInTheDocument()
    expect(screen.getByText('Geen samenvatting beschikbaar.')).toBeInTheDocument()
    expect(screen.queryByText(/2026/)).not.toBeInTheDocument()
  })


  it('renders a single date when the start and end labels are equal or only one side exists', () => {
    const { rerender } = renderCard({
      ...buildTag(),
      first_production_start: '2026-01-01T19:00:00Z',
      last_production_end: '2026-01-01T21:00:00Z',
    })

    expect(screen.getByText('1 jan 2026')).toBeInTheDocument()
    expect(screen.queryByText(/ - /)).not.toBeInTheDocument()

    rerender(
      <MemoryRouter>
        <I18nextProvider i18n={i18n}>
          <ThemeProvider theme={createTheme()}>
            <SeriesGridCard
              tag={{
                ...buildTag(),
                first_production_start: null,
                last_production_end: '2026-01-31T20:00:00Z',
              }}
            />
          </ThemeProvider>
        </I18nextProvider>
      </MemoryRouter>,
    )

    expect(screen.getByText('31 jan 2026')).toBeInTheDocument()
  })
})
