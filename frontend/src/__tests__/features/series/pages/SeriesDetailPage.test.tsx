import '@testing-library/jest-dom'
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'

import SeriesDetailPage from '../../../../features/series/pages/SeriesDetailPage'
import { ApiError } from '../../../../services/ApiTypes'
import { getProductions } from '../../../../services/productions/Productions'
import { getTag } from '../../../../services/tags/Tags'

jest.mock('../../../../services/ApiTypes', () => ({
  ApiError: class ApiError extends Error {
    status: number

    constructor(message: string, status: number) {
      super(message)
      this.status = status
    }
  },
}))

jest.mock('../../../../types/FloatingAlertConfig', () => ({
  ALERT_SEVERITIES: {
    error: 'error',
    warning: 'warning',
  },
}))

jest.mock('../../../../utils/navigation', () => ({
  createFloatingAlertState: ({ message, severity }: { message: string; severity: string }) => ({
    floatingAlert: { message, severity },
  }),
}))

jest.mock('../../../../services/tags/Tags', () => ({
  getTag: jest.fn(),
}))

jest.mock('../../../../services/productions/Productions', () => ({
  getProductions: jest.fn(),
}))

jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, fallback?: string) => {
      const translations: Record<string, string> = {
        'common.loading': 'Loading…',
        'series.loading': 'Reeks laden',
        'series.backToSeries': 'Terug naar reeksen',
        'series.allEditions': 'Alle edities',
        'series.allEditionsSubtitle':
          'Chronologisch overzicht van de producties binnen deze reeks.',
        'series.showMore': 'Toon meer',
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

      return translations[key] ?? fallback ?? key
    },
    i18n: { language: 'nl', resolvedLanguage: 'nl' },
  }),
}))

type MockProductionOverrides = Record<string, unknown>

const baseTag = (overrides: Record<string, unknown> = {}) => ({
  id: 1,
  name: { nl: 'VIDEODROOM' },
  excerpt: { nl: 'Korte samenvatting' },
  display_excerpt: 'Korte samenvatting',
  short_description: { nl: 'Beschrijving van de reeks' },
  display_short_description: 'Beschrijving van de reeks',
  first_production_start: '2020-01-01T20:00:00Z',
  last_production_end: '2025-01-01T20:00:00Z',
  type: 'festival',
  ...overrides,
})

const makeProduction = (id: number, overrides: MockProductionOverrides = {}) => ({
  id,
  display_title: `Productie ${id}`,
  title: { nl: `Productie ${id}` },
  teaser: { nl: `Teaser ${id}` },
  description: { nl: `Beschrijving productie ${id}` },
  artist_name: { nl: `Artiest ${id}` },
  display_artist_name: `Artiest ${id}`,
  first_event_start: `2024-01-${String(id).padStart(2, '0')}T20:00:00Z`,
  last_event_end: null,
  genres: [],
  tags: [],
  media_gallery: { media_items: [] },
  ...overrides,
})

