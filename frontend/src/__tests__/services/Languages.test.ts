import { api } from '../../services/Api'
import { ApiError } from '../../services/ApiTypes'
import { getLanguage, getLanguages } from '../../services/languages/Languages'

jest.mock('../../services/Api', () => ({
  api: {
    get: jest.fn(),
  },
}))

describe('languages service', () => {
  const mockedGet = api.get as jest.Mock

  beforeEach(() => {
    mockedGet.mockReset()
  })

  describe('getLanguage', () => {
    it('fetches one language by code', async () => {
      const data = {
        code: 'nl',
        name: 'Dutch',
        is_active: true,
      }
      mockedGet.mockResolvedValue({ data })

      const result = await getLanguage('nl')

      expect(mockedGet).toHaveBeenCalledWith('/languages/nl/')
      expect(result).toEqual(data)
    })

    it('propagates ApiError to the caller', async () => {
      const error = new ApiError(404, 'The requested resource was not found.')
      mockedGet.mockRejectedValue(error)

      await expect(getLanguage('xx')).rejects.toBe(error)
    })
  })

  describe('getLanguages', () => {
    it('fetches languages without options', async () => {
      const data = {
        count: 2,
        next: null,
        previous: null,
        results: [
          { code: 'en', name: 'English', is_active: true },
          { code: 'nl', name: 'Dutch', is_active: true },
        ],
      }
      mockedGet.mockResolvedValue({ data })

      const result = await getLanguages()

      expect(mockedGet).toHaveBeenCalledWith('/languages/', { params: {} })
      expect(result).toEqual(data)
    })

    it('includes page and page_size when pagination is provided', async () => {
      mockedGet.mockResolvedValue({ data: { results: [] } })

      await getLanguages({ page: 2, pageSize: 25 })

      expect(mockedGet).toHaveBeenCalledWith('/languages/', {
        params: { page: 2, page_size: 25 },
      })
    })

    it.each([
      { code: 'nl' },
      { name: 'Dutch' },
      { is_active: true },
      { search: 'dut' },
      { ordering: 'code' },
      { external_id: 'lang-nl' },
    ])('applies %s filter', async (filters) => {
      mockedGet.mockResolvedValue({ data: { results: [] } })

      await getLanguages({ filters })

      expect(mockedGet).toHaveBeenCalledWith('/languages/', { params: filters })
    })

    it('combines pagination and filters in params', async () => {
      mockedGet.mockResolvedValue({ data: { results: [] } })

      await getLanguages({
        page: 1,
        pageSize: 10,
        filters: {
          code: 'en',
          name: 'English',
          is_active: true,
          search: 'engl',
          ordering: '-name',
          external_id: 'lang-en',
        },
      })

      expect(mockedGet).toHaveBeenCalledWith('/languages/', {
        params: {
          page: 1,
          page_size: 10,
          code: 'en',
          name: 'English',
          is_active: true,
          search: 'engl',
          ordering: '-name',
          external_id: 'lang-en',
        },
      })
    })

    it('propagates ApiError to the caller', async () => {
      const error = new ApiError(401, 'Not authenticated. Please log in.')
      mockedGet.mockRejectedValue(error)

      await expect(getLanguages()).rejects.toBe(error)
    })
  })
})
