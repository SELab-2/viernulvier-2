import { api } from '../../../src/services/Api'
import { getEvent, getEvents } from '../../../src/services/events/Events'
import { ApiError } from '../../../src/services/ApiTypes'

const nestedGenreUseAs = { id: 2, name: 'genre' }

const nestedProduction = {
  id: 1,
  attendance_mode: 'offline',
  performer_type: 'group',
  uit_database_type: { id: 6, name: 'Voorstelling' },
  display_title: 'Hamlet',
  display_artist_name: 'Toneelhuis',
  title: { en: 'Hamlet', nl: 'Hamlet' },
  artist_name: { en: 'Toneelhuis', nl: 'Toneelhuis' },
  tagline: { en: 'A classic', nl: 'Een klassieker' },
  teaser: { en: 'Short teaser', nl: 'Korte teaser' },
  description: { en: 'Long description', nl: 'Lange beschrijving' },
  tags: [],
  genres: [
    {
      id: 10,
      type: 'theater',
      use_as: nestedGenreUseAs,
      name: { en: 'Theatre', nl: 'Theater' },
      display_name: 'Theater',
      vendor_id: 'vendor-42',
    },
  ],
}

const nestedLocation = {
  id: 7,
  street: 'Veldstraat',
  number: '12',
  postal_code: '9000',
  city: 'Ghent',
  country: 'BE',
  phone_1: '+3290000001',
  phone_2: null,
  is_own_location: true,
  name: { en: 'City Hall', nl: 'Stadshal' },
  display_name: 'Stadshal',
}

const nestedHall = {
  id: 3,
  space: {
    id: 9,
    location: nestedLocation,
    name: { en: 'Main Building', nl: 'Hoofdgebouw' },
    display_name: 'Hoofdgebouw',
  },
  seat_selection: true,
  open_seating: false,
  name: { en: 'Main Hall', nl: 'Grote Zaal' },
  display_name: 'Main Hall',
  remark: { en: 'Accessible', nl: 'Toegankelijk' },
}

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
      production: nestedProduction,
      production_display: 'Hamlet',
      hall: nestedHall,
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
          production: nestedProduction,
          production_display: 'Hamlet',
          hall: nestedHall,
          hall_display: 'Main Hall',
          starts_at: '2025-09-15T19:30:00Z',
          ends_at: '2025-09-15T21:30:00Z',
          prices: [
            {
              id: 101,
              event: 42,
              price_rank: {
                id: 1,
                position: 1,
                sold_out_buffer: 0,
                description: { en: 'Standard', nl: 'Standaard' },
                display_description: 'Standard',
              },
              price_rank_display: 'Standard',
              price: {
                id: 1,
                type: 'standard',
                visibility: 'public',
                membership: '',
                minimum: null,
                maximum: null,
                step: null,
                sort_order: 1,
                cineville_box: false,
                description: { en: 'Regular', nl: 'Normaal' },
                display_description: 'Regular',
              },
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
