import { ThemeProvider, createTheme } from '@mui/material/styles'
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { I18nextProvider } from 'react-i18next'
import { MemoryRouter, useLocation } from 'react-router-dom'

import i18n from '../../i18n'
import HomePage from '../../pages/HomePage'
import { ApiError } from '../../services/ApiTypes'
import { getGenres } from '../../services/genres/Genres'
import { getProductions } from '../../services/productions/Productions'
import { getTags } from '../../services/tags/Tags'
import type { Genre } from '../../types/Genres'
import type { Production } from '../../types/Productions'
import type { Tag } from '../../types/Tags'

jest.mock('../../services/productions/Productions', () => ({
  getProductions: jest.fn(),
}))

jest.mock('../../services/genres/Genres', () => ({
  getGenres: jest.fn(),
}))

jest.mock('../../services/tags/Tags', () => ({
  getTags: jest.fn(),
}))

const mockedGetProductions = getProductions as jest.MockedFunction<typeof getProductions>
const mockedGetGenres = getGenres as jest.MockedFunction<typeof getGenres>
const mockedGetTags = getTags as jest.MockedFunction<typeof getTags>

const genreFixtures: Genre[] = [
  {
    id: 5,
    type: 'main',
    use_as: { id: 1, name: 'production' },
    name: { nl: 'Theater' },
    display_name: 'Theater',
    vendor_id: null,
  },
  {
    id: 9,
    type: 'main',
    use_as: { id: 1, name: 'production' },
    name: { nl: 'Dans' },
    display_name: 'Dans',
    vendor_id: null,
  },
]

const tagFixtures: Tag[] = [
  {
    id: 8,
    url: '/api/v1/tags/8/',
    source: 'manual',
    source_type: 'editorial',
    type: 'series',
    is_external: false,
    is_enabled: true,
    display_name: 'Premiere',
    display_short_description: null,
    display_url_title: null,
    name: { nl: 'Premiere' },
    short_description: {},
    url_title: {},
  },
  {
    id: 12,
    url: '/api/v1/tags/12/',
    source: 'manual',
    source_type: 'editorial',
    type: 'series',
    is_external: false,
    is_enabled: true,
    display_name: 'Festival',
    display_short_description: null,
    display_url_title: null,
    name: { nl: 'Festival' },
    short_description: {},
    url_title: {},
  },
]

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

const renderPage = (
  initialEntry:
    | string
    | { pathname: string; state?: { floatingAlert?: { open?: boolean; message?: string } } } = '/',
) =>
  render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <I18nextProvider i18n={i18n}>
        <ThemeProvider theme={createTheme()}>
          <HomePage />
          <LocationProbe />
        </ThemeProvider>
      </I18nextProvider>
    </MemoryRouter>,
  )

const setMatchMediaMatches = (matches: boolean) => {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation((query: string) => ({
      matches,
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    })),
  })
}

