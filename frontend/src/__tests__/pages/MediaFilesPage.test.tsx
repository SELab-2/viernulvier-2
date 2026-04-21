import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import React from 'react'

import { useSearchBarUrlState } from '../../components/searchbar/useSearchBarUrlState'
import MediaFilesPage from '../../pages/MediaFilesPage'
import { ApiError } from '../../services/ApiTypes'
import { getMediaFiles } from '../../services/media_files/MediaFiles'

jest.mock('@mui/material', () => {
  const actual = jest.requireActual('@mui/material')
  return {
    ...actual,
    useTheme: () => ({
      breakpoints: {
        down: () => 'mocked-breakpoint',
      },
      palette: {
        mode: 'light',
      },
    }),
    useMediaQuery: jest.fn(() => false),
  }
})

jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: { language: 'nl' },
  }),
}))

jest.mock('../../components/searchbar/useSearchBarUrlState', () => ({
  useSearchBarUrlState: jest.fn(),
}))

jest.mock('../../components/CollectionPageLayout', () => ({
  __esModule: true,
  default: ({
    resultCount,
    isLoading,
    loadingContent,
    errorMessage,
    hasResults,
    resultsContent,
    retryLabel,
    onRetry,
    page,
    pageSize,
    totalItems,
    onPageChange,
  }: any) => (
    <div>
      <div data-testid="result-count">{resultCount}</div>
      <div data-testid="is-loading">{String(isLoading)}</div>
      <div data-testid="error-message">{errorMessage ?? ''}</div>
      <div data-testid="has-results">{String(hasResults)}</div>
      <div data-testid="current-page">{page}</div>
      <div data-testid="page-size">{pageSize}</div>
      <div data-testid="total-items">{totalItems}</div>
      <button type="button" onClick={onRetry}>
        {retryLabel}
      </button>
      <button type="button" onClick={() => onPageChange(page + 1)}>
        go-to-next-page
      </button>
      <div data-testid="loading-content">{isLoading ? loadingContent : null}</div>
      <div data-testid="results-content">{!isLoading ? resultsContent : null}</div>
    </div>
  ),
}))

jest.mock('../../components/FloatingAlert', () => ({
  __esModule: true,
  default: ({ open, message }: { open: boolean; message: string }) =>
    open ? <div data-testid="floating-alert">{message}</div> : null,
}))

jest.mock('../../pages/MediaFilesPageSkeleton', () => ({
  __esModule: true,
  default: () => <div data-testid="page-skeleton" />,
}))

jest.mock('../../services/media_files/MediaFiles', () => ({
  getMediaFiles: jest.fn(),
}))

jest.mock('../../utils/localization', () => ({
  getLocalizedValue: jest.fn(
    (value: Record<string, string>, locale: string) => value?.[locale] ?? null,
  ),
}))

jest.mock('../../services/ApiTypes', () => ({
  ApiError: class ApiError extends Error {
    status: number

    constructor(status: number, message: string) {
      super(message)
      this.name = 'ApiError'
      this.status = status
    }
  },
}))

const mockedGetMediaFiles = getMediaFiles as jest.MockedFunction<typeof getMediaFiles>
const mockedUseSearchBarUrlState = useSearchBarUrlState as jest.MockedFunction<
  typeof useSearchBarUrlState
>

function buildSearchBarState(overrides?: Record<string, unknown>) {
  return {
    searchValue: '',
    sortTarget: 'date',
    sortDirection: 'desc',
    viewMode: 'grid',
    page: 1,
    setSearchValue: jest.fn(),
    setSortTarget: jest.fn(),
    setSortDirection: jest.fn(),
    setViewMode: jest.fn(),
    setPage: jest.fn(),
    ...overrides,
  }
}

