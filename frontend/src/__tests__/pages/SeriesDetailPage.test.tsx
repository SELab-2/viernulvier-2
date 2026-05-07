import '@testing-library/jest-dom'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'

import SeriesDetailPage from '../../pages/SeriesDetailPage'
import { getProductions } from '../../services/productions/Productions'
import { getTag } from '../../services/tags/Tags'

jest.mock('../../services/tags/Tags', () => ({
  getTag: jest.fn(),
}))

jest.mock('../../services/productions/Productions', () => ({
  getProductions: jest.fn(),
}))

jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        'series.loading': 'Reeks laden',
        'series.backToSeries': 'Terug naar reeksen',
        'series.allEditions': 'Alle edities',
        'series.allEditionsSubtitle':
          'Chronologisch overzicht van de producties binnen deze reeks.',
        'series.noProductions': 'Er zijn geen producties gekoppeld aan deze reeks.',
        'series.invalidId': 'Ongeldig reeks-ID.',
        'series.fetchError': 'Kon de reeks niet ophalen.',
        'series.noDescription': 'Geen beschrijving beschikbaar.',
        'series.untitled': 'Naamloze reeks',
        'series.untitledProduction': 'Naamloze productie',
        'series.stats.editions': 'Edities',
        'series.stats.period': 'Periode',
        'series.stats.type': 'Type',
        'nav.home': 'Home',
        'footer.nav.series': 'Reeksen',
      }

      return translations[key] ?? key
    },
    i18n: { language: 'nl' },
  }),
}))

const SeriesPageProbe = () => {
  const location = useLocation()
  const alert = (location.state as { floatingAlert?: { message?: string } } | null)?.floatingAlert

  return (
    <div>
      <div>SERIES PAGE</div>
      <div data-testid="floating-alert-message">{alert?.message ?? ''}</div>
    </div>
  )
}

