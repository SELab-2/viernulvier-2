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
    id: '4f7ec8d0-6fd4-4d89-8f65-9d8d1f79b4b3',
    external_id: null,
    file: '/media/uploads/4f7ec8d0-6fd4-4d89-8f65-9d8d1f79b4b3.pdf',
    filename: 'season-brochure-2026.pdf',
    display_description: 'Final Dutch brochure version for the 2026 season.',
    description: {
      nl: 'Final Dutch brochure version for the 2026 season.',
      en: 'Final English brochure version for the 2026 season.',
    },
    mime_type: 'application/pdf',
    size_bytes: 2843921,
    file_type: 'pdf',
    created_at: '2026-04-08T10:12:00.000000Z',
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

      const result = await getMediaFile('4f7ec8d0-6fd4-4d89-8f65-9d8d1f79b4b3')

      expect(mockedApi.get).toHaveBeenCalledWith(
        '/media-files/4f7ec8d0-6fd4-4d89-8f65-9d8d1f79b4b3/',
      )
      expect(result).toEqual(mediaFile)
    })

    it('propagates errors', async () => {
      mockedApi.get.mockRejectedValueOnce(new Error('API error'))

      await expect(
        getMediaFile('4f7ec8d0-6fd4-4d89-8f65-9d8d1f79b4b3'),
      ).rejects.toThrow('API error')
    })
  })

  describe('getMediaFiles', () => {
    it('calls endpoint without params when no options provided', async () => {
      mockedBuildListParams.mockReturnValueOnce(undefined)
      mockedApi.get.mockResolvedValueOnce({ data: listResponse })

      const result = await getMediaFiles()

      expect(mockedBuildListParams).toHaveBeenCalledWith(undefined)
      expect(mockedApi.get).toHaveBeenCalledWith('/media-files/', {
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

      expect(mockedApi.get).toHaveBeenCalledWith('/media-files/', {
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
