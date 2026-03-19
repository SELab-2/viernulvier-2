import { api } from '../../services/Api'
import { getGenre, getGenres } from '../../services/genres/Genres'

/**
 * Mock the shared API client so these tests verify request construction and
 * error handling without performing real HTTP calls.
 */
jest.mock('../../services/Api', () => {
  const { buildListParams } = jest.requireActual('../../services/ApiParams')

  return {
    buildListParams,
    api: {
      get: jest.fn(),
    },
  }
})

describe('genres service', () => {
  const mockedGet = api.get as jest.Mock

  const expectGenreShape = (genre: {
    id: unknown
    type: unknown
    use_as: unknown
    name: unknown
    display_name: unknown
    vendor_id: unknown
  }) => {
    expect(typeof genre.id).toBe('number')
    expect(typeof genre.type).toBe('string')
    expect(typeof genre.use_as).toBe('object')

    if (genre.use_as !== null && typeof genre.use_as === 'object') {
      const useAs = genre.use_as as { id?: unknown; name?: unknown }
      expect(typeof useAs.id).toBe('number')
      expect(typeof useAs.name).toBe('string')
    }

    if (genre.name !== null) {
      expect(typeof genre.name).toBe('object')
    }

    if (genre.display_name !== null) {
      expect(typeof genre.display_name).toBe('string')
    }

    if (genre.vendor_id !== null) {
      expect(typeof genre.vendor_id).toBe('string')
    }
  }

  beforeEach(() => {
    // Reset mock state between tests so each assertion only sees its own calls.
    mockedGet.mockReset()
  })

  describe('getGenre', () => {
    /**
     * Confirm that requesting a single genre uses the correct detail endpoint
     * and returns the backend payload unchanged.
     */
    it('fetches one genre by id', async () => {
      const data = {
        id: 7,
        type: 'theater',
        use_as: { id: 2, name: 'genre' },
        name: { en: 'Theatre', nl: 'Theater' },
        display_name: 'Theater',
        vendor_id: 'vendor-42',
      }
      mockedGet.mockResolvedValue({ data })

      const result = await getGenre(7)

      expect(mockedGet).toHaveBeenCalledWith('/genres/7/')
      expect(result).toEqual(data)
      expectGenreShape(result)
    })

    /**
     * Ensure failures from the API client propagate to the caller unchanged.
     * Error transformation is handled by the response interceptor in Api.ts,
     * not by the service itself.
     */
    it('propagates errors to the caller', async () => {
      const error = new Error('request failed')
      mockedGet.mockRejectedValue(error)

      await expect(getGenre(7)).rejects.toThrow('request failed')
    })
  })

  describe('getGenres', () => {
    /**
     * Verify that the list endpoint can be called without options and sends an
     * empty `params` object by default.
     */
    it('fetches genres without options', async () => {
      const data = {
        count: 1,
        next: null,
        previous: null,
        results: [
          {
            id: 7,
            type: 'theater',
            use_as: { id: 2, name: 'genre' },
            name: { en: 'Theatre', nl: 'Theater' },
            display_name: 'Theater',
            vendor_id: 'vendor-42',
          },
        ],
      }
      mockedGet.mockResolvedValue({ data })

      const result = await getGenres()

      expect(mockedGet).toHaveBeenCalledWith('/genres/', { params: {} })
      expect(result).toEqual(data)
      expectGenreShape(result.results[0])
    })

    /**
     * Confirm that the `page` option is forwarded as the `page` query
     * parameter.
     */
    it('includes page in params when provided', async () => {
      mockedGet.mockResolvedValue({ data: { results: [] } })

      await getGenres({ page: 2 })

      expect(mockedGet).toHaveBeenCalledWith('/genres/', { params: { page: 2 } })
    })

    /**
     * Confirm that the frontend `pageSize` option is translated to the backend
     * query parameter name `page_size`.
     */
    it('includes page_size in params when pageSize is provided', async () => {
      mockedGet.mockResolvedValue({ data: { results: [] } })

      await getGenres({ pageSize: 25 })

      expect(mockedGet).toHaveBeenCalledWith('/genres/', { params: { page_size: 25 } })
    })

    /**
     * Verify that every supported filter key is forwarded unchanged as a query
     * parameter in the `params` object.
     */
    it.each([
      { use_as: 1 },
      { type: 'theater' },
      { vendor_id: 'vendor-42' },
      { name: 'festival' },
      { search: 'performance' },
      { ordering: '-name' },
      { external_id: 'ext-001' },
    ])('applies %s filter', async (filters) => {
      mockedGet.mockResolvedValue({ data: { results: [] } })

      await getGenres({ filters })

      expect(mockedGet).toHaveBeenCalledWith('/genres/', { params: filters })
    })

    /**
     * Verify that pagination and all supported filters can be combined in one
     * request and are forwarded together in the final query params.
     */
    it('combines pagination and all filters in params', async () => {
      mockedGet.mockResolvedValue({ data: { results: [] } })

      await getGenres({
        page: 3,
        pageSize: 10,
        filters: {
          use_as: 2,
          type: 'music',
          vendor_id: 'vendor-1',
          name: 'concert',
          search: 'live',
          ordering: 'use_as',
          external_id: 'ext-9',
        },
      })

      expect(mockedGet).toHaveBeenCalledWith('/genres/', {
        params: {
          page: 3,
          page_size: 10,
          use_as: 2,
          type: 'music',
          vendor_id: 'vendor-1',
          name: 'concert',
          search: 'live',
          ordering: 'use_as',
          external_id: 'ext-9',
        },
      })
    })

    /**
     * Ensure list request failures propagate to the caller unchanged.
     * Error transformation is handled by the response interceptor in Api.ts,
     * not by the service itself.
     */
    it('propagates errors to the caller', async () => {
      const error = new Error('request failed')
      mockedGet.mockRejectedValue(error)

      await expect(getGenres({ filters: { type: 'theater' } })).rejects.toThrow('request failed')
    })
  })
})
