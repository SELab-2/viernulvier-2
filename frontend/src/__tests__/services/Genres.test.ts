import { api } from '../../services/Api'
import { getGenre, getGenres } from '../../services/genres/Genres'

/**
 * Mock the shared API client so these tests verify request construction and
 * error handling without performing real HTTP calls.
 */
jest.mock('../../services/Api', () => ({
  api: {
    get: jest.fn(),
  },
}))

describe('genres service', () => {
  const mockedGet = api.get as jest.Mock

  beforeEach(() => {
    // Reset mock state between tests so each assertion only sees its own calls.
    mockedGet.mockReset()

    // Silence expected error logs when testing rejected requests.
    jest.spyOn(console, 'error').mockImplementation(() => undefined)
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  describe('getGenre', () => {
    /**
     * Confirm that requesting a single genre uses the correct detail endpoint
     * and returns the backend payload unchanged.
     */
    it('fetches one genre by id', async () => {
      const data = { id: 7, type: 'theater' }
      mockedGet.mockResolvedValue({ data })

      const result = await getGenre(7)

      expect(mockedGet).toHaveBeenCalledWith('/genres/7/')
      expect(result).toEqual(data)
    })

    /**
     * Ensure request failures are logged and then rethrown so calling code can
     * still handle the error.
     */
    it('logs and rethrows when fetching one genre fails', async () => {
      const error = new Error('request failed')
      mockedGet.mockRejectedValue(error)

      await expect(getGenre(7)).rejects.toThrow('request failed')
      expect(console.error).toHaveBeenCalledWith('Error fetching genre:', error)
    })
  })

  describe('getGenres', () => {
    /**
     * Verify that the list endpoint can be called without options and sends an
     * empty `params` object by default.
     */
    it('fetches genres without options', async () => {
      const data = { results: [] }
      mockedGet.mockResolvedValue({ data })

      const result = await getGenres()

      expect(mockedGet).toHaveBeenCalledWith('/genres/', { params: {} })
      expect(result).toEqual(data)
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
      [{ use_as: 1 }, 'use_as'],
      [{ type: 'theater' }, 'type'],
      [{ vendor_id: 'vendor-42' }, 'vendor_id'],
      [{ name: 'festival' }, 'name'],
      [{ search: 'performance' }, 'search'],
      [{ ordering: '-name' }, 'ordering'],
      [{ external_id: 'ext-001' }, 'external_id'],
    ])('applies %s filter', async (filters, _filterName) => {
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
     * Ensure list request failures follow the same contract as detail requests:
     * log the error and rethrow it unchanged.
     */
    it('logs and rethrows when fetching genres fails', async () => {
      const error = new Error('request failed')
      mockedGet.mockRejectedValue(error)

      await expect(getGenres({ filters: { type: 'theater' } })).rejects.toThrow('request failed')
      expect(console.error).toHaveBeenCalledWith('Error fetching genres:', error)
    })
  })
})