describe('SeriesDetailPage', () => {
  const mockedGetTag = getTag as jest.Mock
  const mockedGetProductions = getProductions as jest.Mock

  beforeEach(() => {
    mockedGetTag.mockReset()
    mockedGetProductions.mockReset()
  })

  const renderPage = (id = '1') => {
    return render(
      <MemoryRouter initialEntries={[`/nl/reeksen/${id}`]}>
        <Routes>
          <Route path="/:lang/reeksen/:id" element={<SeriesDetailPage />} />
          <Route path="/:lang/reeksen" element={<SeriesPageProbe />} />
          <Route path="/:lang/404" element={<div>NOT FOUND</div>} />
          <Route path="/:lang/producties/:id" element={<div>PRODUCTION DETAIL</div>} />
        </Routes>
      </MemoryRouter>,
    )
  }

  it('shows loading state initially', () => {
    mockedGetTag.mockImplementation(() => new Promise(() => {}))
    mockedGetProductions.mockImplementation(() => new Promise(() => {}))

    renderPage()

    expect(screen.getByTestId('series-detail-skeleton')).toBeInTheDocument()
  })

  it('renders series data when API succeeds', async () => {
    mockedGetTag.mockResolvedValue({
      id: 1,
      name: { nl: 'VIDEODROOM' },
      excerpt: { nl: 'Korte samenvatting' },
      display_excerpt: 'Korte samenvatting',
      short_description: { nl: 'Beschrijving van de reeks' },
      type: 'festival',
    })

    mockedGetProductions.mockResolvedValue({
      results: [
        {
          id: 1,
          display_title: 'VIDEODROOM 2024',
          title: { nl: 'VIDEODROOM 2024' },
          teaser: { nl: 'Beschrijving productie' },
          description: { nl: 'Beschrijving productie' },
          artist_name: { nl: 'Artiest' },
          genres: [],
          tags: [],
        },
      ],
    })

    renderPage()

    expect(await screen.findByRole('heading', { name: 'VIDEODROOM' })).toBeInTheDocument()
    expect(screen.getByText('Korte samenvatting')).toBeInTheDocument()
    expect(screen.getByText('Beschrijving van de reeks')).toBeInTheDocument()
    expect(screen.getByText('VIDEODROOM 2024')).toBeInTheDocument()
    expect(screen.getByText('Alle edities')).toBeInTheDocument()
  })

  it('renders breadcrumb buttons to archive and series overview', async () => {
    mockedGetTag.mockResolvedValue({
      id: 1,
      name: { nl: 'VIDEODROOM' },
      excerpt: { nl: 'Korte samenvatting' },
      display_excerpt: 'Korte samenvatting',
      short_description: { nl: 'Beschrijving van de reeks' },
      type: 'festival',
    })

    mockedGetProductions.mockResolvedValue({
      results: [],
    })

    renderPage()

    await screen.findByRole('heading', { name: 'VIDEODROOM' })

    expect(screen.getByRole('button', { name: 'Home' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Reeksen' })).toBeInTheDocument()
  })

  it('redirects to localized 404 when tag is not found', async () => {
    mockedGetTag.mockResolvedValue(null)
    mockedGetProductions.mockResolvedValue({ results: [] })

    renderPage()

    expect(await screen.findByText('NOT FOUND')).toBeInTheDocument()
  })

  it('redirects to localized 404 when API throws error', async () => {
    mockedGetTag.mockRejectedValue(new Error('API error'))
    mockedGetProductions.mockResolvedValue({ results: [] })

    renderPage()

    expect(await screen.findByText('NOT FOUND')).toBeInTheDocument()
  })

  it('shows empty state when no productions exist', async () => {
    mockedGetTag.mockResolvedValue({
      id: 1,
      name: { nl: 'VIDEODROOM' },
      excerpt: { nl: 'Korte samenvatting' },
      display_excerpt: 'Korte samenvatting',
      short_description: { nl: 'Beschrijving' },
      type: 'festival',
    })

    mockedGetProductions.mockResolvedValue({
      results: [],
    })

    renderPage()

    expect(
      await screen.findByText('Er zijn geen producties gekoppeld aan deze reeks.'),
    ).toBeInTheDocument()
  })

  it('redirects to the series tab when id is invalid', async () => {
    renderPage('invalid')

    await waitFor(() => {
      expect(screen.getByText('SERIES PAGE')).toBeInTheDocument()
    })
    expect(screen.getByTestId('floating-alert-message')).toHaveTextContent('Ongeldig reeks-ID.')
  })

  it('navigates to production detail when a production card is clicked', async () => {
    mockedGetTag.mockResolvedValue({
      id: 1,
      name: { nl: 'VIDEODROOM' },
      excerpt: { nl: 'Korte samenvatting' },
      display_excerpt: 'Korte samenvatting',
      short_description: { nl: 'Beschrijving van de reeks' },
      type: 'festival',
    })

    mockedGetProductions.mockResolvedValue({
      results: [
        {
          id: 42,
          display_title: 'VIDEODROOM 2024',
          title: { nl: 'VIDEODROOM 2024' },
          teaser: { nl: 'Beschrijving productie' },
          description: { nl: 'Beschrijving productie' },
          artist_name: { nl: 'Artiest' },
          genres: [],
          tags: [],
        },
      ],
    })

    renderPage()

    const productionCard = await screen.findByRole('link', { name: /videodroom 2024/i })
    fireEvent.click(productionCard)

    expect(await screen.findByText('PRODUCTION DETAIL')).toBeInTheDocument()
  })

  it('renders production genre chips on the production card when genres have display names', async () => {
    mockedGetTag.mockResolvedValue({
      id: 1,
      name: { nl: 'VIDEODROOM' },
      excerpt: { nl: 'Korte samenvatting' },
      display_excerpt: 'Korte samenvatting',
      short_description: { nl: 'Beschrijving van de reeks' },
      type: 'festival',
    })

    mockedGetProductions.mockResolvedValue({
      results: [
        {
          id: 1,
          display_title: 'VIDEODROOM 2024',
          title: { nl: 'VIDEODROOM 2024' },
          teaser: { nl: 'Beschrijving productie' },
          description: { nl: 'Beschrijving productie' },
          artist_name: { nl: 'Artiest' },
          genres: [
            {
              id: 10,
              type: 'genre',
              name: { nl: 'Audiovisueel', en: 'Audiovisual' },
              display_name: 'Audiovisueel',
              vendor_id: null,
            },
            {
              id: 11,
              type: 'genre',
              name: { nl: 'Performance', en: 'Performance' },
              display_name: 'Performance',
              vendor_id: null,
            },
          ],
          tags: [],
        },
      ],
    })

    renderPage()

    expect(await screen.findByText('Audiovisueel')).toBeInTheDocument()
    expect(screen.getByText('Performance')).toBeInTheDocument()
  })
})
