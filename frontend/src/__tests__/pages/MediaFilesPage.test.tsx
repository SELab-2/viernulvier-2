import React from 'react'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'

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
  useSearchBarUrlState: jest.fn(() => ({
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
  })),
}))

jest.mock('../../components/CollectionPageLayout', () => ({
  __esModule: true,
  default: ({
    resultCount,
    isLoading,
    errorMessage,
    hasResults,
    resultsContent,
    retryLabel,
    onRetry,
  }: any) => (
    <div>
      <div data-testid="result-count">{resultCount}</div>
      <div data-testid="is-loading">{String(isLoading)}</div>
      <div data-testid="error-message">{errorMessage ?? ''}</div>
      <div data-testid="has-results">{String(hasResults)}</div>
      <button type="button" onClick={onRetry}>
        {retryLabel}
      </button>
      <div data-testid="results-content">{resultsContent}</div>
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
          description: undefined,
          ordering: '-created_at',
        },
      })
    })

    expect(await screen.findByText('poster.jpg')).toBeInTheDocument()
    expect(screen.getByTestId('result-count')).toHaveTextContent('1')
    expect(screen.getByTestId('has-results')).toHaveTextContent('true')
    expect(screen.getByTestId('error-message')).toHaveTextContent('')
    expect(screen.queryByTestId('floating-alert')).not.toBeInTheDocument()
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
