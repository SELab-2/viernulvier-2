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
const mockedBuildListParams = buildListParams as jest.MockedFunction<typeof buildListParams>

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
    file_type: 'pdf' as const,
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
    it('calls the detail endpoint and returns the response data', async () => {
      mockedApi.get.mockResolvedValueOnce({ data: mediaFile })

      const result = await getMediaFile('4f7ec8d0-6fd4-4d89-8f65-9d8d1f79b4b3')

      expect(mockedApi.get).toHaveBeenCalledWith('/media/4f7ec8d0-6fd4-4d89-8f65-9d8d1f79b4b3/')
      expect(result).toEqual(mediaFile)
    })

    it('propagates detail endpoint errors', async () => {
      const error = new Error('API error')
      mockedApi.get.mockRejectedValueOnce(error)

      await expect(getMediaFile('4f7ec8d0-6fd4-4d89-8f65-9d8d1f79b4b3')).rejects.toThrow(error)
    })
  })

  describe('getMediaFiles', () => {
    it('calls the list endpoint without params when no options are provided', async () => {
      mockedBuildListParams.mockReturnValueOnce({})
      mockedApi.get.mockResolvedValueOnce({ data: listResponse })

      const result = await getMediaFiles()

      expect(mockedBuildListParams).toHaveBeenCalledWith(undefined)
      expect(mockedApi.get).toHaveBeenCalledWith('/media/', {
        params: {},
      })
      expect(result).toEqual(listResponse)
    })

    it('passes built params to the list endpoint when options are provided', async () => {
      mockedBuildListParams.mockReturnValueOnce({
        page: 1,
        page_size: 12,
        search: 'poster',
        description: 'poster',
        ordering: '-created_at',
      })

      mockedApi.get.mockResolvedValueOnce({ data: listResponse })

      const result = await getMediaFiles({
        page: 1,
        pageSize: 12,
        filters: {
          search: 'poster',
          description: 'poster',
          ordering: '-created_at',
        },
      })

      expect(mockedBuildListParams).toHaveBeenCalledWith({
        page: 1,
        pageSize: 12,
        filters: {
          search: 'poster',
          description: 'poster',
          ordering: '-created_at',
        },
      })

      expect(mockedApi.get).toHaveBeenCalledWith('/media/', {
        params: {
          page: 1,
          page_size: 12,
          search: 'poster',
          description: 'poster',
          ordering: '-created_at',
        },
      })
      expect(result).toEqual(listResponse)
    })

    it('propagates list endpoint errors', async () => {
      const error = new Error('API error')
      mockedBuildListParams.mockReturnValueOnce({})
      mockedApi.get.mockRejectedValueOnce(error)

      await expect(getMediaFiles()).rejects.toThrow(error)
    })
  })
})
