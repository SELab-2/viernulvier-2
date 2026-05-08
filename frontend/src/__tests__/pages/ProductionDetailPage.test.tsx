import { ThemeProvider, createTheme } from '@mui/material'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import ProductionDetailPage from '../../pages/ProductionDetailPage'
import { getProduction } from '../../services/productions/Productions'

import type { Event } from '../../types/Events'
import type { Production } from '../../types/Productions'

const languageState = { current: 'nl' }

jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    i18n: { language: languageState.current },
    t: (_key: string, defaultValue: string) => defaultValue,
  }),
}))

const mockNavigate = jest.fn()
const mockUseParams = jest.fn()

jest.mock('react-router-dom', () => ({
  ...(jest.requireActual('react-router-dom') as object),
  useParams: () => mockUseParams(),
  useNavigate: () => mockNavigate,
}))

jest.mock('../../services/productions/Productions', () => ({
  getProduction: jest.fn(),
}))

jest.mock('../../components/production/RelatedProductions', () => ({
  __esModule: true,
  default: () => <div data-testid="related-productions-mock" />,
}))

jest.mock('../../components/production/RelatedBlogs', () => ({
  __esModule: true,
  default: () => <div data-testid="related-blogs-mock" />,
}))

beforeEach(() => {
  Element.prototype.scrollTo = jest.fn()
})

const mockedGetProduction = getProduction as jest.MockedFunction<typeof getProduction>

