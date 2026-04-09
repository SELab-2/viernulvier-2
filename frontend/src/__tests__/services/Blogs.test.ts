import { api } from '../../../src/services/Api'
import { getBlog, getBlogs } from '../../../src/services/blogs/Blogs'
import { ApiError } from '../../../src/services/ApiTypes'

jest.mock('../../../src/services/Api', () => ({
  api: {
    get: jest.fn(),
  },
}))

const mockedApi = api as jest.Mocked<typeof api>

const nestedProduction = {
  id: 101,
  attendance_mode: 'offline',
  performer_type: 'group',
  display_title: 'Collectief Morgen - De Laatste Avond',
  display_artist_name: 'Collectief Morgen',
  title: { nl: 'Collectief Morgen - De Laatste Avond' },
  artist_name: { nl: 'Collectief Morgen' },
  tags: [],
  genres: [],
}

describe('Blogs service', () => {
  afterEach(() => {
    jest.clearAllMocks()
  })

  it('fetches a single blog by id', async () => {
    const mockBlog = {
      id: 42,
      slug: 'i-love-techno-2024',
      published_at: '2024-11-15T10:00:00Z',
      cover_image: '/media/blog_covers/i-love-techno-2024.jpg',
      title: { nl: 'I Love Techno 2024: Een Terugblik', en: 'I Love Techno 2024: A Retrospective' },
      body: { nl: '<p>Een uitgebreide terugblik...</p>', en: '<p>An extensive look back...</p>' },
      excerpt: { nl: 'Een korte samenvatting', en: 'A brief summary' },
      display_title: 'I Love Techno 2024: Een Terugblik',
      display_excerpt: 'Een korte samenvatting',
      productions: [nestedProduction],
    }

    mockedApi.get.mockResolvedValue({ data: mockBlog })

    const result = await getBlog(42)

    expect(mockedApi.get).toHaveBeenCalledWith('/blogs/42/')
    expect(result).toEqual(mockBlog)
  })

  it('fetches the blog list without options', async () => {
    const mockResponse = {
      count: 1,
      next: null,
      previous: null,
      results: [
        {
          id: 42,
          slug: 'vooruit-100-years',
          published_at: '2024-03-20T14:30:00Z',
          cover_image: '/media/blog_covers/vooruit-100.jpg',
          title: { nl: '100 Jaar Vooruit' },
          body: { nl: '<p>Een historisch overzicht...</p>' },
          excerpt: { nl: 'Een historisch overzicht' },
          display_title: '100 Jaar Vooruit',
          display_excerpt: 'Een historisch overzicht',
          productions: [nestedProduction],
        },
      ],
    }

    mockedApi.get.mockResolvedValue({ data: mockResponse })

    const result = await getBlogs()

    expect(mockedApi.get).toHaveBeenCalledWith('/blogs/', {
      params: {},
    })
    expect(result).toEqual(mockResponse)
  })

  it('passes pagination and filters correctly', async () => {
    mockedApi.get.mockResolvedValue({ data: { count: 0, next: null, previous: null, results: [] } })

    await getBlogs({
      page: 3,
      pageSize: 10,
      filters: {
        search: 'vooruit',
        ordering: '-published_at',
        production: 101,
        published: true,
        slug: 'vooruit-100-years',
        title: 'Vooruit',
      },
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/blogs/', {
      params: {
        page: 3,
        page_size: 10,
        search: 'vooruit',
        ordering: '-published_at',
        production: 101,
        published: true,
        slug: 'vooruit-100-years',
        title: 'Vooruit',
      },
    })
  })

  it('propagates ApiError from api interceptor on getBlogs', async () => {
    const error = new ApiError(401, 'Not authenticated')
    mockedApi.get.mockRejectedValue(error)

    await expect(getBlogs()).rejects.toBe(error)
  })

  it('propagates ApiError from api interceptor on getBlog', async () => {
    const error = new ApiError(404, 'Not found')
    mockedApi.get.mockRejectedValue(error)

    await expect(getBlog(99)).rejects.toBe(error)
  })
})
