// src/services/media_files/MediaFiles.test.ts

import { api } from '../../services/Api'
import { buildListParams } from '../../services/ApiParams'
import { getMediaFile, getMediaFiles } from '../../services/media_files/MediaFiles'

jest.mock('../../services/Api', () => ({
  api: {
    get: jest.fn(),
  },
}))

jest.mock('../../services/ApiParams', () => ({
  buildListParams: jest.fn(),
}))

const mockedApi = api as jest.Mocked<typeof api>
const mockedBuildListParams = buildListParams as jest.Mock

describe('MediaFiles API service', () => {
  const mediaFile = {
    id: 'uuid-1',
    external_id: null,
    file: '/media/uploads/file.pdf',
    filename: 'file.pdf',
    description: 'Definitieve brochure voor het seizoen 2026.',
    mime_type: 'application/pdf',
    size_bytes: 1234,
    file_type: 'pdf',
    created_at: '2026-01-01T00:00:00Z',
  }

  const listResponse = {
    count: 1,
    next: null,
    previous: null,
    results: [mediaFile],
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('getMediaFile', () => {
    it('calls correct endpoint and returns data', async () => {
      mockedApi.get.mockResolvedValueOnce({ data: mediaFile })

      const result = await getMediaFile('uuid-1')

      expect(mockedApi.get).toHaveBeenCalledWith('/media/uuid-1/')
      expect(result).toEqual(mediaFile)
    })

    it('propagates errors', async () => {
      mockedApi.get.mockRejectedValueOnce(new Error('API error'))

      await expect(getMediaFile('uuid-1')).rejects.toThrow('API error')
    })
  })

  describe('getMediaFiles', () => {
    it('calls endpoint without params when no options provided', async () => {
      mockedBuildListParams.mockReturnValueOnce(undefined)
      mockedApi.get.mockResolvedValueOnce({ data: listResponse })

      const result = await getMediaFiles()

      expect(mockedBuildListParams).toHaveBeenCalledWith(undefined)
      expect(mockedApi.get).toHaveBeenCalledWith('/media/', {
        params: undefined,
      })
      expect(result).toEqual(listResponse)
    })

    it('uses buildListParams when options are provided', async () => {
      mockedBuildListParams.mockReturnValue({
        page: 1,
        file_type: 'image',
        description: 'poster',
      })

      mockedApi.get.mockResolvedValueOnce({ data: listResponse })

      const result = await getMediaFiles({
        page: 1,
        filters: { file_type: 'image', description: 'poster' },
      })

      expect(mockedBuildListParams).toHaveBeenCalledWith({
        page: 1,
        filters: { file_type: 'image', description: 'poster' },
      })

      expect(mockedApi.get).toHaveBeenCalledWith('/media/', {
        params: {
          page: 1,
          file_type: 'image',
          description: 'poster',
        },
      })

      expect(result).toEqual(listResponse)
    })

    it('propagates errors', async () => {
      mockedBuildListParams.mockReturnValueOnce(undefined)
      mockedApi.get.mockRejectedValueOnce(new Error('API error'))

      await expect(getMediaFiles()).rejects.toThrow('API error')
    })
  })
})
