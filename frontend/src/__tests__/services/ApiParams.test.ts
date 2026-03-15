import { buildListParams } from '../../services/ApiParams'

describe('buildListParams', () => {
  it('returns an empty object when no options are provided', () => {
    expect(buildListParams()).toEqual({})
  })

  it('includes page when provided', () => {
    expect(buildListParams({ page: 2 })).toEqual({ page: 2 })
  })

  it('includes page_size when pageSize is provided', () => {
    expect(buildListParams({ pageSize: 25 })).toEqual({ page_size: 25 })
  })

  it('keeps zero values for page and pageSize', () => {
    expect(buildListParams({ page: 0, pageSize: 0 })).toEqual({ page: 0, page_size: 0 })
  })

  it('includes only filters when pagination is omitted', () => {
    expect(
      buildListParams({
        filters: {
          type: 'theater',
          search: 'festival',
        },
      }),
    ).toEqual({
      type: 'theater',
      search: 'festival',
    })
  })

  it('combines pagination and filters into one params object', () => {
    expect(
      buildListParams({
        page: 3,
        pageSize: 10,
        filters: {
          use_as: 2,
          ordering: '-name',
          external_id: '/genres/123',
        },
      }),
    ).toEqual({
      page: 3,
      page_size: 10,
      use_as: 2,
      ordering: '-name',
      external_id: '/genres/123',
    })
  })

  it('does not mutate the original filters object', () => {
    const filters = {
      name: 'concert',
      search: 'live',
    }

    buildListParams({ page: 1, filters })

    expect(filters).toEqual({
      name: 'concert',
      search: 'live',
    })
  })
})
