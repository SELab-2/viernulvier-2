import { api } from '../services/Api'
import { getEvent, getEvents } from '../services/events/Events'
import { ApiError } from '../services/ApiTypes'

jest.mock('../services/Api', () => ({
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
          prices: [],
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

  it('passes pagination and filters correctly', async () => {
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

  it('omits undefined filter values', async () => {
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
        production: 1,
        hall: undefined,
        search: undefined,
      },
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/events/', {
      params: {
        production: 1,
      },
    })
  })

  it('propagates ApiError from api interceptor', async () => {
    const error = new ApiError(401, 'Not authenticated. Please log in.')
    mockedApi.get.mockRejectedValue(error)

    await expect(getEvents()).rejects.toBe(error)
  })
})