const setMatchMediaMatches = (matches: boolean) => {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    configurable: true,
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

const renderPage = () =>
  render(
    <MemoryRouter>
      <ThemeProvider theme={createTheme()}>
        <ProductionDetailPage />
      </ThemeProvider>
    </MemoryRouter>,
  )

describe('ProductionDetailPage', () => {
  afterEach(() => {
    jest.clearAllMocks()
    mockedGetProduction.mockReset()
    languageState.current = 'nl'
    setMatchMediaMatches(false)
  })

  it('shows invalid id error and navigates to home for non-numeric ID', async () => {
    mockUseParams.mockReturnValue({ id: 'abc' })

    renderPage()

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/nl', {
        state: {
          floatingAlert: {
            open: true,
            message: 'Invalid production ID',
            severity: 'error',
          },
        },
      })
    })
  })

  it('renders all production data and media list when getProduction returns valid result', async () => {
    mockUseParams.mockReturnValue({ id: '42' })

    const productionData = {
      id: 42,
      title: { nl: 'Productie NL', en: 'Production EN' },
      display_title: 'Display production',
      artist_name: { nl: 'Kunstenaar NL' },
      display_artist_name: 'Artist display',
      tagline: { nl: 'Tagline NL' },
      description: { nl: 'Omschrijving NL' },
      teaser: { nl: 'Teaser NL' },
      media_gallery: {
        id: 1,
        name: 'Primary media',
        media_items: [
          {
            id: 1,
            gallery: 1,
            type: 'foto',
            format: 'jpg',
            original_filename: 'img.jpg',
            position: 0,
            width: null,
            height: null,
            title: null,
            display_title: 'Image title',
            description: null,
            credits: null,
            link: null,
            crops: [{ id: 1, name: 'FE3_header', image_url: 'https://x.png' }],
          },
        ],
      },
      events: [
        {
          id: 1,
          production: {
            id: 42,
            attendance_mode: 'offline',
            performer_type: 'group',
            uit_database_type: null,
            display_title: null,
            display_artist_name: null,
            title: {},
            artist_name: {},
            tagline: {},
            teaser: {},
            description: {},
            tags: [],
            genres: [],
            media_gallery: { id: 1, name: 'Primary media', media_items: [] },
            events: [],
          },
          production_display: 'Production 1',
          hall: null,
          hall_display: 'Main hall',
          starts_at: '2025-10-01T20:00:00Z',
          ends_at: '2025-10-01T22:00:00Z',
          prices: [],
        },
        {
          id: 2,
          production: {
            id: 42,
            attendance_mode: 'offline',
            performer_type: 'group',
            uit_database_type: null,
            display_title: null,
            display_artist_name: null,
            title: {},
            artist_name: {},
            tagline: {},
            teaser: {},
            description: {},
            tags: [],
            genres: [],
            media_gallery: { id: 1, name: 'Primary media', media_items: [] },
            events: [],
          },
          production_display: 'Production 2',
          hall: null,
          hall_display: 'Second hall',
          starts_at: '2025-10-02T20:00:00Z',
          ends_at: '2025-10-02T22:00:00Z',
          prices: [],
        },
      ] as unknown as Event[],
      genres: [
        {
          id: 1,
          type: 'genre',
          name: { nl: 'Drama' },
          display_name: 'Drama',
          vendor_id: null,
        },
      ],
      tags: [
        {
          id: 1,
          url: 'https://tags.local/tag1',
          source: 'local',
          type: 'tag',
          is_enabled: true,
          image: null,
          display_name: 'Tag1',
          display_short_description: null,
          display_excerpt: null,
          display_url_title: null,
          first_production_start: null,
          last_production_end: null,
          name: null,
          excerpt: null,
          short_description: null,
          url_title: null,
        },
      ],
      uit_database_type: { id: 1, name: 'TypeName' },
      performer_type: 'group',
      attendance_mode: 'offline',
      first_event_start: null,
      last_event_end: null,
      blogs: [
        {
          id: 100,
          slug: 'blog',
          published_at: '2025-01-01T10:00:00Z',
          cover_image: null,
          title: { nl: 'Blog' },
          excerpt: { nl: 'Excerpt' },
          display_title: 'Blog',
          display_excerpt: 'Excerpt',
        },
      ],
    } as Production

    mockedGetProduction.mockResolvedValue(productionData as Production)

    renderPage()

    await waitFor(() => {
      expect(screen.getAllByText('Productie NL')).toHaveLength(2)
      expect(screen.getByRole('heading', { name: 'Productie NL' })).toBeInTheDocument()
      expect(screen.queryByText('Tagline NL')).not.toBeInTheDocument()
      expect(screen.getByText('Teaser NL')).toBeInTheDocument()
      expect(screen.getByText('Omschrijving NL')).toBeInTheDocument()
      expect(screen.getByText('Events')).toBeInTheDocument()
      expect(screen.getByText('Media')).toBeInTheDocument()
      expect(screen.getByTestId('related-blogs-mock')).toBeInTheDocument()
    })

    expect(mockedGetProduction).toHaveBeenCalledWith(42, ['events', 'related', 'blogs'])
    expect(mockNavigate).not.toHaveBeenCalled()
  })

  it('shows load failed if getProduction throws and navigates to home', async () => {
    mockUseParams.mockReturnValue({ id: '42' })
    mockedGetProduction.mockRejectedValue(new Error('network error'))

    renderPage()

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/nl', {
        state: {
          floatingAlert: {
            open: true,
            message: 'Could not load production',
            severity: 'error',
          },
        },
      })
    })
  })

  it('keeps rendering production details when no related blogs are returned', async () => {
    mockUseParams.mockReturnValue({ id: '42' })

    mockedGetProduction.mockResolvedValue({
      id: 42,
      title: { nl: 'Productie NL' },
      display_title: 'Display production',
      artist_name: {},
      display_artist_name: null,
      tagline: { nl: 'Tagline NL' },
      description: { nl: 'Omschrijving NL' },
      teaser: { nl: 'Teaser NL' },
      media_gallery: { id: 1, name: 'Primary media', media_items: [] },
      events: [],
      genres: [],
      tags: [],
      uit_database_type: null,
      performer_type: 'group',
      attendance_mode: 'offline',
      first_event_start: null,
      last_event_end: null,
      blogs: [],
    } as Production)

    renderPage()

    await waitFor(() => {
      expect(screen.queryByText('Tagline NL')).not.toBeInTheDocument()
      expect(screen.getByRole('heading', { name: 'Productie NL' })).toBeInTheDocument()
      expect(screen.getByText('Events')).toBeInTheDocument()
    })

    expect(screen.queryByTestId('related-blogs-mock')).not.toBeInTheDocument()
    expect(mockNavigate).not.toHaveBeenCalled()
  })

  it('renders title at top and hides meta header on mobile', async () => {
    setMatchMediaMatches(true)
    mockUseParams.mockReturnValue({ id: '42' })

    mockedGetProduction.mockResolvedValue({
      id: 42,
      title: { nl: 'Productie NL' },
      display_title: 'Display production',
      artist_name: {},
      display_artist_name: null,
      tagline: { nl: 'Tagline NL' },
      description: { nl: 'Omschrijving NL' },
      teaser: { nl: 'Teaser NL' },
      media_gallery: { id: 1, name: 'Primary media', media_items: [] },
      events: [],
      genres: [],
      tags: [],
      uit_database_type: null,
      performer_type: 'group',
      attendance_mode: 'offline',
      first_event_start: null,
      last_event_end: null,
      blogs: [],
    } as Production)

    renderPage()

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Productie NL' })).toBeInTheDocument()
      expect(screen.queryByText('Tagline NL')).not.toBeInTheDocument()
      expect(screen.getByText('Teaser NL')).toBeInTheDocument()
    })
  })

  it('uses first available crop when preferred hero crops are missing', async () => {
    mockUseParams.mockReturnValue({ id: '42' })

    mockedGetProduction.mockResolvedValue({
      id: 42,
      title: { nl: 'Productie NL' },
      display_title: null,
      artist_name: {},
      display_artist_name: null,
      tagline: {},
      description: {},
      teaser: {},
      media_gallery: {
        id: 1,
        name: 'Primary media',
        media_items: [
          {
            id: 5,
            gallery: 1,
            type: 'foto',
            format: 'jpg',
            original_filename: 'image.jpg',
            position: 0,
            width: null,
            height: null,
            title: null,
            display_title: null,
            description: null,
            credits: null,
            link: null,
            crops: [
              { id: 11, name: 'custom_crop', image_url: 'https://cdn.test/fallback-crop.jpg' },
            ],
          },
        ],
      },
      events: [],
      genres: [],
      tags: [],
      uit_database_type: null,
      performer_type: 'group',
      attendance_mode: 'offline',
      first_event_start: null,
      last_event_end: null,
    } as unknown as Production)

    renderPage()

    const heroImage = await screen.findByRole('img', { name: 'Productie NL' })
    expect(heroImage).toHaveAttribute('src', 'https://cdn.test/fallback-crop.jpg')
  })

  it('returns null when route parameter id is missing', () => {
    mockUseParams.mockReturnValue({})

    const { container } = renderPage()

    expect(container).toBeEmptyDOMElement()
    expect(mockedGetProduction).not.toHaveBeenCalled()
    expect(mockNavigate).not.toHaveBeenCalled()
  })
})
