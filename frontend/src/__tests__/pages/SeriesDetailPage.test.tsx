import '@testing-library/jest-dom'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import SeriesDetailPage from '../../features/series/pages/SeriesDetailPage'
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
          <Route path="/:lang/producties/:id" element={<div>PRODUCTION DETAIL</div>} />
          <Route path="/:lang/not-found" element={<div>404 PAGE</div>} />
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

  it('redirects to /404 when tag is not found', async () => {
    mockedGetTag.mockResolvedValue(null)
    mockedGetProductions.mockResolvedValue({ results: [] })

    renderPage()

    expect(await screen.findByText('404 PAGE')).toBeInTheDocument()
  })

  it('redirects to /404 when API throws error', async () => {
    mockedGetTag.mockRejectedValue(new Error('API error'))
    mockedGetProductions.mockResolvedValue({ results: [] })

    renderPage()

    expect(await screen.findByText('404 PAGE')).toBeInTheDocument()
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

  it('redirects to /404 when id is invalid', async () => {
    renderPage('invalid')

    await waitFor(() => {
      expect(screen.getByText('404 PAGE')).toBeInTheDocument()
    })
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

  it('sorts productions by event date and groups undated productions last', async () => {
    mockedGetTag.mockResolvedValue({
      id: 1,
      name: null,
      display_name: 'Fallback reeks',
      excerpt: null,
      display_excerpt: null,
      short_description: null,
      display_short_description: null,
      first_production_start: null,
      last_production_end: null,
      type: null,
    })

    mockedGetProductions.mockResolvedValue({
      results: [
        {
          id: 1,
          display_title: 'Zonder datum laag',
          title: { nl: 'Zonder datum laag' },
          teaser: {},
          description: {},
          artist_name: {},
          first_event_start: null,
          last_event_end: null,
          genres: [],
          tags: [],
        },
        {
          id: 2,
          display_title: 'Editie 2024',
          title: { nl: 'Editie 2024' },
          teaser: {},
          description: {},
          artist_name: {},
          first_event_start: '2024-06-01T20:00:00Z',
          last_event_end: null,
          genres: [],
          tags: [],
        },
        {
          id: 3,
          display_title: 'Editie 2025',
          title: { nl: 'Editie 2025' },
          teaser: {},
          description: {},
          artist_name: {},
          first_event_start: '2025-06-01T20:00:00Z',
          last_event_end: null,
          genres: [],
          tags: [],
        },
        {
          id: 4,
          display_title: 'Alleen einddatum',
          title: { nl: 'Alleen einddatum' },
          teaser: {},
          description: {},
          artist_name: {},
          first_event_start: null,
          last_event_end: '2023-06-01T20:00:00Z',
          genres: [],
          tags: [],
        },
        {
          id: 5,
          display_title: 'Zonder datum hoog',
          title: { nl: 'Zonder datum hoog' },
          teaser: {},
          description: {},
          artist_name: {},
          first_event_start: null,
          last_event_end: null,
          genres: [],
          tags: [],
        },
      ],
    })

    renderPage()

    expect(await screen.findByRole('heading', { name: 'Fallback reeks' })).toBeInTheDocument()
    expect(screen.getByText('Geen beschrijving beschikbaar.')).toBeInTheDocument()
    expect(screen.getAllByText('—').length).toBeGreaterThanOrEqual(2)

    const edition2025 = screen.getByRole('heading', { name: 'Editie 2025' })
    const edition2024 = screen.getByRole('heading', { name: 'Editie 2024' })
    const undatedHigh = screen.getByRole('heading', { name: 'Zonder datum hoog' })
    const undatedLow = screen.getByRole('heading', { name: 'Zonder datum laag' })

    expect(screen.getByText('2023')).toBeInTheDocument()
    expect(edition2025.compareDocumentPosition(edition2024)).toBe(Node.DOCUMENT_POSITION_FOLLOWING)
    expect(edition2024.compareDocumentPosition(undatedHigh)).toBe(Node.DOCUMENT_POSITION_FOLLOWING)
    expect(undatedHigh.compareDocumentPosition(undatedLow)).toBe(Node.DOCUMENT_POSITION_FOLLOWING)
  })
})
