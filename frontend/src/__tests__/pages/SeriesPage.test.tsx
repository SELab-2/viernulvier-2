import { ThemeProvider, createTheme } from '@mui/material/styles'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { I18nextProvider } from 'react-i18next'
import { MemoryRouter, useLocation } from 'react-router-dom'
import i18n from '../../i18n'
import SeriesPage from '../../pages/SeriesPage'
import { getProductionSeries } from '../../services/productions/Productions'
import type { Series } from '../../types/Series'
import type { Tag } from '../../types/Tags'

jest.mock('../../services/productions/Productions', () => ({
  getProductionSeries: jest.fn(),
}))

const mockedGetProductionSeries = getProductionSeries as jest.MockedFunction<
  typeof getProductionSeries
>

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

const buildSeries = (tag: Tag): Series => ({
  tag,
  firstProductionStart: '2026-01-01T19:00:00Z',
  lastProductionEnd: '2026-01-01T20:00:00Z',
  lastProductionImage: null,
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

    mockedGetProductionSeries.mockResolvedValueOnce({
      count: 1,
      next: null,
      previous: null,
      results: [buildSeries(seriesTag)],
    })

    renderPage()

    await waitFor(() => {
      expect(mockedGetProductionSeries).toHaveBeenCalledWith({
        page: 1,
        pageSize: 250,
        filters: {
          search: undefined,
        },
      })
    })

    expect(await screen.findByRole('heading', { name: 'Reeks Alpha' })).toBeInTheDocument()
    expect(screen.getByText('1 jan 2026')).toBeInTheDocument()
  })

  it('fetches first and last production for each series card', async () => {
    const seriesTag = buildTag(10, 'Reeks Alpha')
    const secondSeriesTag = buildTag(11, 'Reeks Beta')

    mockedGetProductionSeries
      .mockResolvedValueOnce({
        count: 2,
        next: 'https://example.test/productions/?page=2',
        previous: null,
        results: [buildSeries(seriesTag)],
      })
      .mockResolvedValueOnce({
        count: 2,
        next: null,
        previous: 'https://example.test/productions/?page=1',
        results: [buildSeries(secondSeriesTag)],
      })

    renderPage()

    await waitFor(() => {
      expect(mockedGetProductionSeries).toHaveBeenNthCalledWith(1, {
        page: 1,
        pageSize: 250,
        filters: {
          search: undefined,
        },
      })
      expect(mockedGetProductionSeries).toHaveBeenNthCalledWith(2, {
        page: 2,
        pageSize: 250,
        filters: {
          search: undefined,
        },
      })
    })

    expect(await screen.findByRole('heading', { name: 'Reeks Alpha' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Reeks Beta' })).toBeInTheDocument()
    expect(screen.getAllByText('1 jan 2026').length).toBeGreaterThan(0)
  })

  it('shows empty state when there are no series bundles', async () => {
    mockedGetProductionSeries.mockResolvedValueOnce({
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

    mockedGetProductionSeries
      .mockRejectedValueOnce(new Error('network down'))
      .mockResolvedValueOnce({
        count: 1,
        next: null,
        previous: null,
        results: [buildSeries(seriesTag)],
      })

    renderPage()

    expect(await screen.findByText('Kon reeksen niet laden.')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Opnieuw proberen' }))

    await waitFor(() => {
      expect(mockedGetProductionSeries).toHaveBeenCalledTimes(2)
    })

    expect(await screen.findByRole('heading', { name: 'Reeks Alpha' })).toBeInTheDocument()
  })

  it('does not render a filter chip panel', async () => {
    const seriesTag = buildTag(10, 'Reeks Alpha')

    mockedGetProductionSeries.mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [buildSeries(seriesTag)],
    })

    renderPage()

    await screen.findByRole('heading', { name: 'Reeks Alpha' })
    expect(screen.queryByRole('button', { name: 'Reeks Alpha' })).not.toBeInTheDocument()
    const queryString = screen.getByTestId('url-search').textContent ?? ''
    expect(queryString).not.toMatch(/[?&]t=/)
  })
})
