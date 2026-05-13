import { ThemeProvider, createTheme } from '@mui/material/styles'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { I18nextProvider } from 'react-i18next'
import { MemoryRouter, useLocation } from 'react-router-dom'

import i18n from '../../../../i18n'
import SeriesPage from '../../../../features/series/pages/SeriesPage'
import { ApiError } from '../../../../services/ApiTypes'
import { getTags } from '../../../../services/tags/Tags'

import type { Tag, TagListResponse } from '../../../../types/Tags'

jest.mock('../../../../services/tags/Tags', () => ({
  getTags: jest.fn(),
}))

const mockedGetTags = getTags as jest.MockedFunction<typeof getTags>

const LocationProbe = () => {
  const location = useLocation()
  return <div data-testid="url-search">{location.search}</div>
}

const buildTag = (id: number, name: string): Tag => ({
  id,
  url: '',
  source: 'system',
  type: 'series',
  is_enabled: true,
  image: null,
  display_name: name,
  display_short_description: null,
  display_excerpt: null,
  display_url_title: null,
  first_production_start: '2026-01-01T19:00:00Z',
  last_production_end: '2026-01-31T20:00:00Z',
  name: { nl: name, en: name },
  excerpt: null,
  short_description: null,
  url_title: null,
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
    mockedGetTags.mockReset()
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
    })

    expect(await screen.findByRole('heading', { name: 'Reeks Alpha' })).toBeInTheDocument()

    expect(screen.getByText(/1\s+jan\.?\s+2026/i)).toBeInTheDocument()
  })

  it('renders the collection skeleton while loading', async () => {
    type SeriesResponse = TagListResponse

    let resolveFetch: ((value: SeriesResponse) => void) | undefined

    mockedGetTags.mockReturnValueOnce(
      new Promise<SeriesResponse>((resolve) => {
        resolveFetch = resolve
      }),
    )

    renderPage()

    expect(screen.getByTestId('collection-results-skeleton')).toBeInTheDocument()

    resolveFetch?.({
      count: 0,
      next: null,
      previous: null,
      results: [],
    })

    expect(await screen.findByText('Geen reeksen gevonden')).toBeInTheDocument()
  })

  it('fetches first and last production for each series card', async () => {
    const seriesTag = buildTag(10, 'Reeks Alpha')
    const secondSeriesTag = buildTag(11, 'Reeks Beta')

    mockedGetTags
      .mockResolvedValueOnce({
        count: 2,
        next: 'https://example.test/tags/?page=2',
        previous: null,
        results: [seriesTag],
      })
      .mockResolvedValueOnce({
        count: 2,
        next: null,
        previous: 'https://example.test/tags/?page=1',
        results: [secondSeriesTag],
      })

    renderPage()

    await waitFor(() => {
      expect(mockedGetTags).toHaveBeenNthCalledWith(1, {
        page: 1,
        pageSize: 250,
        filters: {
          is_enabled: true,
          search: undefined,
        },
      })
      expect(mockedGetTags).toHaveBeenNthCalledWith(2, {
        page: 2,
        pageSize: 250,
        filters: {
          is_enabled: true,
          search: undefined,
        },
      })
    })

    expect(await screen.findByRole('heading', { name: 'Reeks Alpha' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Reeks Beta' })).toBeInTheDocument()
    expect(screen.getAllByText(/1\s+jan\.?\s+2026/i).length).toBeGreaterThan(0)
  })

  it('shows empty state when there are no series bundles', async () => {
    mockedGetTags.mockResolvedValueOnce({
      count: 0,
      next: null,
      previous: null,
      results: [],
    })

    renderPage()

    expect(await screen.findByText('Geen reeksen gevonden')).toBeInTheDocument()
    expect(screen.getByText('Pas je zoekopdracht aan en probeer opnieuw.')).toBeInTheDocument()
  })

  it('shows error state and retries successfully', async () => {
    const seriesTag = buildTag(10, 'Reeks Alpha')

    mockedGetTags.mockRejectedValueOnce(new Error('network down')).mockResolvedValueOnce({
      count: 1,
      next: null,
      previous: null,
      results: [seriesTag],
    })

    renderPage()

    expect(await screen.findByText('Kon reeksen niet laden.')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Opnieuw proberen' }))

    await waitFor(() => {
      expect(mockedGetTags).toHaveBeenCalledTimes(2)
    })

    expect(await screen.findByRole('heading', { name: 'Reeks Alpha' })).toBeInTheDocument()
  })

  it('shows API error messages returned by the service layer', async () => {
    mockedGetTags.mockRejectedValueOnce(new ApiError(500, 'Server kon reeksen niet laden.'))

    renderPage()

    expect(await screen.findByText('Server kon reeksen niet laden.')).toBeInTheDocument()
    expect(screen.getByText('Er ging iets mis bij het laden van reeksen.')).toBeInTheDocument()
  })

  it('sorts series by localized name when requested from the URL', async () => {
    mockedGetTags.mockResolvedValueOnce({
      count: 2,
      next: null,
      previous: null,
      results: [buildTag(1, 'Reeks Beta'), buildTag(2, 'Reeks Alpha')],
    })

    renderPage('/series?st=n&sd=a')

    const alpha = await screen.findByRole('heading', { name: 'Reeks Alpha' })
    const beta = screen.getByRole('heading', { name: 'Reeks Beta' })

    expect(alpha.compareDocumentPosition(beta)).toBe(Node.DOCUMENT_POSITION_FOLLOWING)
  })

  it('submits a trimmed search query to the tag service', async () => {
    mockedGetTags
      .mockResolvedValueOnce({
        count: 0,
        next: null,
        previous: null,
        results: [],
      })
      .mockResolvedValueOnce({
        count: 1,
        next: null,
        previous: null,
        results: [buildTag(1, 'Zoekresultaat')],
      })

    renderPage()

    await screen.findByText('Geen reeksen gevonden')
    fireEvent.change(screen.getByRole('textbox'), {
      target: { value: '  Zoekresultaat  ' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Zoeken' }))

    await waitFor(() => {
      expect(mockedGetTags).toHaveBeenLastCalledWith({
        page: 1,
        pageSize: 250,
        filters: {
          is_enabled: true,
          search: 'Zoekresultaat',
        },
      })
    })
    expect(await screen.findByRole('heading', { name: 'Zoekresultaat' })).toBeInTheDocument()
  })

  it('does not render a filter chip panel', async () => {
    const seriesTag = buildTag(10, 'Reeks Alpha')

    mockedGetTags.mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [seriesTag],
    })

    renderPage()

    await screen.findByRole('heading', { name: 'Reeks Alpha' })
    expect(screen.queryByRole('button', { name: 'Reeks Alpha' })).not.toBeInTheDocument()
    const queryString = screen.getByTestId('url-search').textContent ?? ''
    expect(queryString).not.toMatch(/[?&]t=/)
  })

  it('normalizes unsupported date sorting to name sorting for series', async () => {
    mockedGetTags.mockResolvedValueOnce({
      count: 1,
      next: null,
      previous: null,
      results: [buildTag(10, 'Reeks Alpha')],
    })

    renderPage('/series?st=d&sd=a')

    expect(await screen.findByRole('heading', { name: 'Reeks Alpha' })).toBeInTheDocument()

    await waitFor(() => {
      const queryString = screen.getByTestId('url-search').textContent ?? ''
      expect(queryString).toContain('st=n')
      expect(queryString).toContain('sd=a')
    })
  })

  it('moves back to the last available page when URL page exceeds result pages', async () => {
    mockedGetTags.mockResolvedValueOnce({
      count: 1,
      next: null,
      previous: null,
      results: [buildTag(10, 'Reeks Alpha')],
    })

    renderPage('/series?p=3')

    expect(await screen.findByRole('heading', { name: 'Reeks Alpha' })).toBeInTheDocument()

    await waitFor(() => {
      const queryString = screen.getByTestId('url-search').textContent ?? ''
      expect(queryString).not.toContain('p=')
    })
  })

  it('sorts by localized English names when language is en', async () => {
    await i18n.changeLanguage('en')

    mockedGetTags.mockResolvedValueOnce({
      count: 2,
      next: null,
      previous: null,
      results: [
        {
          ...buildTag(1, 'Fallback NL 1'),
          name: { nl: 'Zeta', en: 'Alpha' },
          display_name: 'Fallback NL 1',
        },
        {
          ...buildTag(2, 'Fallback NL 2'),
          name: { nl: 'Alpha', en: 'Zulu' },
          display_name: 'Fallback NL 2',
        },
      ],
    })

    renderPage('/series?st=n&sd=a')

    const alpha = await screen.findByRole('heading', { name: 'Alpha' })
    const zulu = screen.getByRole('heading', { name: 'Zulu' })

    expect(alpha.compareDocumentPosition(zulu)).toBe(Node.DOCUMENT_POSITION_FOLLOWING)
  })
})
