import { api } from '../../services/Api'
import { getHall, getHalls } from '../../services/halls/Halls'

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

jest.mock('../../services/Api', () => {
  const { buildListParams } = jest.requireActual('../../services/ApiParams')

  return {
    buildListParams,
    api: {
      get: jest.fn(),
    },
  }
})

describe('locations service - halls', () => {
  const mockedGet = api.get as jest.Mock

  beforeEach(() => {
    mockedGet.mockReset()
  })

  describe('getHall', () => {
    it('fetches one hall by id', async () => {
      const data = {
        id: 5,
        space: {
          id: 3,
          location: nestedLocation,
          name: { en: 'Main Building', nl: 'Hoofdgebouw' },
          display_name: 'Hoofdgebouw',
        },
        seat_selection: true,
        open_seating: false,
        name: { en: 'Main Hall', nl: 'Grote Zaal' },
        display_name: 'Grote Zaal',
        remark: { en: 'Accessible', nl: 'Toegankelijk' },
      }
      mockedGet.mockResolvedValue({ data })

      const result = await getHall(5)

      expect(mockedGet).toHaveBeenCalledWith('/halls/5/')
      expect(result).toEqual(data)
    })

    it('propagates errors to the caller', async () => {
      const error = new Error('request failed')
      mockedGet.mockRejectedValue(error)

      await expect(getHall(5)).rejects.toThrow('request failed')
    })
  })

  describe('getHalls', () => {
    it('fetches halls without options', async () => {
      const data = {
        count: 1,
        next: null,
        previous: null,
        results: [
          {
            id: 5,
            space: {
              id: 3,
              location: nestedLocation,
              name: { en: 'Main Building', nl: 'Hoofdgebouw' },
              display_name: 'Hoofdgebouw',
            },
            seat_selection: true,
            open_seating: false,
            name: { en: 'Main Hall', nl: 'Grote Zaal' },
            display_name: 'Grote Zaal',
            remark: { en: 'Accessible', nl: 'Toegankelijk' },
          },
        ],
      }
      mockedGet.mockResolvedValue({ data })

      const result = await getHalls()

      expect(mockedGet).toHaveBeenCalledWith('/halls/', { params: {} })
      expect(result).toEqual(data)
    })

    it.each([
      { space: 3 },
      { location: 7 },
      { seat_selection: true },
      { open_seating: false },
      { name: 'grote zaal' },
      { search: 'hall' },
      { ordering: '-space' },
      { external_id: 'ext-2' },
    ])('applies %s filter', async (filters) => {
      mockedGet.mockResolvedValue({ data: { results: [] } })

      await getHalls({ filters })

      expect(mockedGet).toHaveBeenCalledWith('/halls/', { params: filters })
    })

    it('combines pagination and filters in params', async () => {
      mockedGet.mockResolvedValue({ data: { results: [] } })

      await getHalls({
        page: 4,
        pageSize: 10,
        filters: {
          space: 3,
          location: 7,
          seat_selection: true,
          open_seating: false,
          name: 'grote zaal',
          search: 'hall',
          ordering: 'space',
          external_id: 'ext-9',
        },
      })

      expect(mockedGet).toHaveBeenCalledWith('/halls/', {
        params: {
          page: 4,
          page_size: 10,
          space: 3,
          location: 7,
          seat_selection: true,
          open_seating: false,
          name: 'grote zaal',
          search: 'hall',
          ordering: 'space',
          external_id: 'ext-9',
        },
      })
    })

    it('propagates errors to the caller', async () => {
      const error = new Error('request failed')
      mockedGet.mockRejectedValue(error)

      await expect(getHalls({ filters: { space: 3 } })).rejects.toThrow('request failed')
    })
  })
})
