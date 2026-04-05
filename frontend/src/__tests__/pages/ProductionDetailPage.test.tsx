import { render, screen, waitFor } from '@testing-library/react'
import { ThemeProvider, createTheme } from '@mui/material'
import ProductionDetailPage from '../../pages/ProductionDetailPage'
import { getProduction } from '../../services/productions/Productions'
import type { Event } from '../../types/Events'
import type { Production } from '../../types/Productions'

jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    i18n: { language: 'nl' },
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

const mockedGetProduction = getProduction as jest.MockedFunction<typeof getProduction>

const renderPage = () =>
  render(
    <ThemeProvider theme={createTheme()}>
      <ProductionDetailPage />
    </ThemeProvider>,
  )

describe('ProductionDetailPage', () => {
  afterEach(() => {
    jest.clearAllMocks()
  })

  it('shows invalid id error and navigates to home for non-numeric ID', async () => {
    mockUseParams.mockReturnValue({ id: 'abc' })
    mockedGetProduction.mockResolvedValueOnce(undefined as never)

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Invalid production ID')).toBeInTheDocument()
      expect(mockNavigate).toHaveBeenCalledWith('/', {
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
            uit_database_theme: null,
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
            uit_database_theme: null,
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
          use_as: { id: 1, name: 'main' },
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
          source_type: 'tag',
          type: 'tag',
          is_external: false,
          is_enabled: true,
          display_name: 'Tag1',
          display_short_description: null,
          display_url_title: null,
          name: null,
          short_description: null,
          url_title: null,
        },
      ],
      uit_database_theme: null,
      uit_database_type: { id: 1, name: 'TypeName' },
      performer_type: 'group',
      attendance_mode: 'offline',
      first_event_start: null,
      last_event_end: null,
    } as Production

    mockedGetProduction.mockResolvedValue(productionData as Production)

    renderPage()

    await waitFor(() => {
      expect(screen.getAllByText('Productie NL')).toHaveLength(2)
      expect(screen.getByText('Tagline NL')).toBeInTheDocument()
      expect(screen.getByText('Teaser NL')).toBeInTheDocument()
      expect(screen.getByText('Omschrijving NL')).toBeInTheDocument()
      expect(screen.getByText('Events')).toBeInTheDocument()
      expect(screen.getByText('Media')).toBeInTheDocument()
      expect(screen.getByText('1 / 1')).toBeInTheDocument()
    })

    expect(mockNavigate).not.toHaveBeenCalled()
  })

  it('shows load failed if getProduction throws and navigates to home', async () => {
    mockUseParams.mockReturnValue({ id: '42' })
    mockedGetProduction.mockRejectedValue(new Error('network error'))

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Could not load production')).toBeInTheDocument()
      expect(mockNavigate).toHaveBeenCalledWith('/', {
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
})