describe('HomePage (ProductionPage)', () => {
  afterEach(() => {
    jest.clearAllMocks()
  })

  beforeEach(async () => {
    await i18n.changeLanguage('nl')
    setMatchMediaMatches(false)
    mockedGetGenres.mockResolvedValue({
      count: genreFixtures.length,
      next: null,
      previous: null,
      results: genreFixtures,
    })
    mockedGetTags.mockResolvedValue({
      count: tagFixtures.length,
      next: null,
      previous: null,
      results: tagFixtures,
    })
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

  it('does not refetch productions when the language changes', async () => {
    mockedGetProductions.mockResolvedValueOnce({
      count: 1,
      next: null,
      previous: null,
      results: [buildProduction(1)],
    })

    renderPage()

    await screen.findByRole('heading', { name: 'Productie 1' })
    expect(mockedGetProductions).toHaveBeenCalledTimes(1)

    await act(async () => {
      await i18n.changeLanguage('en')
    })

    expect(mockedGetProductions).toHaveBeenCalledTimes(1)
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
    expect(screen.getByText('Pas je zoekopdracht aan en probeer opnieuw.')).toBeInTheDocument()
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

  it('shows localized fallback copy when API returns a non-localized error message', async () => {
    mockedGetProductions.mockRejectedValueOnce(new ApiError(500, 'Something failed on server'))

    renderPage()

    expect(await screen.findByText('Kon producties niet laden.')).toBeInTheDocument()
    expect(screen.queryByText('Something failed on server')).not.toBeInTheDocument()
  })

  it('shows floating alert message passed through navigation state without inline error', async () => {
    mockedGetProductions.mockResolvedValueOnce({
      count: 1,
      next: null,
      previous: null,
      results: [buildProduction(10)],
    })

    renderPage({
      pathname: '/',
      state: {
        floatingAlert: {
          open: true,
          message: 'Kon productie niet laden',
        },
      },
    })

    expect(await screen.findByText('Kon productie niet laden')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Opnieuw proberen' })).not.toBeInTheDocument()
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

  it('opens filters in a mobile dialog instead of rendering the sidebar inline', async () => {
    setMatchMediaMatches(true)
    mockedGetProductions.mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [buildProduction(11)],
    })

    renderPage()

    await screen.findByRole('heading', { name: 'Productie 11' })
    expect(
      screen.queryByRole('complementary', { name: 'Geavanceerde filters' }),
    ).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Filters' }))

    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByRole('checkbox', { name: 'Online' })).toBeInTheDocument()
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

  it('retries fetch when submitting the same query after an error', async () => {
    mockedGetProductions.mockRejectedValueOnce(new Error('network down')).mockResolvedValueOnce({
      count: 1,
      next: null,
      previous: null,
      results: [buildProduction(9)],
    })

    renderPage('/?q=romeo')

    expect(await screen.findByText('Kon producties niet laden.')).toBeInTheDocument()

    fireEvent.keyDown(
      screen.getByPlaceholderText('Zoek naar evenementen, artiesten of locaties...'),
      {
        key: 'Enter',
        code: 'Enter',
      },
    )

    await waitFor(() => {
      expect(mockedGetProductions).toHaveBeenCalledTimes(2)
    })
    expect(await screen.findByRole('heading', { name: 'Productie 9' })).toBeInTheDocument()
  })

  it('applies sidebar filters to the URL and forwards only the first selected values to the backend', async () => {
    mockedGetProductions.mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [buildProduction(7)],
    })

    renderPage('/?p=2&fa=2026-03-01&fb=2026-03-31')

    await screen.findByRole('heading', { name: 'Productie 7' })

    fireEvent.click(screen.getByRole('checkbox', { name: 'Online' }))
    fireEvent.click(screen.getByRole('checkbox', { name: 'Fysiek' }))
    fireEvent.click(screen.getByRole('checkbox', { name: 'Groep' }))
    fireEvent.click(screen.getByRole('checkbox', { name: 'Solo' }))
    fireEvent.click(screen.getByText('Theater'))
    fireEvent.click(screen.getByText('Dans'))
    fireEvent.click(screen.getByText('Premiere'))
    fireEvent.click(screen.getByText('Festival'))

    await waitFor(() => {
      expect(mockedGetProductions).toHaveBeenLastCalledWith({
        page: 1,
        pageSize: 12,
        filters: {
          search: undefined,
          ordering: '-first_event_start',
          attendance_mode: 'online',
          performer_type: 'group',
          genre: 5,
          tag: 8,
          first_event_start_after: '2026-03-01T00:00:00.000Z',
          first_event_start_before: '2026-03-31T23:59:59.999Z',
        },
      })
    })

    expect(screen.getByTestId('url-search')).toHaveTextContent('am=online-offline')
    expect(screen.getByTestId('url-search')).toHaveTextContent('pt=group-solo')
    expect(screen.getByTestId('url-search')).toHaveTextContent('g=5-9')
    expect(screen.getByTestId('url-search')).toHaveTextContent('t=8-12')
    expect(screen.getByTestId('url-search')).toHaveTextContent('fa=2026-03-01')
    expect(screen.getByTestId('url-search')).toHaveTextContent('fb=2026-03-31')
    expect(screen.getByTestId('url-search')).not.toHaveTextContent('p=')
  })
})
