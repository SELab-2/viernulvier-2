import { api } from '../../services/Api'
import { getLocation, getLocations } from '../../services/locations/Locations'

jest.mock('../../services/Api', () => {
  const { buildListParams } = jest.requireActual('../../services/ApiParams')

  return {
    buildListParams,
    api: {
      get: jest.fn(),
    },
  }
})

describe('locations service - locations', () => {
  const mockedGet = api.get as jest.Mock

  const expectLocationShape = (location: {
    id: unknown
    street: unknown
    number: unknown
    postal_code: unknown
    city: unknown
    country: unknown
    phone_1: unknown
    phone_2: unknown
    is_own_location: unknown
    name: unknown
    display_name: unknown
  }) => {
    expect(typeof location.id).toBe('number')

    if (location.street !== null) {
      expect(typeof location.street).toBe('string')
    }

    if (location.number !== null) {
      expect(typeof location.number).toBe('string')
    }

    if (location.postal_code !== null) {
      expect(typeof location.postal_code).toBe('string')
    }

    if (location.city !== null) {
      expect(typeof location.city).toBe('string')
    }

    expect(typeof location.country).toBe('string')

    if (location.phone_1 !== null) {
      expect(typeof location.phone_1).toBe('string')
    }

    if (location.phone_2 !== null) {
      expect(typeof location.phone_2).toBe('string')
    }

    expect(typeof location.is_own_location).toBe('boolean')

    if (location.name !== null) {
      expect(typeof location.name).toBe('object')
    }

    if (location.display_name !== null) {
      expect(typeof location.display_name).toBe('string')
    }
  }

  beforeEach(() => {
    mockedGet.mockReset()
  })

  describe('getLocation', () => {
    it('fetches one location by id', async () => {
      const data = {
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
      mockedGet.mockResolvedValue({ data })

      const result = await getLocation(7)

      expect(mockedGet).toHaveBeenCalledWith('/locations/7/')
      expect(result).toEqual(data)
      expectLocationShape(result)
    })

    it('propagates errors to the caller', async () => {
      const error = new Error('request failed')
      mockedGet.mockRejectedValue(error)

      await expect(getLocation(7)).rejects.toThrow('request failed')
    })
  })

  describe('getLocations', () => {
    it('fetches locations without options', async () => {
      const data = {
        count: 1,
        next: null,
        previous: null,
        results: [
          {
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
          },
        ],
      }
      mockedGet.mockResolvedValue({ data })

      const result = await getLocations()

      expect(mockedGet).toHaveBeenCalledWith('/locations/', { params: {} })
      expect(result).toEqual(data)
      expectLocationShape(result.results[0])
    })

    it('includes page in params when provided', async () => {
      mockedGet.mockResolvedValue({ data: { results: [] } })

      await getLocations({ page: 2 })

      expect(mockedGet).toHaveBeenCalledWith('/locations/', { params: { page: 2 } })
    })

    it('includes page_size in params when pageSize is provided', async () => {
      mockedGet.mockResolvedValue({ data: { results: [] } })

      await getLocations({ pageSize: 25 })

      expect(mockedGet).toHaveBeenCalledWith('/locations/', { params: { page_size: 25 } })
    })

    it.each([
      { city: 'ghent' },
      { country: 'BE' },
      { postal_code: '9000' },
      { is_own_location: true },
      { name: 'stadshal' },
      { search: 'venue' },
      { ordering: '-city' },
      { external_id: 'ext-001' },
    ])('applies %s filter', async (filters) => {
      mockedGet.mockResolvedValue({ data: { results: [] } })

      await getLocations({ filters })

      expect(mockedGet).toHaveBeenCalledWith('/locations/', { params: filters })
    })

    it('combines pagination and all filters in params', async () => {
      mockedGet.mockResolvedValue({ data: { results: [] } })

      await getLocations({
        page: 3,
        pageSize: 10,
        filters: {
          city: 'ghent',
          country: 'BE',
          postal_code: '9000',
          is_own_location: false,
          name: 'hall',
          search: 'venue',
          ordering: 'city',
          external_id: 'ext-9',
        },
      })

      expect(mockedGet).toHaveBeenCalledWith('/locations/', {
        params: {
          page: 3,
          page_size: 10,
          city: 'ghent',
          country: 'BE',
          postal_code: '9000',
          is_own_location: false,
          name: 'hall',
          search: 'venue',
          ordering: 'city',
          external_id: 'ext-9',
        },
      })
    })

    it('propagates errors to the caller', async () => {
      const error = new Error('request failed')
      mockedGet.mockRejectedValue(error)

      await expect(getLocations({ filters: { city: 'ghent' } })).rejects.toThrow('request failed')
    })
  })
})
