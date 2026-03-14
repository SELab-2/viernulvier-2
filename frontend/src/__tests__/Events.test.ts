import { getEvent, getEvents } from '../services/events/events'
import { api } from '../services/api'
import { ApiError } from '../services/apiTypes'

jest.mock('../services/api', () => ({
  api: {
    get: jest.fn(),
  },
}))

const mockedApi = api as jest.Mocked<typeof api>

describe('events service', () => {
  afterEach(() => {
    jest.clearAllMocks()
  })

  it('fetches the event list', async () => {
    const mockResponse = {
      data: {
        count: 1,
        next: null,
        previous: null,
        results: [
          {
            id: 42,
            production: 1,
            production_display: 'Hamlet',
            hall: 3,
            hall_display: 'Main Hall',
            starts_at: '2025-09-15T19:30:00Z',
            ends_at: '2025-09-15T21:30:00Z',
            prices: [
              {
                id: 101,
                event: 42,
                price_rank: 1,
                price_rank_display: 'Standard',
                price: 1,
                price_display: 'Regular',
                amount: '18.00',
                available: 120,
              },
            ],
          },
        ],
      },
    }

    mockedApi.get.mockResolvedValue(mockResponse)

    const result = await getEvents()

    expect(mockedApi.get).toHaveBeenCalledWith('/events/', {
      params: {},
    })
    expect(result).toEqual(mockResponse.data)
  })

  it('passes pagination, search, ordering, and filters', async () => {
    mockedApi.get.mockResolvedValue({
      data: {
        count: 0,
        next: null,
        previous: null,
        results: [],
      },
    })

    await getEvents({
      page: 2,
      pageSize: 25,
      filters: {
        search: 'hamlet',
        ordering: '-starts_at',
        production: 1,
        hall: 3,
      },
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/events/', {
      params: {
        page: 2,
        page_size: 25,
        search: 'hamlet',
        ordering: '-starts_at',
        production: 1,
        hall: 3,
      },
    })
  })

  it('omits undefined, null, and empty-string filter values', async () => {
    mockedApi.get.mockResolvedValue({
      data: {
        count: 0,
        next: null,
        previous: null,
        results: [],
      },
    })

    await getEvents({
      filters: {
        search: '',
        production: 1,
        hall: undefined,
        location: null as unknown as number,
      },
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/events/', {
      params: {
        production: 1,
      },
    })
  })

  it('fetches a single event', async () => {
    const mockEvent = {
      id: 42,
      production: 1,
      production_display: 'Hamlet',
      hall: 3,
      hall_display: 'Main Hall',
      starts_at: '2025-09-15T19:30:00Z',
      ends_at: '2025-09-15T21:30:00Z',
      prices: [],
    }

    mockedApi.get.mockResolvedValue({ data: mockEvent })

    const result = await getEvent(42)

    expect(mockedApi.get).toHaveBeenCalledWith('/events/42/')
    expect(result).toEqual(mockEvent)
  })

  it('propagates ApiError from the shared api instance', async () => {
    const error = new ApiError(401, 'Not authenticated. Please log in.')
    mockedApi.get.mockRejectedValue(error)

    await expect(getEvents()).rejects.toBe(error)
  })
})