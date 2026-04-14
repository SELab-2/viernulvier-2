import { ThemeProvider, createTheme } from '@mui/material/styles'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { I18nextProvider } from 'react-i18next'
import { MemoryRouter, useLocation } from 'react-router-dom'
import i18n from '../../i18n'
import SeriesPage from '../../pages/SeriesPage'
import { getTags } from '../../services/tags/Tags'
import { getProductions } from '../../services/productions/Productions'
import type { Production } from '../../types/Productions'
import type { Tag } from '../../types/Tags'

jest.mock('../../services/productions/Productions', () => ({
  getProductions: jest.fn(),
}))

jest.mock('../../services/tags/Tags', () => ({
  getTags: jest.fn(),
}))

const mockedGetTags = getTags as jest.MockedFunction<typeof getTags>
const mockedGetProductions = getProductions as jest.MockedFunction<typeof getProductions>

const LocationProbe = () => {
  const location = useLocation()
  return <div data-testid="url-search">{location.search}</div>
}

const buildTag = (id: number, name: string): Tag => ({
  id,
  url: '',
  source: 'system',
  source_type: 'theme',
  type: 'series',
  is_external: false,
  is_enabled: true,
  display_name: name,
  display_short_description: null,
  display_url_title: null,
  name: { nl: name, en: name },
  short_description: null,
  url_title: null,
})

const buildProduction = (id: number, tags: Tag[]): Production => ({
  id,
  attendance_mode: 'offline',
  performer_type: 'solo',
  first_event_start: '2026-01-01T19:00:00Z',
  last_event_end: '2026-01-01T20:00:00Z',
  media_gallery: { id: 0, name: null, media_items: [] },
  uit_database_theme: null,
  uit_database_type: null,
  display_title: `Productie ${id}`,
  display_artist_name: null,
  title: { nl: `Productie ${id}`, en: `Production ${id}` },
  artist_name: {},
  tagline: {},
  teaser: {},
  description: {},
  tags,
  genres: [],
})

const renderPage = (initialPath = '/series') =>
  render(
    <MemoryRouter initialEntries={[initialPath]}>
      <I18nextProvider i18n={i18n}>
        <ThemeProvider theme={createTheme()}>
          <SeriesPage />
          <LocationProbe />
        </ThemeProvider>
      </I18nextProvider>
    </MemoryRouter>,
  )

