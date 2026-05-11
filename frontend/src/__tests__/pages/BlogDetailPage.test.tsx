import { ThemeProvider, createTheme } from '@mui/material'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import BlogDetailPage from '../../pages/BlogDetailPage'
import { getBlog } from '../../services/blogs/Blogs'

import type { Blog } from '../../types/Blogs'

const languageState = { current: 'nl' }

jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    i18n: { language: languageState.current },
    t: (_key: string, defaultValue: string) => defaultValue,
  }),
}))

const mockNavigate = jest.fn()
const mockUseParams = jest.fn()

jest.mock('react-router-dom', () => ({
  ...(jest.requireActual('react-router-dom') as object),
  useParams: () => mockUseParams(),
  useNavigate: () => mockNavigate,
}))

jest.mock('../../services/blogs/Blogs', () => ({
  getBlog: jest.fn(),
}))

jest.mock('../../components/production/RelatedProductions', () => ({
  __esModule: true,
  default: () => <div data-testid="related-productions-mock" />,
}))

const mockedGetBlog = getBlog as jest.MockedFunction<typeof getBlog>

const renderPage = () =>
  render(
    <MemoryRouter>
      <ThemeProvider theme={createTheme()}>
        <BlogDetailPage />
      </ThemeProvider>
    </MemoryRouter>,
  )

describe('BlogDetailPage', () => {
  afterEach(() => {
    jest.clearAllMocks()
    mockedGetBlog.mockReset()
    languageState.current = 'nl'
  })

  it('shows invalid id error and navigates to blogs for non-numeric ID', async () => {
    mockUseParams.mockReturnValue({ id: 'abc' })

    renderPage()

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/nl/blogs', {
        state: {
          floatingAlert: {
            open: true,
            message: 'Invalid blog ID',
            severity: 'error',
          },
        },
      })
    })
  })

  it('renders blog title and published date and shows related productions', async () => {
    mockUseParams.mockReturnValue({ id: '12' })

    const blogData = {
      id: 12,
      slug: 'test-blog',
      published_at: '2025-10-05T12:00:00Z',
      cover_image: 'https://example.com/cover.jpg',
      title: { nl: 'Blog NL', en: 'Blog EN' },
      body: { nl: '<p>Body NL</p>' },
      excerpt: { nl: '<p>Excerpt NL</p>' },
      display_title: 'Display title',
      display_excerpt: 'Display excerpt',
      productions: [{ id: 1, display_title: 'Prod 1' }],
    } as unknown as Blog

    mockedGetBlog.mockResolvedValue(blogData)

    renderPage()

    renderPage()

    await waitFor(() => {
      // Use heading query to avoid matching the breadcrumb label duplicate
      expect(screen.getByRole('heading', { name: 'Blog NL' })).toBeInTheDocument()
      // Published on label should be present and year from the date appears
      expect(screen.getByText(/Published on/)).toBeInTheDocument()
      expect(screen.getByText(/2025/)).toBeInTheDocument()
      expect(screen.getByTestId('related-productions-mock')).toBeInTheDocument()
    })
  })

  it('handles unpublished blog by navigating to localized 404', async () => {
    mockUseParams.mockReturnValue({ id: '13' })

    const blogData = {
      id: 13,
      slug: 'draft-blog',
      published_at: null,
      cover_image: null,
      title: { nl: 'Draft NL' },
      body: { nl: '<p>Draft</p>' },
      excerpt: { nl: '<p>Draft</p>' },
      display_title: 'Draft',
      display_excerpt: 'Draft',
      productions: [],
    } as unknown as Blog

    mockedGetBlog.mockResolvedValue(blogData)

    renderPage()

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/nl/404', {
        state: {
          floatingAlert: {
            open: true,
            message: 'Could not load blog',
            severity: 'error',
          },
        },
      })
    })
  })

  it('handles fetch error by navigating to localized 404', async () => {
    mockUseParams.mockReturnValue({ id: '12' })
    mockedGetBlog.mockRejectedValue(new Error('network error'))

    renderPage()

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/nl/404', {
        state: {
          floatingAlert: {
            open: true,
            message: 'Could not load blog',
            severity: 'error',
          },
        },
      })
    })
  })
})
