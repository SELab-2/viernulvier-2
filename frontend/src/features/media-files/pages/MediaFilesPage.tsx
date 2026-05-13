import { useMediaQuery, useTheme } from '@mui/material'
import { useEffect, useMemo, useRef } from 'react'
import { useTranslation } from 'react-i18next'

import MediaFilesPageSkeleton from './MediaFilesPageSkeleton'
import MediaFileGridCard from '../components/MediaFileGridCard'
import MediaFileListCard from '../components/MediaFileListCard'
import CollectionView from '../../../shared/components/CollectionView'
import { type SearchSortDirection, type SearchSortTarget } from '../../../shared/components/search/types'
import { useSearchBarUrlState } from '../../../shared/hooks/useSearchBarUrlState'
import useCollectionQuery from '../../../shared/hooks/useCollectionQuery'
import useSearchDraft from '../../../shared/hooks/useSearchDraft'
import CollectionPageLayout from '../../../shared/layouts/CollectionPageLayout'
import { useNotification } from '../../../contexts/notificationContextShared'
import { ApiError } from '../../../services/ApiTypes'
import { getMediaFiles } from '../../../services/media_files/MediaFiles'

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
 * Media files list page that uses shared collection hooks.
 *
 * This page keeps the search input trimmed on change to match previous UX.
 */
const MediaFilesPage = () => {
  const { t } = useTranslation()
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const { showFloatingAlert } = useNotification()

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

  const previousOrderingRef = useRef<string | null>(null)

  const ordering = useMemo(
    () => getOrderingValue(sortTarget, sortDirection),
    [sortTarget, sortDirection],
  )

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

  const searchDraft = useSearchDraft({
    value: searchValue,
    trackDirty: true,
    onCommit: (nextValue) => {
      if (page !== 1) {
        setPage(1)
      }
      setSearchValue(nextValue)
    },
    onSameQuery: () => retry(),
  })

  const renderedErrorMessage = error.showFallback ? t('media.error.fallback') : error.message

  useEffect(() => {
    const previousOrdering = previousOrderingRef.current

    if (previousOrdering !== null && previousOrdering !== ordering && page !== 1) {
      setPage(1)
    }

    previousOrderingRef.current = ordering
  }, [ordering, page, setPage])

  const onSearchSubmit = (value: string) => {
    searchDraft.submit(value)
  }

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
        <MediaFilesPageSkeleton layout={viewMode} isMobile={isMobile} cards={PAGE_SIZE} />
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