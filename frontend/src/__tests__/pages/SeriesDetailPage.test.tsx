import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import SeriesDetailPage from '../../pages/SeriesDetailPage'

import { getTag } from '../../services/tags/Tags'
import { getProductions } from '../../services/productions/Productions'

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
        'nav.home': 'Archief',
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
      <MemoryRouter initialEntries={[`/series/${id}`]}>
        <Routes>
          <Route path="/series/:id" element={<SeriesDetailPage />} />
          <Route path="/productions/:id" element={<div>PRODUCTION DETAIL</div>} />
          <Route path="/404" element={<div>404 PAGE</div>} />
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
    expect(screen.getByText('Beschrijving van de reeks')).toBeInTheDocument()
    expect(screen.getByText('VIDEODROOM 2024')).toBeInTheDocument()
    expect(screen.getByText('Alle edities')).toBeInTheDocument()
  })

  it('renders breadcrumb buttons to archive and series overview', async () => {
    mockedGetTag.mockResolvedValue({
      id: 1,
      name: { nl: 'VIDEODROOM' },
      short_description: { nl: 'Beschrijving van de reeks' },
      type: 'festival',
    })

    mockedGetProductions.mockResolvedValue({
      results: [],
    })

    renderPage()

    await screen.findByRole('heading', { name: 'VIDEODROOM' })

    expect(screen.getByRole('button', { name: 'Archief' })).toBeInTheDocument()
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

    const productionCard = await screen.findByRole('button', { name: /videodroom 2024/i })
    fireEvent.click(productionCard)

    expect(await screen.findByText('PRODUCTION DETAIL')).toBeInTheDocument()
  })

  it('renders both production genres and series tags in the production card', async () => {
    mockedGetTag.mockResolvedValue({
      id: 1,
      name: { nl: 'VIDEODROOM' },
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
              use_as: { id: 1, name: 'genre' },
              name: { nl: 'Audiovisueel', en: 'Audiovisual' },
              display_name: null,
              vendor_id: null,
            },
            {
              id: 11,
              type: 'genre',
              use_as: { id: 1, name: 'genre' },
              name: { nl: 'Performance', en: 'Performance' },
              display_name: null,
              vendor_id: null,
            },
          ],
          tags: [
            {
              id: 20,
              name: { nl: 'Festivalreeks', en: 'Festival series' },
              display_name: null,
              type: 'series',
            },
            {
              id: 21,
              name: { nl: 'Videodroom', en: 'Videodroom' },
              display_name: null,
              type: 'series',
            },
          ],
        },
      ],
    })

    renderPage()

    expect(await screen.findByText('Audiovisueel')).toBeInTheDocument()
    expect(screen.getByText('Performance')).toBeInTheDocument()
    expect(screen.getByText('Festivalreeks')).toBeInTheDocument()
    expect(screen.getByText('Videodroom')).toBeInTheDocument()

    expect(screen.getByRole('link', { name: 'Festivalreeks' })).toHaveAttribute(
      'href',
      '/series/20',
    )
    expect(screen.getByRole('link', { name: 'Videodroom' })).toHaveAttribute('href', '/series/21')
  })
})
