import { api } from '../../services/Api'
import { ApiError } from '../../services/ApiTypes'
import { getTag, getTags } from '../../services/tags/Tags'

import type { Tag, TagListResponse } from '../../types/Tags'

jest.mock('../../services/Api', () => ({
  api: {
    get: jest.fn(),
  },
}))

describe('tags service', () => {
  const mockedGet = api.get as jest.Mock

  const mockTag: Tag = {
    id: 9,
    url: 'https://example.com/tags/classic',
    source: 'uitdatabank',
    type: 'theme',
    is_enabled: true,
    image: null,
    display_name: 'Classic',
    display_short_description: 'Classic theatre',
    display_excerpt: 'A short summary',
    display_url_title: 'classic',
    firstProductionStart: '2026-01-01T10:00:00Z',
    lastProductionEnd: '2026-01-31T10:00:00Z',
    name: { en: 'Classic' },
    excerpt: { en: 'A short summary' },
    short_description: { en: 'Classic theatre' },
    url_title: { en: 'classic' },
  }

  beforeEach(() => {
    mockedGet.mockReset()
  })

  describe('getTag', () => {
    it('fetches one tag by id', async () => {
      mockedGet.mockResolvedValue({ data: mockTag })

      const result = await getTag(9)

      expect(mockedGet).toHaveBeenCalledWith('/tags/9/')
      expect(result).toEqual(mockTag)
    })

    it('propagates ApiError to the caller', async () => {
      const error = new ApiError(404, 'The requested resource was not found.')
      mockedGet.mockRejectedValue(error)

      await expect(getTag(9)).rejects.toBe(error)
    })
  })

  describe('getTags', () => {
    it('fetches tags without options', async () => {
      const data: TagListResponse = {
        count: 1,
        next: null,
        previous: null,
        results: [mockTag],
      }
      mockedGet.mockResolvedValue({ data })

      const result = await getTags()

      expect(mockedGet).toHaveBeenCalledWith('/tags/', { params: {} })
      expect(result).toEqual(data)
    })

    it('includes page and page_size when pagination is provided', async () => {
      const data: TagListResponse = {
        count: 1,
        next: null,
        previous: null,
        results: [mockTag],
      }
      mockedGet.mockResolvedValue({ data })

      const result = await getTags({ page: 2, pageSize: 10 })

      expect(mockedGet).toHaveBeenCalledWith('/tags/', { params: { page: 2, page_size: 10 } })
      expect(result).toEqual(data)
    })

    it('forwards filters as query params', async () => {
      const data: TagListResponse = {
        count: 1,
        next: null,
        previous: null,
        results: [mockTag],
      }
      mockedGet.mockResolvedValue({ data })

      const filters = { type: 'theme', is_enabled: true, name: 'classic' }
      const result = await getTags({ filters })

      expect(mockedGet).toHaveBeenCalledWith('/tags/', { params: { ...filters } })
      expect(result).toEqual(data)
    })

    it('propagates ApiError to the caller', async () => {
      const error = new ApiError(500, 'Internal server error')
      mockedGet.mockRejectedValue(error)

      await expect(getTags()).rejects.toBe(error)
    })
  })
})
