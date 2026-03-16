import { api } from '../../../services/Api'
import { getSpace, getSpaces } from '../../../services/spaces/Spaces'

jest.mock('../../../services/Api', () => {
  const { buildListParams } = jest.requireActual('../../../services/ApiParams')

  return {
    buildListParams,
    api: {
      get: jest.fn(),
    },
  }
})

describe('locations service - spaces', () => {
  const mockedGet = api.get as jest.Mock

  beforeEach(() => {
    mockedGet.mockReset()
  })

  describe('getSpace', () => {
    it('fetches one space by id', async () => {
      const data = {
        id: 3,
        location: 7,
        name: { en: 'Main Building', nl: 'Hoofdgebouw' },
        display_name: 'Hoofdgebouw',
      }
      mockedGet.mockResolvedValue({ data })

      const result = await getSpace(3)

      expect(mockedGet).toHaveBeenCalledWith('/spaces/3/')
      expect(result).toEqual(data)
    })

    it('propagates errors to the caller', async () => {
      const error = new Error('request failed')
      mockedGet.mockRejectedValue(error)

      await expect(getSpace(3)).rejects.toThrow('request failed')
    })
  })

  describe('getSpaces', () => {
    it('fetches spaces without options', async () => {
      const data = {
        count: 1,
        next: null,
        previous: null,
        results: [
          {
            id: 3,
            location: 7,
            name: { en: 'Main Building', nl: 'Hoofdgebouw' },
            display_name: 'Hoofdgebouw',
          },
        ],
      }
      mockedGet.mockResolvedValue({ data })

      const result = await getSpaces()

      expect(mockedGet).toHaveBeenCalledWith('/spaces/', { params: {} })
      expect(result).toEqual(data)
    })

    it.each([
      { location: 7 },
      { name: 'foyer' },
      { search: 'stage' },
      { ordering: '-id' },
      { external_id: 'ext-1' },
    ])('applies %s filter', async (filters) => {
      mockedGet.mockResolvedValue({ data: { results: [] } })

      await getSpaces({ filters })

      expect(mockedGet).toHaveBeenCalledWith('/spaces/', { params: filters })
    })

    it('combines pagination and filters in params', async () => {
      mockedGet.mockResolvedValue({ data: { results: [] } })

      await getSpaces({
        page: 2,
        pageSize: 25,
        filters: {
          location: 7,
          name: 'foyer',
          search: 'stage',
          ordering: 'location',
          external_id: 'ext-8',
        },
      })

      expect(mockedGet).toHaveBeenCalledWith('/spaces/', {
        params: {
          page: 2,
          page_size: 25,
          location: 7,
          name: 'foyer',
          search: 'stage',
          ordering: 'location',
          external_id: 'ext-8',
        },
      })
    })

    it('propagates errors to the caller', async () => {
      const error = new Error('request failed')
      mockedGet.mockRejectedValue(error)

      await expect(getSpaces({ filters: { location: 1 } })).rejects.toThrow('request failed')
    })
  })
})
