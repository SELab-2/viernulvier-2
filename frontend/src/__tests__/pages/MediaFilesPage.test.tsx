import '@testing-library/jest-dom'
import { beforeEach, describe, expect, it, jest } from '@jest/globals'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'

const useMediaQueryMock = jest.fn<(query?: unknown) => boolean>()
const getMediaFilesMock = jest.fn<(params?: unknown) => Promise<any>>()
const setSearchValueMock = jest.fn<(value: string) => void>()
const setSortTargetMock = jest.fn<(value: string) => void>()
const setSortDirectionMock = jest.fn<(value: string) => void>()
const setViewModeMock = jest.fn<(value: string) => void>()
const setPageMock = jest.fn<(value: number) => void>()
const searchBarStateMock = jest.fn<() => any>()

jest.mock('@mui/material', () => {
  const actual = jest.requireActual('@mui/material') as Record<string, unknown>
  return {
    ...actual,
    useTheme: () => ({
      breakpoints: {
        down: jest.fn(() => 'mocked-breakpoint'),
      },
    }),
    useMediaQuery: (...args: unknown[]) => useMediaQueryMock(...args),
  }
})

jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}))

jest.mock('../../components/searchbar/useSearchBarUrlState', () => ({
  useSearchBarUrlState: () => searchBarStateMock(),
}))

jest.mock('../../services/media_files/MediaFiles', () => ({
  getMediaFiles: (params: unknown) => getMediaFilesMock(params),
}))

jest.mock('../../components/media-files/MediaFileView', () => ({
  __esModule: true,
  default: ({ mediaFiles, layout }: { mediaFiles: Array<{ id: number }>; layout: string }) => (
    <div data-testid="media-file-view">
      {layout}:{mediaFiles.map((file) => file.id).join(',')}
    </div>
  ),
}))

jest.mock('../../components/skeletons/CollectionResultsSkeleton', () => ({
  __esModule: true,
  default: () => <div data-testid="results-skeleton">loading</div>,
}))

jest.mock('../../components/FloatingAlert', () => ({
  __esModule: true,
  default: ({ open, message, onClose }: { open: boolean; message: string; onClose: () => void }) =>
    open ? (
      <div>
        <span>{message}</span>
        <button onClick={onClose}>close-floating-alert</button>
      </div>
    ) : null,
}))

jest.mock('../../components/CollectionPageLayout', () => ({
  __esModule: true,
  default: (props: any) => (
    <div>
      <div data-testid="search-value">{props.searchValue}</div>
      <div data-testid="result-count">{props.resultCount}</div>
      <div data-testid="error-message">{props.errorMessage ?? ''}</div>
      <button onClick={() => props.onSearchChange('  report  ')}>change-search</button>
      <button onClick={() => props.onSearchSubmit('  report  ')}>submit-search</button>
      <button onClick={() => props.onRetry()}>retry</button>
      <button onClick={() => props.onSortTargetChange('name')}>change-sort-target</button>
      <button onClick={() => props.onSortDirectionChange('asc')}>change-sort-direction</button>
      <button onClick={() => props.onViewModeChange('grid')}>change-view-mode</button>
      <button onClick={() => props.onPageChange(3)}>change-page</button>
      <div data-testid="loading-state">{String(props.isLoading)}</div>
      {props.resultsContent}
    </div>
  ),
}))

import MediaFilesPage from '../../pages/MediaFilesPage'
import { ApiError } from '../../services/ApiTypes'

describe('MediaFilesPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()

    useMediaQueryMock.mockReturnValue(false)
    searchBarStateMock.mockReturnValue({
      searchValue: '  initial search  ',
      sortTarget: 'date',
      sortDirection: 'desc',
      viewMode: 'list',
      page: 2,
      setSearchValue: setSearchValueMock,
      setSortTarget: setSortTargetMock,
      setSortDirection: setSortDirectionMock,
      setViewMode: setViewModeMock,
      setPage: setPageMock,
    })
  })

  it('fetches media files with trimmed search and ordering, then renders the results', async () => {
    getMediaFilesMock.mockResolvedValueOnce({
      results: [{ id: 11 }, { id: 22 }],
      count: 2,
    })

    render(<MediaFilesPage />)

    await waitFor(() => {
      expect(getMediaFilesMock).toHaveBeenCalledWith({
        page: 2,
        pageSize: 12,
        filters: {
          search: 'initial search',
          ordering: '-created_at',
        },
      })
    })

    await waitFor(() => {
      expect(screen.getByTestId('media-file-view')).toHaveTextContent('list:11,22')
    })

    expect(screen.getByTestId('result-count')).toHaveTextContent('2')
  })

  it('resets the page on ordering change and trims submitted search input', async () => {
    getMediaFilesMock.mockResolvedValue({
      results: [],
      count: 0,
    })

    const { rerender } = render(<MediaFilesPage />)

    await waitFor(() => expect(getMediaFilesMock).toHaveBeenCalledTimes(1))

    searchBarStateMock.mockReturnValue({
      searchValue: '  initial search  ',
      sortTarget: 'name',
      sortDirection: 'desc',
      viewMode: 'list',
      page: 2,
      setSearchValue: setSearchValueMock,
      setSortTarget: setSortTargetMock,
      setSortDirection: setSortDirectionMock,
      setViewMode: setViewModeMock,
      setPage: setPageMock,
    })

    rerender(<MediaFilesPage />)

    await waitFor(() => expect(setPageMock).toHaveBeenCalledWith(1))

    fireEvent.click(screen.getByText('submit-search'))

    expect(setPageMock).toHaveBeenCalledWith(1)
    expect(setSearchValueMock).toHaveBeenCalledWith('report')
  })

  it('retries after an ApiError and shows fallback errors including the floating alert', async () => {
    getMediaFilesMock
      .mockRejectedValueOnce(new ApiError(500, 'Backend failure'))
      .mockResolvedValueOnce({ results: [{ id: 1 }], count: 1 })

    render(<MediaFilesPage />)

    await waitFor(() => {
      expect(screen.getByTestId('error-message')).toHaveTextContent('media.error.fallback')
    })
    expect(screen.getByText('media.error.notification')).toBeInTheDocument()

    fireEvent.click(screen.getByText('retry'))

    await waitFor(() => expect(getMediaFilesMock).toHaveBeenCalledTimes(2))
    expect(screen.getByTestId('media-file-view')).toHaveTextContent('list:1')
  })

  it('re-fetches when the submitted query only changes by whitespace', async () => {
    searchBarStateMock.mockReturnValue({
      searchValue: 'report',
      sortTarget: 'date',
      sortDirection: 'desc',
      viewMode: 'list',
      page: 1,
      setSearchValue: setSearchValueMock,
      setSortTarget: setSortTargetMock,
      setSortDirection: setSortDirectionMock,
      setViewMode: setViewModeMock,
      setPage: setPageMock,
    })

    getMediaFilesMock.mockResolvedValue({
      results: [],
      count: 0,
    })

    render(<MediaFilesPage />)

    await waitFor(() => expect(getMediaFilesMock).toHaveBeenCalledTimes(1))

    fireEvent.click(screen.getByText('submit-search'))

    await waitFor(() => expect(getMediaFilesMock).toHaveBeenCalledTimes(2))
    expect(setSearchValueMock).not.toHaveBeenCalled()
  })
})
