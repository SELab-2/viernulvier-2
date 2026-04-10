import { ThemeProvider, createTheme } from '@mui/material/styles'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { I18nextProvider } from 'react-i18next'
import { MemoryRouter, useLocation } from 'react-router-dom'
import i18n from '../../i18n'
import BlogsPage from '../../pages/BlogsPage'
import { getBlogs } from '../../services/blogs/Blogs'
import type { Blog } from '../../types/Blogs'

jest.mock('../../services/blogs/Blogs', () => ({
  getBlogs: jest.fn(),
}))

const mockedGetBlogs = getBlogs as jest.MockedFunction<typeof getBlogs>

const LocationProbe = () => {
  const location = useLocation()
  return <div data-testid="url-search">{location.search}</div>
}

const buildBlog = (id: number): Blog => ({
  id,
  slug: `story-${id}`,
  published_at: '2026-01-01T19:00:00Z',
  cover_image: null,
  title: { nl: `Verhaal ${id}`, en: `Story ${id}` },
  body: { nl: `Body ${id}` },
  excerpt: { nl: `Samenvatting ${id}` },
  display_title: `Verhaal ${id}`,
  display_excerpt: `Samenvatting ${id}`,
  productions: [],
})

const renderPage = (initialPath = '/blogs') =>
  render(
    <MemoryRouter initialEntries={[initialPath]}>
      <I18nextProvider i18n={i18n}>
        <ThemeProvider theme={createTheme()}>
          <BlogsPage />
          <LocationProbe />
        </ThemeProvider>
      </I18nextProvider>
    </MemoryRouter>,
  )

describe('BlogsPage', () => {
  afterEach(() => {
    jest.clearAllMocks()
  })

  beforeEach(async () => {
    await i18n.changeLanguage('nl')
  })

  it('loads blogs from API with default params and renders results', async () => {
    mockedGetBlogs.mockResolvedValueOnce({
      count: 2,
      next: null,
      previous: null,
      results: [buildBlog(1), buildBlog(2)],
    })

    renderPage()

    await waitFor(() => {
      expect(mockedGetBlogs).toHaveBeenCalledWith({
        page: 1,
        pageSize: 12,
        filters: {
          published: true,
          search: undefined,
          ordering: '-published_at',
        },
      })
    })

    expect(await screen.findByRole('heading', { name: 'Verhaal 1' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Verhaal 2' })).toBeInTheDocument()
  })

  it('shows empty state when API returns no blogs', async () => {
    mockedGetBlogs.mockResolvedValueOnce({
      count: 0,
      next: null,
      previous: null,
      results: [],
    })

    renderPage()

    expect(await screen.findByText('Geen verhalen gevonden')).toBeInTheDocument()
    expect(screen.getByText('Pas je zoekopdracht aan en probeer opnieuw.')).toBeInTheDocument()
  })

  it('shows error state and retries after failure', async () => {
    mockedGetBlogs.mockRejectedValueOnce(new Error('network down')).mockResolvedValueOnce({
      count: 1,
      next: null,
      previous: null,
      results: [buildBlog(3)],
    })

    renderPage()

    expect(await screen.findByText('Kon verhalen niet laden.')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Opnieuw proberen' }))

    await waitFor(() => {
      expect(mockedGetBlogs).toHaveBeenCalledTimes(2)
    })
    expect(await screen.findByRole('heading', { name: 'Verhaal 3' })).toBeInTheDocument()
  })

  it('updates URL state when list view is selected', async () => {
    mockedGetBlogs.mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [buildBlog(4)],
    })

    renderPage()

    await screen.findByRole('heading', { name: 'Verhaal 4' })
    fireEvent.click(screen.getByRole('button', { name: 'Lijst' }))

    expect(screen.getByTestId('url-search')).toHaveTextContent('v=l')
  })

  it('does not refetch while typing and only searches on explicit submit', async () => {
    mockedGetBlogs
      .mockResolvedValueOnce({
        count: 1,
        next: null,
        previous: null,
        results: [buildBlog(5)],
      })
      .mockResolvedValueOnce({
        count: 1,
        next: null,
        previous: null,
        results: [buildBlog(6)],
      })

    renderPage()

    await screen.findByRole('heading', { name: 'Verhaal 5' })
    expect(mockedGetBlogs).toHaveBeenCalledTimes(1)

    fireEvent.change(screen.getByPlaceholderText('Zoek verhalen op titel of samenvatting...'), {
      target: { value: 'vooruit' },
    })

    expect(mockedGetBlogs).toHaveBeenCalledTimes(1)

    fireEvent.click(screen.getByRole('button', { name: 'Zoeken' }))

    await waitFor(() => {
      expect(mockedGetBlogs).toHaveBeenCalledTimes(2)
      expect(mockedGetBlogs).toHaveBeenLastCalledWith({
        page: 1,
        pageSize: 12,
        filters: {
          published: true,
          search: 'vooruit',
          ordering: '-published_at',
        },
      })
    })
  })
})