const SeriesPageMock = () => {
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
          <Route path="/:lang/reeksen" element={<SeriesPageMock />} />
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

  it('renders series data, statistics and the first page of productions when API succeeds', async () => {
    mockedGetTag.mockResolvedValue(baseTag())
    mockedGetProductions.mockResolvedValue({
      count: 1,
      results: [
        makeProduction(1, {
          display_title: 'VIDEODROOM 2024',
          title: { nl: 'VIDEODROOM 2024' },
        }),
      ],
    })

    renderPage()

    expect(await screen.findByRole('heading', { name: 'VIDEODROOM' })).toBeInTheDocument()
    expect(screen.getByText('Korte samenvatting')).toBeInTheDocument()
    expect(screen.getByText('Beschrijving van de reeks')).toBeInTheDocument()
    expect(screen.getByText('VIDEODROOM 2024')).toBeInTheDocument()
    expect(screen.getByText('Alle edities')).toBeInTheDocument()
    expect(screen.getByText('1')).toBeInTheDocument()
    expect(screen.getByText('2020–2025')).toBeInTheDocument()
    expect(screen.getByText('festival')).toBeInTheDocument()
    expect(mockedGetProductions).toHaveBeenCalledWith({
      page: 1,
      pageSize: 12,
      filters: { tag: 1, ordering: '-first_event_start' },
    })
  })

  it('renders breadcrumb buttons to archive and series overview', async () => {
    mockedGetTag.mockResolvedValue(baseTag())
    mockedGetProductions.mockResolvedValue({ count: 0, results: [] })

    renderPage()

    await screen.findByRole('heading', { name: 'VIDEODROOM' })

    expect(screen.getByRole('button', { name: 'Home' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Reeksen' })).toBeInTheDocument()
  })

  it('redirects to /404 when tag is not found', async () => {
    mockedGetTag.mockResolvedValue(null)
    mockedGetProductions.mockResolvedValue({ count: 0, results: [] })

    renderPage()

    expect(await screen.findByText('404 PAGE')).toBeInTheDocument()
  })

  it('redirects to /404 when API throws a non-rate-limit error', async () => {
    mockedGetTag.mockRejectedValue(new Error('API error'))
    mockedGetProductions.mockResolvedValue({ count: 0, results: [] })

    renderPage()

    expect(await screen.findByText('404 PAGE')).toBeInTheDocument()
  })

  it('redirects to the series page with a floating alert when the API returns a rate-limit error', async () => {
    mockedGetTag.mockRejectedValue(new ApiError(429, 'Te veel aanvragen.'))
    mockedGetProductions.mockResolvedValue({ count: 0, results: [] })

    renderPage()

    expect(await screen.findByText('SERIES PAGE')).toBeInTheDocument()
    expect(screen.getByTestId('floating-alert-message')).toHaveTextContent('Te veel aanvragen.')
  })

  it('does not update the page when the initial request resolves after unmount', async () => {
    let resolveTag: (value: unknown) => void
    let resolveProductions: (value: unknown) => void

    mockedGetTag.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveTag = resolve
        }),
    )
    mockedGetProductions.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveProductions = resolve
        }),
    )

    const { unmount } = renderPage()
    unmount()

    await act(async () => {
      resolveTag!(baseTag())
      resolveProductions!({ count: 1, results: [makeProduction(1)] })
    })

    expect(screen.queryByRole('heading', { name: 'VIDEODROOM' })).not.toBeInTheDocument()
  })

  it('shows empty state when no productions exist', async () => {
    mockedGetTag.mockResolvedValue(baseTag({ short_description: { nl: 'Beschrijving' } }))
    mockedGetProductions.mockResolvedValue({ count: 0, results: [] })

    renderPage()

    expect(
      await screen.findByText('Er zijn geen producties gekoppeld aan deze reeks.'),
    ).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Toon meer' })).not.toBeInTheDocument()
  })

  it('redirects to the series tab when id is invalid', async () => {
    renderPage('invalid')

    await waitFor(() => {
      expect(screen.getByText('SERIES PAGE')).toBeInTheDocument()
    })

    expect(mockedGetTag).not.toHaveBeenCalled()
    expect(mockedGetProductions).not.toHaveBeenCalled()
    expect(screen.getByTestId('floating-alert-message')).toHaveTextContent('Ongeldig reeks-ID.')
  })

  it('navigates to production detail when a production card is clicked', async () => {
    mockedGetTag.mockResolvedValue(baseTag())
    mockedGetProductions.mockResolvedValue({
      count: 1,
      results: [
        makeProduction(42, {
          display_title: 'VIDEODROOM 2024',
          title: { nl: 'VIDEODROOM 2024' },
          first_event_start: '2024-01-01T20:00:00Z',
        }),
      ],
    })

    renderPage()

    const productionCard = await screen.findByRole('link', {
      name: /videodroom 2024/i,
    })
    fireEvent.click(productionCard)

    expect(await screen.findByText('PRODUCTION DETAIL')).toBeInTheDocument()
  })

  it('navigates to production detail with keyboard activation', async () => {
    mockedGetTag.mockResolvedValue(baseTag())
    mockedGetProductions.mockResolvedValue({
      count: 1,
      results: [
        makeProduction(43, {
          display_title: 'Keyboard productie',
          title: { nl: 'Keyboard productie' },
          first_event_start: '2024-01-02T20:00:00Z',
        }),
      ],
    })

    renderPage()

    const productionCard = await screen.findByRole('link', {
      name: /keyboard productie/i,
    })
    fireEvent.keyDown(productionCard, { key: 'Enter' })

    expect(await screen.findByText('PRODUCTION DETAIL')).toBeInTheDocument()
  })

  it('renders production genre chips on the production card when genres have display names', async () => {
    mockedGetTag.mockResolvedValue(baseTag())
    mockedGetProductions.mockResolvedValue({
      count: 1,
      results: [
        makeProduction(1, {
          display_title: 'VIDEODROOM 2024',
          title: { nl: 'VIDEODROOM 2024' },
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
        }),
      ],
    })

    renderPage()

    expect(await screen.findByText('Audiovisueel')).toBeInTheDocument()
    expect(screen.getByText('Performance')).toBeInTheDocument()
  })

  it('sorts the loaded productions by event date, groups them by year and ignores undated productions', async () => {
    mockedGetTag.mockResolvedValue(
      baseTag({
        name: null,
        display_name: 'Fallback reeks',
        excerpt: null,
        display_excerpt: null,
        short_description: null,
        display_short_description: null,
        first_production_start: null,
        last_production_end: null,
        type: null,
      }),
    )

    mockedGetProductions.mockResolvedValue({
      count: 5,
      results: [
        makeProduction(1, {
          display_title: 'Zonder datum laag',
          title: { nl: 'Zonder datum laag' },
          artist_name: {},
          first_event_start: null,
          last_event_end: null,
        }),
        makeProduction(2, {
          display_title: 'Editie 2024',
          title: { nl: 'Editie 2024' },
          artist_name: {},
          first_event_start: '2024-06-01T20:00:00Z',
          last_event_end: null,
        }),
        makeProduction(3, {
          display_title: 'Editie 2025',
          title: { nl: 'Editie 2025' },
          artist_name: {},
          first_event_start: '2025-06-01T20:00:00Z',
          last_event_end: null,
        }),
        makeProduction(4, {
          display_title: 'Alleen einddatum',
          title: { nl: 'Alleen einddatum' },
          artist_name: {},
          first_event_start: null,
          last_event_end: '2023-06-01T20:00:00Z',
        }),
        makeProduction(5, {
          display_title: 'Zonder datum hoog',
          title: { nl: 'Zonder datum hoog' },
          artist_name: {},
          first_event_start: null,
          last_event_end: null,
        }),
      ],
    })

    renderPage()

    expect(await screen.findByRole('heading', { name: 'Fallback reeks' })).toBeInTheDocument()
    expect(screen.getByText('Geen beschrijving beschikbaar.')).toBeInTheDocument()
    expect(screen.getAllByText('—').length).toBeGreaterThanOrEqual(2)

    const edition2025 = screen.getByRole('heading', { name: 'Editie 2025' })
    const edition2024 = screen.getByRole('heading', { name: 'Editie 2024' })
    const onlyEndDate = screen.getByRole('heading', {
      name: 'Alleen einddatum',
    })
    expect(screen.getByText('2023')).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Zonder datum hoog' })).not.toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Zonder datum laag' })).not.toBeInTheDocument()
    expect(edition2025.compareDocumentPosition(edition2024)).toBe(Node.DOCUMENT_POSITION_FOLLOWING)
    expect(edition2024.compareDocumentPosition(onlyEndDate)).toBe(Node.DOCUMENT_POSITION_FOLLOWING)
  })

  it('does not render Show More when the loaded amount matches the total amount', async () => {
    mockedGetTag.mockResolvedValue(baseTag())
    mockedGetProductions.mockResolvedValue({
      count: 2,
      results: [makeProduction(1), makeProduction(2)],
    })

    renderPage()

    expect(await screen.findByRole('heading', { name: 'Productie 1' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Toon meer' })).not.toBeInTheDocument()
  })

  it('loads the next page when Show More is clicked and hides the button on the last page', async () => {
    mockedGetTag.mockResolvedValue(baseTag())
    mockedGetProductions
      .mockResolvedValueOnce({
        count: 13,
        results: Array.from({ length: 12 }, (_, index) => makeProduction(index + 1)),
      })
      .mockResolvedValueOnce({
        count: 13,
        results: [
          makeProduction(13, {
            display_title: 'Productie 13',
            title: { nl: 'Productie 13' },
          }),
        ],
      })

    renderPage()

    const showMoreButton = await screen.findByRole('button', {
      name: 'Toon meer',
    })
    expect(screen.queryByRole('heading', { name: 'Productie 13' })).not.toBeInTheDocument()

    fireEvent.click(showMoreButton)

    expect(await screen.findByRole('heading', { name: 'Productie 13' })).toBeInTheDocument()
    expect(mockedGetProductions).toHaveBeenLastCalledWith({
      page: 2,
      pageSize: 12,
      filters: { tag: 1, ordering: '-first_event_start' },
    })
    expect(screen.queryByRole('button', { name: 'Toon meer' })).not.toBeInTheDocument()
  })

  it('disables Show More and shows a loading label while the next page is loading', async () => {
    let resolveNextPage: (value: unknown) => void

    mockedGetTag.mockResolvedValue(baseTag())
    mockedGetProductions
      .mockResolvedValueOnce({
        count: 13,
        results: Array.from({ length: 12 }, (_, index) => makeProduction(index + 1)),
      })
      .mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            resolveNextPage = resolve
          }),
      )

    renderPage()

    fireEvent.click(await screen.findByRole('button', { name: 'Toon meer' }))

    const loadingButton = await screen.findByRole('button', {
      name: 'Loading…',
    })
    expect(loadingButton).toBeDisabled()

    fireEvent.click(loadingButton)
    expect(mockedGetProductions).toHaveBeenCalledTimes(2)

    await act(async () => {
      resolveNextPage!({ count: 13, results: [makeProduction(13)] })
    })

    expect(await screen.findByRole('heading', { name: 'Productie 13' })).toBeInTheDocument()
  })
})
