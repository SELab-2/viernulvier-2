// src/services/media_files/MediaFiles.test.ts

import { getMediaFile, getMediaFiles } from '../../services/media_files/MediaFiles'
import { api } from '../../services/Api'
import { buildListParams } from '../../services/ApiParams'

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
    mime_type: 'application/pdf',
    size_bytes: 1234,
    file_type: 'pdf',
    uploaded_by: 'editor1',
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
      mockedApi.get.mockResolvedValueOnce({ data: listResponse })

      const result = await getMediaFiles()

      expect(mockedApi.get).toHaveBeenCalledWith('/media/', {
        params: undefined,
      })
      expect(result).toEqual(listResponse)
    })

    it('uses buildListParams when options are provided', async () => {
      mockedBuildListParams.mockReturnValue({
        page: 1,
        file_type: 'image',
      })

      mockedApi.get.mockResolvedValueOnce({ data: listResponse })

      const result = await getMediaFiles({
        page: 1,
        filters: { file_type: 'image' },
      })

      expect(mockedBuildListParams).toHaveBeenCalledWith({
        page: 1,
        filters: { file_type: 'image' },
      })

      expect(mockedApi.get).toHaveBeenCalledWith('/media/', {
        params: {
          page: 1,
          file_type: 'image',
        },
      })

      expect(result).toEqual(listResponse)
    })

    it('propagates errors', async () => {
      mockedApi.get.mockRejectedValueOnce(new Error('API error'))

      await expect(getMediaFiles()).rejects.toThrow('API error')
    })
  })
})
