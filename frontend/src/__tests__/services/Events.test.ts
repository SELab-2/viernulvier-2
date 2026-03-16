import { api } from '../../../src/services/Api'
import { getEvent, getEvents } from '../../../src/services/events/Events'
import { ApiError } from '../../../src/services/ApiTypes'

jest.mock('../../../src/services/Api', () => ({
  api: {
    get: jest.fn(),
  },
}))

const mockedApi = api as jest.Mocked<typeof api>

describe('Events service', () => {
  afterEach(() => {
    jest.clearAllMocks()
  })

  it('fetches a single event by id', async () => {
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

  it('fetches the event list without options', async () => {
    const mockResponse = {
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
    }

    mockedApi.get.mockResolvedValue({ data: mockResponse })

    const result = await getEvents()

    expect(mockedApi.get).toHaveBeenCalledWith('/events/', {
      params: {},
    })
    expect(result).toEqual(mockResponse)
  })

  it('passes pagination and standard filters correctly', async () => {
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
        location: 7,
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
        location: 7,
      },
    })
  })

  it('passes datetime filters correctly', async () => {
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
        starts_at_after: '2025-01-01T00:00:00Z',
        starts_at_before: '2025-12-31T23:59:59Z',
        ends_at_after: '2025-01-01T00:00:00Z',
        ends_at_before: '2025-12-31T23:59:59Z',
      },
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/events/', {
      params: {
        starts_at_after: '2025-01-01T00:00:00Z',
        starts_at_before: '2025-12-31T23:59:59Z',
        ends_at_after: '2025-01-01T00:00:00Z',
        ends_at_before: '2025-12-31T23:59:59Z',
      },
    })
  })

  it('propagates ApiError from api interceptor on getEvents', async () => {
    const error = new ApiError(401, 'Not authenticated. Please log in.')
    mockedApi.get.mockRejectedValue(error)

    await expect(getEvents()).rejects.toBe(error)
  })

  it('propagates ApiError from api interceptor on getEvent', async () => {
    const error = new ApiError(404, 'The requested resource was not found.')
    mockedApi.get.mockRejectedValue(error)

    await expect(getEvent(42)).rejects.toBe(error)
  })
})