describe('MediaFilesPage', () => {
  const mediaFile = {
    id: '1',
    external_id: null,
    file: '/media/uploads/poster.jpg',
    filename: 'poster.jpg',
    display_description: 'Poster description',
    description: { nl: 'Poster description' },
    mime_type: 'image/jpeg',
    size_bytes: 1024,
    file_type: 'image' as const,
    created_at: '2026-04-08T10:12:00.000000Z',
  }

  beforeEach(() => {
    jest.clearAllMocks()
    mockedUseSearchBarUrlState.mockReturnValue(buildSearchBarState() as any)
  })

  it('shows skeleton while loading', async () => {
    mockedGetMediaFiles.mockReturnValue(new Promise(() => {}))

    render(<MediaFilesPage />)

    expect(screen.getByTestId('page-skeleton')).toBeInTheDocument()
  })

  it('loads media files and does not show an error when the request succeeds', async () => {
    mockedGetMediaFiles.mockResolvedValueOnce({
      count: 1,
      next: null,
      previous: null,
      results: [mediaFile],
    })

    render(<MediaFilesPage />)

    await waitFor(() => {
      expect(mockedGetMediaFiles).toHaveBeenCalledWith({
        page: 1,
        pageSize: 12,
        filters: {
          search: undefined,
          ordering: '-created_at',
        },
      })
    })

    expect(await screen.findByText('poster.jpg')).toBeInTheDocument()
    expect(screen.getByTestId('result-count')).toHaveTextContent('1')
    expect(screen.getByTestId('has-results')).toHaveTextContent('true')
    expect(screen.getByTestId('error-message')).toHaveTextContent('')
    expect(screen.getByTestId('current-page')).toHaveTextContent('1')
    expect(screen.getByTestId('page-size')).toHaveTextContent('12')
    expect(screen.getByTestId('total-items')).toHaveTextContent('1')
    expect(screen.queryByTestId('floating-alert')).not.toBeInTheDocument()
  })

  it('renders an open file button with the correct link attributes', async () => {
    mockedGetMediaFiles.mockResolvedValueOnce({
      count: 1,
      next: null,
      previous: null,
      results: [mediaFile],
    })

    render(<MediaFilesPage />)

    const openLink = await screen.findByRole('link', { name: 'media.openFile' })

    expect(openLink).toHaveAttribute('href', '/media/uploads/poster.jpg')
    expect(openLink).toHaveAttribute('target', '_blank')
    expect(openLink).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('uses filename ordering when sorting by name ascending', async () => {
    mockedUseSearchBarUrlState.mockReturnValue(
      buildSearchBarState({
        sortTarget: 'name',
        sortDirection: 'asc',
      }) as any,
    )

    mockedGetMediaFiles.mockResolvedValueOnce({
      count: 1,
      next: null,
      previous: null,
      results: [mediaFile],
    })

    render(<MediaFilesPage />)

    await waitFor(() => {
      expect(mockedGetMediaFiles).toHaveBeenCalledWith({
        page: 1,
        pageSize: 12,
        filters: {
          search: undefined,
          ordering: 'filename',
        },
      })
    })
  })

  it('uses descending filename ordering when sorting by name descending', async () => {
    mockedUseSearchBarUrlState.mockReturnValue(
      buildSearchBarState({
        sortTarget: 'name',
        sortDirection: 'desc',
      }) as any,
    )

    mockedGetMediaFiles.mockResolvedValueOnce({
      count: 1,
      next: null,
      previous: null,
      results: [mediaFile],
    })

    render(<MediaFilesPage />)

    await waitFor(() => {
      expect(mockedGetMediaFiles).toHaveBeenCalledWith({
        page: 1,
        pageSize: 12,
        filters: {
          search: undefined,
          ordering: '-filename',
        },
      })
    })
  })

  it('calls setPage with the next page when pagination changes', async () => {
    const setPage = jest.fn()

    mockedUseSearchBarUrlState.mockReturnValue(
      buildSearchBarState({
        page: 1,
        setPage,
      }) as any,
    )

    mockedGetMediaFiles.mockResolvedValueOnce({
      count: 24,
      next: '/api/v1/media/?page=2',
      previous: null,
      results: [mediaFile],
    })

    render(<MediaFilesPage />)

    expect(await screen.findByText('poster.jpg')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'go-to-next-page' }))

    expect(setPage).toHaveBeenCalledWith(2)
  })

  it('requests page 2 when the current page is 2', async () => {
    mockedUseSearchBarUrlState.mockReturnValue(
      buildSearchBarState({
        page: 2,
      }) as any,
    )

    mockedGetMediaFiles.mockResolvedValueOnce({
      count: 24,
      next: null,
      previous: '/api/v1/media/?page=1',
      results: [
        {
          ...mediaFile,
          id: '2',
          filename: 'second-page-file.jpg',
        },
      ],
    })

    render(<MediaFilesPage />)

    await waitFor(() => {
      expect(mockedGetMediaFiles).toHaveBeenCalledWith({
        page: 2,
        pageSize: 12,
        filters: {
          search: undefined,
          ordering: '-created_at',
        },
      })
    })

    expect(await screen.findByText('second-page-file.jpg')).toBeInTheDocument()
  })

  it('shows the ApiError message when the request fails with an ApiError', async () => {
    mockedGetMediaFiles.mockRejectedValueOnce(new ApiError(500, 'media.error.fallback'))

    render(<MediaFilesPage />)

    await waitFor(() => {
      expect(screen.getByTestId('error-message')).toHaveTextContent('media.error.fallback')
    })

    expect(screen.getByTestId('result-count')).toHaveTextContent('0')
    expect(screen.getByTestId('has-results')).toHaveTextContent('false')
    expect(screen.getByTestId('floating-alert')).toHaveTextContent('media.error.notification')
  })

  it('shows the fallback error message for non-ApiError failures', async () => {
    mockedGetMediaFiles.mockRejectedValueOnce(new Error('Unknown failure'))

    render(<MediaFilesPage />)

    await waitFor(() => {
      expect(screen.getByTestId('error-message')).toHaveTextContent('media.error.fallback')
    })

    expect(screen.getByTestId('floating-alert')).toHaveTextContent('media.error.notification')
  })

  it('retries loading after clicking retry', async () => {
    mockedGetMediaFiles.mockRejectedValueOnce(new Error('Unknown failure')).mockResolvedValueOnce({
      count: 1,
      next: null,
      previous: null,
      results: [mediaFile],
    })

    render(<MediaFilesPage />)

    await waitFor(() => {
      expect(screen.getByTestId('error-message')).toHaveTextContent('media.error.fallback')
    })

    fireEvent.click(screen.getByRole('button', { name: 'media.error.retry' }))

    await waitFor(() => {
      expect(mockedGetMediaFiles).toHaveBeenCalledTimes(2)
    })

    expect(await screen.findByText('poster.jpg')).toBeInTheDocument()
    expect(screen.getByTestId('error-message')).toHaveTextContent('')
    expect(screen.queryByTestId('floating-alert')).not.toBeInTheDocument()
  })
})
