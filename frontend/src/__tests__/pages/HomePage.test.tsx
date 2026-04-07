import { ThemeProvider, createTheme } from '@mui/material/styles'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { I18nextProvider } from 'react-i18next'
import { MemoryRouter, useLocation } from 'react-router-dom'
import i18n from '../../i18n'
import HomePage from '../../pages/HomePage'
import { getProductions } from '../../services/productions/Productions'
import type { Production } from '../../types/Productions'

jest.mock('../../services/productions/Productions', () => ({
  getProductions: jest.fn(),
}))

const mockedGetProductions = getProductions as jest.MockedFunction<typeof getProductions>

const LocationProbe = () => {
  const location = useLocation()
  return <div data-testid="url-search">{location.search}</div>
}

const buildProduction = (id: number): Production => ({
  id,
  attendance_mode: 'offline',
  performer_type: 'solo',
  first_event_start: '2026-01-01T19:00:00Z',
  last_event_end: '2026-01-01T20:00:00Z',
  media_gallery: { id: 0, name: null, media_items: [] },
  uit_database_theme: null,
  uit_database_type: null,
  display_title: `Production ${id}`,
  display_artist_name: null,
  title: { nl: `Productie ${id}` },
  artist_name: {},
  tagline: {},
  teaser: {},
  description: {},
  tags: [],
  genres: [],
})

const renderPage = (initialPath = '/') =>
  render(
    <MemoryRouter initialEntries={[initialPath]}>
      <I18nextProvider i18n={i18n}>
        <ThemeProvider theme={createTheme()}>
          <HomePage />
          <LocationProbe />
        </ThemeProvider>
      </I18nextProvider>
    </MemoryRouter>,
  )

describe('HomePage (ProductionPage)', () => {
  afterEach(() => {
    jest.clearAllMocks()
  })

  beforeEach(async () => {
    await i18n.changeLanguage('nl')
  })

  it('loads productions from API with default params and renders results', async () => {
    mockedGetProductions.mockResolvedValueOnce({
      count: 2,
      next: null,
      previous: null,
      results: [buildProduction(1), buildProduction(2)],
    })

    renderPage()

    await waitFor(() => {
      expect(mockedGetProductions).toHaveBeenCalledWith({
        page: 1,
        pageSize: 12,
        filters: {
          search: undefined,
          ordering: '-first_event_start',
        },
      })
    })

    expect(await screen.findByRole('heading', { name: 'Productie 1' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Productie 2' })).toBeInTheDocument()
  })

  it('shows empty state when API returns no productions', async () => {
    mockedGetProductions.mockResolvedValueOnce({
      count: 0,
      next: null,
      previous: null,
      results: [],
    })

    renderPage()

    expect(await screen.findByText('Geen producties gevonden')).toBeInTheDocument()
    expect(
      screen.getByText('Pas je zoekopdracht of sortering aan en probeer opnieuw.'),
    ).toBeInTheDocument()
  })

  it('shows error state and retries after failure', async () => {
    mockedGetProductions.mockRejectedValueOnce(new Error('network down')).mockResolvedValueOnce({
      count: 1,
      next: null,
      previous: null,
      results: [buildProduction(3)],
    })

    renderPage()

    expect(await screen.findByText('Kon producties niet laden.')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Opnieuw proberen' }))

    await waitFor(() => {
      expect(mockedGetProductions).toHaveBeenCalledTimes(2)
    })
    expect(await screen.findByRole('heading', { name: 'Productie 3' })).toBeInTheDocument()
  })

  it('updates URL state when list view is selected', async () => {
    mockedGetProductions.mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [buildProduction(4)],
    })

    renderPage()

    await screen.findByRole('heading', { name: 'Productie 4' })
    fireEvent.click(screen.getByRole('button', { name: 'Lijst' }))

    expect(screen.getByTestId('url-search')).toHaveTextContent('v=l')
  })

  it('fetches next page when pagination is used', async () => {
    mockedGetProductions
      .mockResolvedValueOnce({
        count: 24,
        next: '/api/v1/productions/?page=2',
        previous: null,
        results: Array.from({ length: 12 }, (_, index) => buildProduction(index + 1)),
      })
      .mockResolvedValueOnce({
        count: 24,
        next: null,
        previous: '/api/v1/productions/?page=1',
        results: Array.from({ length: 12 }, (_, index) => buildProduction(index + 13)),
      })

    renderPage()

    await screen.findByRole('button', { name: 'Ga naar pagina 2' })
    fireEvent.click(screen.getByRole('button', { name: 'Ga naar pagina 2' }))

    await waitFor(() => {
      expect(mockedGetProductions).toHaveBeenLastCalledWith({
        page: 2,
        pageSize: 12,
        filters: {
          search: undefined,
          ordering: '-first_event_start',
        },
      })
    })
  })

  it('does not refetch while typing and only searches on explicit submit', async () => {
    mockedGetProductions
      .mockResolvedValueOnce({
        count: 1,
        next: null,
        previous: null,
        results: [buildProduction(5)],
      })
      .mockResolvedValueOnce({
        count: 1,
        next: null,
        previous: null,
        results: [buildProduction(6)],
      })

    renderPage()

    await screen.findByRole('heading', { name: 'Productie 5' })
    expect(mockedGetProductions).toHaveBeenCalledTimes(1)

    fireEvent.change(
      screen.getByPlaceholderText('Zoek naar evenementen, artiesten of locaties...'),
      {
        target: { value: 'romeo' },
      },
    )

    expect(mockedGetProductions).toHaveBeenCalledTimes(1)

    fireEvent.click(screen.getByRole('button', { name: 'Zoeken' }))

    await waitFor(() => {
      expect(mockedGetProductions).toHaveBeenCalledTimes(2)
      expect(mockedGetProductions).toHaveBeenLastCalledWith({
        page: 1,
        pageSize: 12,
        filters: {
          search: 'romeo',
          ordering: '-first_event_start',
        },
      })
    })
  })
})
