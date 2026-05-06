import { useMediaQuery, useTheme } from '@mui/material'
import { useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'

import MediaFilesPageSkeleton from './MediaFilesPageSkeleton'
import CollectionPageLayout from '../components/CollectionPageLayout'
import MediaFileView from '../components/media-files/MediaFileView'
import { useSearchBarUrlState } from '../components/searchbar/useSearchBarUrlState'
import { useCollectionPageNotification } from '../hooks/useCollectionPageNotification'
import { ApiError } from '../services/ApiTypes'
import { getMediaFiles } from '../services/media_files/MediaFiles'

import type { SearchSortDirection, SearchSortTarget } from '../components/searchbar/types'
import type { MediaFile } from '../types/MediaFiles'

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

const MediaFilesPage = () => {
  const { t } = useTranslation()
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))

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

  const [isLoading, setIsLoading] = useState(true)
  const [mediaFiles, setMediaFiles] = useState<MediaFile[]>([])
  const [totalCount, setTotalCount] = useState(0)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [showFallbackError, setShowFallbackError] = useState(false)
  const { showFloatingAlert, clearFloatingAlert } = useCollectionPageNotification(
    'media.error.notification',
  )
  const [retryKey, setRetryKey] = useState(0)
  const [searchInputValue, setSearchInputValue] = useState(searchValue)

  const previousOrderingRef = useRef<string | null>(null)

  const renderedErrorMessage = showFallbackError ? t('media.error.fallback') : errorMessage
  const ordering = useMemo(
    () => getOrderingValue(sortTarget, sortDirection),
    [sortTarget, sortDirection],
  )
  useEffect(() => {
    const previousOrdering = previousOrderingRef.current

    if (previousOrdering !== null && previousOrdering !== ordering && page !== 1) {
      setPage(1)
    }

    previousOrderingRef.current = ordering
  }, [ordering, page, setPage])

  useEffect(() => {
    let isActive = true

    const fetchMediaFiles = async () => {
      setIsLoading(true)
      setErrorMessage(null)
      setShowFallbackError(false)
      clearFloatingAlert()

      try {
        const trimmedSearchValue = searchValue.trim()

        const response = await getMediaFiles({
          page,
          pageSize: PAGE_SIZE,
          filters: {
            search: trimmedSearchValue || undefined,
            ordering,
          },
        })

        if (!isActive) {
          return
        }

        setMediaFiles(response.results)
        setTotalCount(response.count)
      } catch (error: unknown) {
        if (!isActive) {
          return
        }

        if (error instanceof ApiError) {
          setErrorMessage(error.message)
          setShowFallbackError(true)
        } else {
          setErrorMessage(null)
          setShowFallbackError(true)
        }

        showFloatingAlert()
        setMediaFiles([])
        setTotalCount(0)
      } finally {
        if (isActive) {
          setIsLoading(false)
        }
      }
    }

    void fetchMediaFiles()

    return () => {
      isActive = false
    }
  }, [clearFloatingAlert, ordering, page, retryKey, searchValue, showFloatingAlert])

  const onRetry = () => {
    clearFloatingAlert()
    setRetryKey((value) => value + 1)
  }

  const onSearchSubmit = (value: string) => {
    const nextQuery = value.trim()

    if (nextQuery === searchValue.trim()) {
      setRetryKey((current) => current + 1)
      return
    }

    if (page !== 1) {
      setPage(1)
    }

    setSearchValue(nextQuery)
  }

  const resultsContent = <MediaFileView mediaFiles={mediaFiles} layout={viewMode} />

  return (
    <CollectionPageLayout
      isMobile={isMobile}
      searchPlaceholder={t('media.searchPlaceholder')}
      searchValue={searchInputValue}
      onSearchChange={setSearchInputValue}
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
      onRetry={onRetry}
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
