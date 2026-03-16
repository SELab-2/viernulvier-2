import { api } from '../../../services/Api'
import { getPrice, getPrices, getPriceRank, getPriceRanks} from '../../../services/pricing/Pricing'
import { ApiError } from '../../../services/ApiTypes'

jest.mock('../../../services/Api', () => ({
  api: {
    get: jest.fn(),
  },
}))

const mockedApi = api as jest.Mocked<typeof api>

describe('Pricing service', () => {
  afterEach(() => {
    jest.clearAllMocks()
  })

  describe('prices', () => {
    it('fetches a single price by id', async () => {
      const mockPrice = {
        id: 1,
        type: 'student',
        visibility: 'public',
        membership: '',
        minimum: null,
        maximum: null,
        step: null,
        sort_order: 1,
        cineville_box: false,
        description: { en: 'Student', nl: 'Student' },
        display_description: 'Student',
      }

      mockedApi.get.mockResolvedValue({ data: mockPrice })

      const result = await getPrice(1)

      expect(mockedApi.get).toHaveBeenCalledWith('/prices/1/')
      expect(result).toEqual(mockPrice)
    })

    it('fetches the price list without options', async () => {
      const mockResponse = {
        count: 1,
        next: null,
        previous: null,
        results: [
          {
            id: 1,
            type: 'student',
            visibility: 'public',
            membership: '',
            minimum: null,
            maximum: null,
            step: null,
            sort_order: 1,
            cineville_box: false,
            description: { en: 'Student' },
            display_description: 'Student',
          },
        ],
      }

      mockedApi.get.mockResolvedValue({ data: mockResponse })

      const result = await getPrices()

      expect(mockedApi.get).toHaveBeenCalledWith('/prices/', {
        params: {},
      })
      expect(result).toEqual(mockResponse)
    })

    it('passes pagination and price filters correctly', async () => {
      mockedApi.get.mockResolvedValue({
        data: {
          count: 0,
          next: null,
          previous: null,
          results: [],
        },
      })

      await getPrices({
        page: 2,
        pageSize: 25,
        filters: {
          search: 'student',
          ordering: 'sort_order',
          type: 'student',
          visibility: 'public',
          membership: 'cineville',
          cineville_box: true,
          description: 'student',
        },
      })

      expect(mockedApi.get).toHaveBeenCalledWith('/prices/', {
        params: {
          page: 2,
          page_size: 25,
          search: 'student',
          ordering: 'sort_order',
          type: 'student',
          visibility: 'public',
          membership: 'cineville',
          cineville_box: true,
          description: 'student',
        },
      })
    })

    it('propagates ApiError from api interceptor on getPrices', async () => {
      const error = new ApiError(401, 'Not authenticated. Please log in.')
      mockedApi.get.mockRejectedValue(error)

      await expect(getPrices()).rejects.toBe(error)
    })

    it('propagates ApiError from api interceptor on getPrice', async () => {
      const error = new ApiError(404, 'The requested resource was not found.')
      mockedApi.get.mockRejectedValue(error)

      await expect(getPrice(1)).rejects.toBe(error)
    })
  })

  describe('price ranks', () => {
    it('fetches a single price rank by id', async () => {
      const mockPriceRank = {
        id: 1,
        position: 1,
        sold_out_buffer: 0,
        description: { en: 'Early Bird', nl: 'Vroege Vogel' },
        display_description: 'Early Bird',
      }

      mockedApi.get.mockResolvedValue({ data: mockPriceRank })

      const result = await getPriceRank(1)

      expect(mockedApi.get).toHaveBeenCalledWith('/price-ranks/1/')
      expect(result).toEqual(mockPriceRank)
    })

    it('fetches the price-rank list without options', async () => {
      const mockResponse = {
        count: 1,
        next: null,
        previous: null,
        results: [
          {
            id: 1,
            position: 1,
            sold_out_buffer: 0,
            description: { en: 'Early Bird' },
            display_description: 'Early Bird',
          },
        ],
      }

      mockedApi.get.mockResolvedValue({ data: mockResponse })

      const result = await getPriceRanks()

      expect(mockedApi.get).toHaveBeenCalledWith('/price-ranks/', {
        params: {},
      })
      expect(result).toEqual(mockResponse)
    })

    it('passes pagination and price-rank filters correctly', async () => {
      mockedApi.get.mockResolvedValue({
        data: {
          count: 0,
          next: null,
          previous: null,
          results: [],
        },
      })

      await getPriceRanks({
        page: 1,
        pageSize: 10,
        filters: {
          search: 'early',
          ordering: 'position',
          position: 1,
          position_gte: 1,
          position_lte: 5,
          description: 'student',
        },
      })

      expect(mockedApi.get).toHaveBeenCalledWith('/price-ranks/', {
        params: {
          page: 1,
          page_size: 10,
          search: 'early',
          ordering: 'position',
          position: 1,
          position_gte: 1,
          position_lte: 5,
          description: 'student',
        },
      })
    })

    it('propagates ApiError from api interceptor on getPriceRanks', async () => {
      const error = new ApiError(401, 'Not authenticated. Please log in.')
      mockedApi.get.mockRejectedValue(error)

      await expect(getPriceRanks()).rejects.toBe(error)
    })

    it('propagates ApiError from api interceptor on getPriceRank', async () => {
      const error = new ApiError(404, 'The requested resource was not found.')
      mockedApi.get.mockRejectedValue(error)

      await expect(getPriceRank(1)).rejects.toBe(error)
    })
  })
})