describe('SeriesPage', () => {
  afterEach(() => {
    jest.clearAllMocks()
  })

  beforeEach(async () => {
    await i18n.changeLanguage('nl')
  })

  it('loads tags and renders series cards', async () => {
    const seriesTag = buildTag(10, 'Reeks Alpha')

    mockedGetTags.mockResolvedValueOnce({
      count: 1,
      next: null,
      previous: null,
      results: [seriesTag],
    })

    mockedGetProductions.mockResolvedValueOnce({
      count: 1,
      next: null,
      previous: null,
      results: [buildProduction(1, [seriesTag])],
    })

    mockedGetProductions.mockResolvedValueOnce({
      count: 1,
      next: null,
      previous: null,
      results: [buildProduction(1, [seriesTag])],
    })

    renderPage()

    await waitFor(() => {
      expect(mockedGetTags).toHaveBeenCalledWith({
        page: 1,
        pageSize: 250,
        filters: {
          is_enabled: true,
          search: undefined,
        },
      })
      expect(mockedGetProductions).toHaveBeenNthCalledWith(1, {
        page: 1,
        pageSize: 1,
        filters: {
          tag: 10,
          ordering: 'first_event_start',
        },
      })
      expect(mockedGetProductions).toHaveBeenNthCalledWith(2, {
        page: 1,
        pageSize: 1,
        filters: {
          tag: 10,
          ordering: '-first_event_start',
        },
      })
    })

    expect(await screen.findByRole('heading', { name: 'Reeks Alpha' })).toBeInTheDocument()
    expect(screen.getByText('1 jan 2026')).toBeInTheDocument()
  })

  it('fetches first and last production for each series card', async () => {
    const seriesTag = buildTag(10, 'Reeks Alpha')

    mockedGetTags.mockResolvedValueOnce({
      count: 1,
      next: null,
      previous: null,
      results: [seriesTag],
    })

    mockedGetProductions
      .mockResolvedValueOnce({
        count: 2,
        next: 'https://example.test/productions/?page=2',
        previous: null,
        results: [buildProduction(1, [seriesTag])],
      })
      .mockResolvedValueOnce({
        count: 2,
        next: null,
        previous: 'https://example.test/productions/?page=1',
        results: [buildProduction(2, [seriesTag])],
      })

    renderPage()

    await waitFor(() => {
      expect(mockedGetTags).toHaveBeenCalledWith({
        page: 1,
        pageSize: 250,
        filters: {
          is_enabled: true,
          search: undefined,
        },
      })
      expect(mockedGetProductions).toHaveBeenNthCalledWith(1, {
        page: 1,
        pageSize: 1,
        filters: {
          tag: 10,
          ordering: 'first_event_start',
        },
      })
      expect(mockedGetProductions).toHaveBeenNthCalledWith(2, {
        page: 1,
        pageSize: 1,
        filters: {
          tag: 10,
          ordering: '-first_event_start',
        },
      })
    })

    expect(await screen.findByRole('heading', { name: 'Reeks Alpha' })).toBeInTheDocument()
    expect(screen.getByText('1 jan 2026')).toBeInTheDocument()
  })

  it('shows empty state when there are no series bundles', async () => {
    mockedGetTags.mockResolvedValueOnce({
      count: 1,
      next: null,
      previous: null,
      results: [buildTag(10, 'Reeks Alpha')],
    })

    mockedGetProductions.mockResolvedValueOnce({
      count: 0,
      next: null,
      previous: null,
      results: [],
    })

    mockedGetProductions.mockResolvedValueOnce({
      count: 0,
      next: null,
      previous: null,
      results: [],
    })

    renderPage()

    expect(await screen.findByText('Geen reeksen gevonden')).toBeInTheDocument()
    expect(
      screen.getByText('Pas je zoekopdracht of filters aan en probeer opnieuw.'),
    ).toBeInTheDocument()
  })

  it('shows error state and retries successfully', async () => {
    const seriesTag = buildTag(10, 'Reeks Alpha')

    mockedGetTags.mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [seriesTag],
    })

    mockedGetProductions
      .mockRejectedValueOnce(new Error('network down'))
      .mockResolvedValueOnce({
        count: 1,
        next: null,
        previous: null,
        results: [buildProduction(2, [seriesTag])],
      })
      .mockResolvedValueOnce({
        count: 1,
        next: null,
        previous: null,
        results: [buildProduction(2, [seriesTag])],
      })
      .mockResolvedValueOnce({
        count: 1,
        next: null,
        previous: null,
        results: [buildProduction(2, [seriesTag])],
      })

    renderPage()

    expect(await screen.findByText('Kon reeksen niet laden.')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Opnieuw proberen' }))

    await waitFor(() => {
      expect(mockedGetProductions).toHaveBeenCalledTimes(4)
    })

    expect(await screen.findByRole('heading', { name: 'Reeks Alpha' })).toBeInTheDocument()
  })

  it('does not render a filter chip panel', async () => {
    const seriesTag = buildTag(10, 'Reeks Alpha')

    mockedGetTags.mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [seriesTag],
    })

    mockedGetProductions
      .mockResolvedValueOnce({
        count: 1,
        next: null,
        previous: null,
        results: [buildProduction(3, [seriesTag])],
      })
      .mockResolvedValueOnce({
        count: 1,
        next: null,
        previous: null,
        results: [buildProduction(3, [seriesTag])],
      })

    renderPage()

    await screen.findByRole('heading', { name: 'Reeks Alpha' })
    expect(screen.queryByRole('button', { name: 'Reeks Alpha' })).not.toBeInTheDocument()
    const queryString = screen.getByTestId('url-search').textContent ?? ''
    expect(queryString).not.toMatch(/[?&]t=/)
  })
})
