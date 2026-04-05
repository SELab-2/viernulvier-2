import { api } from '../../services/Api'
import { ApiError } from '../../services/ApiTypes'
import { getProduction, getProductions } from '../../services/productions/Productions'
import { AttendanceMode, PerformerType } from '../../types/Productions'

jest.mock('../../services/Api', () => ({
  api: {
    get: jest.fn(),
  },
}))

describe('productions service', () => {
  const mockedGet = api.get as jest.Mock

  const mockProduction = {
    id: 42,
    attendance_mode: 'offline',
    performer_type: 'group',
    uit_database_theme: {
      id: 4,
      name: 'Drama',
    },
    uit_database_type: {
      id: 7,
      name: 'Theater',
    },
    display_title: 'Hamlet',
    display_artist_name: 'Royal Players',
    title: {
      nl: 'Hamlet',
      en: 'Hamlet',
    },
    artist_name: {
      nl: 'Royal Players',
    },
    tagline: {
      nl: 'Een klassieker op scène',
    },
    teaser: {
      nl: 'Een moderne interpretatie van Shakespeare.',
    },
    description: {
      nl: 'Volledige productieomschrijving.',
    },
    tags: [
      {
        id: 9,
        url: 'https://example.com/tags/classic',
        source: 'uitdatabank',
        source_type: 'theme',
        type: 'theme',
        is_external: true,
        is_enabled: true,
        display_name: 'Classic',
        display_short_description: 'Classic theatre',
        display_url_title: 'classic',
        name: {
          en: 'Classic',
        },
        short_description: {
          en: 'Classic theatre',
        },
        url_title: {
          en: 'classic',
        },
      },
    ],
    genres: [
      {
        id: 3,
        type: 'theater',
        use_as: 2,
        name: {
          en: 'Theatre',
        },
        display_name: 'Theatre',
        vendor_id: 'genre-3',
      },
    ],
  }

  beforeEach(() => {
    mockedGet.mockReset()
  })

  describe('getProduction', () => {
    it('fetches one production by id', async () => {
      mockedGet.mockResolvedValue({ data: mockProduction })

      const result = await getProduction(42)

      expect(mockedGet).toHaveBeenCalledWith('/productions/42/', { params: {} })
      expect(result).toEqual(mockProduction)
    })

    it('propagates ApiError to the caller', async () => {
      const error = new ApiError(404, 'The requested resource was not found.')
      mockedGet.mockRejectedValue(error)

      await expect(getProduction(42)).rejects.toBe(error)
    })

    it('fetches a production with events using include array', async () => {
      const productionWithEvents = {
        ...mockProduction,
        events: [
          {
            id: 101,
            production: 42,
            production_display: 'Hamlet',
            hall: null,
            hall_display: null,
            starts_at: '2026-03-22T20:00:00Z',
            ends_at: '2026-03-22T22:00:00Z',
            prices: [],
          },
        ],
      }
      mockedGet.mockResolvedValue({ data: productionWithEvents })

      const result = await getProduction(42, ['events'])

      expect(mockedGet).toHaveBeenCalledWith('/productions/42/', { params: { include: 'events' } })
      expect(result).toEqual(productionWithEvents)
    })
  })

  describe('getProductions', () => {
    it('fetches productions without options', async () => {
      const data = {
        count: 1,
        next: null,
        previous: null,
        results: [mockProduction],
      }
      mockedGet.mockResolvedValue({ data })

      const result = await getProductions()

      expect(mockedGet).toHaveBeenCalledWith('/productions/', { params: {} })
      expect(result).toEqual(data)
    })

    it('includes page and page_size when pagination is provided', async () => {
      mockedGet.mockResolvedValue({ data: { results: [] } })

      await getProductions({ page: 2, pageSize: 25 })

      expect(mockedGet).toHaveBeenCalledWith('/productions/', {
        params: { page: 2, page_size: 25 },
      })
    })

    it.each([
      { attendance_mode: 'offline' as AttendanceMode },
      { performer_type: 'solo' as PerformerType },
      { uit_database_theme: 4 },
      { uit_database_type: 7 },
      { genre: 3 },
      { tag: 9 },
      { has_media: true },
      { title: 'hamlet' },
      { artist_name: 'royal' },
      { search: 'shakespeare' },
      { ordering: '-id' },
      { external_id: '/api/v1/productions/42' },
    ])('applies %s filter', async (filters) => {
      mockedGet.mockResolvedValue({ data: { results: [] } })

      await getProductions({ filters })

      expect(mockedGet).toHaveBeenCalledWith('/productions/', { params: filters })
    })

    it('combines pagination and filters in params', async () => {
      mockedGet.mockResolvedValue({ data: { results: [] } })

      await getProductions({
        page: 1,
        pageSize: 10,
        filters: {
          attendance_mode: 'online' as AttendanceMode,
          performer_type: 'group' as PerformerType,
          uit_database_theme: 2,
          uit_database_type: 5,
          genre: 3,
          tag: 8,
          has_media: false,
          title: 'concert',
          artist_name: 'ensemble',
          search: 'live',
          ordering: '-id',
          external_id: '/api/v1/productions/42',
        },
      })

      expect(mockedGet).toHaveBeenCalledWith('/productions/', {
        params: {
          page: 1,
          page_size: 10,
          attendance_mode: 'online',
          performer_type: 'group',
          uit_database_theme: 2,
          uit_database_type: 5,
          genre: 3,
          tag: 8,
          has_media: false,
          title: 'concert',
          artist_name: 'ensemble',
          search: 'live',
          ordering: '-id',
          external_id: '/api/v1/productions/42',
        },
      })
    })

    it('propagates ApiError to the caller', async () => {
      const error = new ApiError(400, 'Invalid request parameters.')
      mockedGet.mockRejectedValue(error)

      await expect(getProductions({ filters: { title: 'hamlet' } })).rejects.toBe(error)
    })
  })
})
