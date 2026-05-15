import { useMediaQuery, useTheme } from '@mui/material'
import { useEffect, useMemo, useRef } from 'react'
import { useTranslation } from 'react-i18next'

import { useNotification } from '../../../contexts/notificationContextShared'
import { ApiError } from '../../../services/ApiTypes'
import { getMediaFiles } from '../../../services/media_files/MediaFiles'
import CollectionView from '../../../shared/components/CollectionView'
import useCollectionQuery from '../../../shared/hooks/useCollectionQuery'
import { useSearchBarUrlState } from '../../../shared/hooks/useSearchBarUrlState'
import CollectionResultsSkeleton from '../../../shared/components/skeletons/CollectionResultsSkeleton'
import useSearchDraft from '../../../shared/hooks/useSearchDraft'
import CollectionPageLayout from '../../../shared/layouts/CollectionPageLayout'
import MediaFileGridCard from '../components/MediaFileGridCard'
import MediaFileListCard from '../components/MediaFileListCard'

import type { SearchSortDirection, SearchSortTarget } from '../../../shared/components/search/types'
import type { MediaFile } from '../../../types/MediaFiles'

const PAGE_SIZE = 12

const MEDIA_SORT_TARGET_OPTIONS: Array<{ value: SearchSortTarget; labelKey: string }> = [
  { value: 'date', labelKey: 'searchbar.sort.date' },
  { value: 'name', labelKey: 'searchbar.sort.name' },
]

const getOrderingValue = (
  sortTarget: SearchSortTarget,
  sortDirection: SearchSortDirection,
): string => {
  if (sortTarget === 'name') {
    return sortDirection === 'desc' ? '-filename' : 'filename'
  }

  return sortDirection === 'desc' ? '-created_at' : 'created_at'
}

/**
 * Media files list page.
 *
 * Purpose:
 * - Displays paginated media library (images/videos/files)
 * - Supports search, sorting, pagination, and grid/list views
 *
 * Key behaviour:
 * - Search is URL-synced via useSearchBarUrlState
 * - Sorting is translated into backend ordering parameters
 * - Page resets automatically when ordering or search changes
 * - Uses shared CollectionView for consistent rendering logic
 */
const MediaFilesPage = () => {
  const { t } = useTranslation()
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const { showFloatingAlert } = useNotification()

  // URL-synced state (keeps UI state in sync with query params)
  const {
    searchValue,
    sortTarget,
    sortDirection,
    viewMode,
    page,
    setSearchValue,
    setSortTarget,
    setSortDirection,
    setViewMode,
    setPage,
  } = useSearchBarUrlState({ isMobile })

  // Tracks previous ordering to detect changes and reset pagination
  const previousOrderingRef = useRef<string | null>(null)

  // Converts UI sort state into backend ordering string
  const ordering = useMemo(
    () => getOrderingValue(sortTarget, sortDirection),
    [sortTarget, sortDirection],
  )

  /**
   * Main data query for media files.
   *
   * Notes:
   * - searchValue is trimmed before sending to API
   * - API returns both results + total count for pagination
   * - Errors trigger both UI fallback + floating notification
   */
  const {
    isLoading,
    items: mediaFiles,
    count: totalCount,
    error,
    retry,
  } = useCollectionQuery<MediaFile, { results: MediaFile[]; count: number }>({
    deps: [ordering, page, searchValue],
    fetcher: () =>
      getMediaFiles({
        page,
        pageSize: PAGE_SIZE,
        filters: {
          search: searchValue.trim() || undefined,
          ordering,
        },
      }),
    select: (response) => ({ items: response.results, count: response.count }),
    mapError: (error: unknown) => {
      showFloatingAlert({
        message: t('media.error.notification'),
        severity: 'error',
      })

      return {
        message: error instanceof ApiError ? error.message : null,
        showFallback: true,
      }
    },
  })

  // Local draft state for search input (decouples typing from API calls)
  const searchDraft = useSearchDraft({
    value: searchValue,
    trackDirty: true,
    onCommit: (nextValue) => {
      // Reset pagination when committing a new search
      if (page !== 1) {
        setPage(1)
      }
      setSearchValue(nextValue)
    },
    onSameQuery: () => retry(),
  })

  // Chooses which error message to render (fallback vs API message)
  const renderedErrorMessage = error.showFallback ? t('media.error.fallback') : error.message

  /**
   * Reset pagination when ordering changes.
   * Ensures user always sees page 1 for a new sort order.
   */
  useEffect(() => {
    const previousOrdering = previousOrderingRef.current

    if (previousOrdering !== null && previousOrdering !== ordering && page !== 1) {
      setPage(1)
    }

    previousOrderingRef.current = ordering
  }, [ordering, page, setPage])

  // Search submit handler (commits draft to actual query state)
  const onSearchSubmit = (value: string) => {
    searchDraft.submit(value)
  }

  // Renders collection results using shared abstraction
  const resultsContent = (
    <CollectionView
      items={mediaFiles}
      layout={viewMode}
      getKey={(mediaFile) => mediaFile.id}
      renderListItem={(mediaFile) => <MediaFileListCard mediaFile={mediaFile} />}
      renderGridItem={(mediaFile) => <MediaFileGridCard mediaFile={mediaFile} />}
    />
  )

  return (
    <CollectionPageLayout
      isMobile={isMobile}
      searchPlaceholder={t('media.searchPlaceholder')}
      searchValue={searchDraft.displayedValue}
      onSearchChange={(value) => searchDraft.setDraft(value.trim())}
      onSearchSubmit={onSearchSubmit}
      sortTarget={sortTarget}
      onSortTargetChange={setSortTarget}
      sortDirection={sortDirection}
      onSortDirectionChange={setSortDirection}
      sortTargetOptions={MEDIA_SORT_TARGET_OPTIONS}
      viewMode={viewMode}
      onViewModeChange={setViewMode}
      resultCount={totalCount}
      resultsRegionAriaLabel={t('media.resultsRegionLabel')}
      isLoading={isLoading}
      loadingLabel={t('media.loading')}
      loadingContent={
        <CollectionResultsSkeleton layout={viewMode} isMobile={isMobile} cards={PAGE_SIZE} />
      }
      errorMessage={renderedErrorMessage}
      retryLabel={t('media.error.retry')}
      onRetry={retry}
      emptyTitle={t('media.empty.title')}
      emptyDescription={t('media.empty.description')}
      hasResults={mediaFiles.length > 0}
      resultsContent={resultsContent}
      page={page}
      pageSize={PAGE_SIZE}
      totalItems={totalCount}
      onPageChange={setPage}
      paginationI18nKeyPrefix="media.pagination"
    />
  )
}

export default MediaFilesPage
