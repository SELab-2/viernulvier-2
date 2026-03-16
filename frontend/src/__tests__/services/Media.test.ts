import { api } from '../../services/Api'
import {
    getMediaGalleries,
    getMediaGallery,
    getMediaItems,
    getMediaItem,
} from '../../services/media/Media'
import { ApiError } from '../../services/ApiTypes'

jest.mock('../../services/Api', () => ({
    api: {
        get: jest.fn(),
    },
}))

const mockedApi = api as jest.Mocked<typeof api>

describe('Media service', () => {
    afterEach(() => {
        jest.clearAllMocks()
    })

    const mockGallery = {
        id: 1,
        name: 'Season 2025',
        media_items: [],
    }

    const mockItem = {
        id: 10,
        gallery: 1,
        type: 'foto' as const,
        format: 'jpg',
        original_filename: 'poster.jpg',
        position: 0,
        width: 1920,
        height: 1080,
        title: { en: 'Poster', nl: 'Affiche' },
        display_title: 'Poster',
        description: null,
        credits: null,
        link: null,
        crops: [{ id: 1, name: 'thumbnail', image_url: 'https://example.com/thumb.jpg' }],
    }

    describe('getMediaGalleries', () => {
        it('fetches gallery list', async () => {
            const mockResponse = { count: 1, next: null, previous: null, results: [mockGallery] }
            mockedApi.get.mockResolvedValue({ data: mockResponse })

            const result = await getMediaGalleries()

            expect(mockedApi.get).toHaveBeenCalledWith('/media-galleries/', { params: {} })
            expect(result).toEqual(mockResponse)
        })

        it('propagates errors to the caller', async () => {
            mockedApi.get.mockRejectedValue(new ApiError(500, 'Internal server error'))

            await expect(getMediaGalleries()).rejects.toBeInstanceOf(ApiError)
        })

        it('passes filters and pagination as query params', async () => {
            const mockResponse = { count: 1, next: null, previous: null, results: [mockGallery] }
            mockedApi.get.mockResolvedValue({ data: mockResponse })

            await getMediaGalleries({ page: 2, pageSize: 10, filters: { name: 'season' } })

            expect(mockedApi.get).toHaveBeenCalledWith('/media-galleries/', {
                params: { page: 2, page_size: 10, name: 'season' },
            })
        })
    })

    describe('getMediaGallery', () => {
        it('fetches a single gallery by id', async () => {
            mockedApi.get.mockResolvedValue({ data: mockGallery })

            const result = await getMediaGallery(1)

            expect(mockedApi.get).toHaveBeenCalledWith('/media-galleries/1/')
            expect(result).toEqual(mockGallery)
        })

        it('propagates errors to the caller', async () => {
            mockedApi.get.mockRejectedValue(new ApiError(404, 'Not found'))

            await expect(getMediaGallery(999)).rejects.toBeInstanceOf(ApiError)
        })
    })

    describe('getMediaItems', () => {
        it('fetches media item list', async () => {
            const mockResponse = { count: 1, next: null, previous: null, results: [mockItem] }
            mockedApi.get.mockResolvedValue({ data: mockResponse })

            const result = await getMediaItems()

            expect(mockedApi.get).toHaveBeenCalledWith('/media-items/', { params: {} })
            expect(result).toEqual(mockResponse)
        })

        it('passes filters and pagination as query params', async () => {
            const mockResponse = { count: 1, next: null, previous: null, results: [mockItem] }
            mockedApi.get.mockResolvedValue({ data: mockResponse })

            await getMediaItems({ page: 1, filters: { type: 'foto', gallery: 1 } })

            expect(mockedApi.get).toHaveBeenCalledWith('/media-items/', {
                params: { page: 1, type: 'foto', gallery: 1 },
            })
        })
    })

    describe('getMediaItem', () => {
        it('fetches a single media item by id', async () => {
            mockedApi.get.mockResolvedValue({ data: mockItem })

            const result = await getMediaItem(10)

            expect(mockedApi.get).toHaveBeenCalledWith('/media-items/10/')
            expect(result).toEqual(mockItem)
        })
    })
})
