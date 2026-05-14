import { useMediaQuery, useTheme } from '@mui/material'
import { useEffect, useMemo } from 'react'
import { useTranslation } from 'react-i18next'

import { useNotification } from '../../../contexts/notificationContextShared'
import { ApiError } from '../../../services/ApiTypes'
import { getTags } from '../../../services/tags/Tags'
import CollectionView from '../../../shared/components/CollectionView'
import CollectionResultsSkeleton from '../../../shared/components/skeletons/CollectionResultsSkeleton'
import useCollectionQuery from '../../../shared/hooks/useCollectionQuery'
import { useSearchBarUrlState } from '../../../shared/hooks/useSearchBarUrlState'
import useSearchDraft from '../../../shared/hooks/useSearchDraft'
import CollectionPageLayout from '../../../shared/layouts/CollectionPageLayout'
import { getTranslatedRecord } from '../../../utils/translations'
import SeriesGridCard from '../components/SeriesGridCard'
import SeriesListCard from '../components/SeriesListCard'

import type { SearchSortDirection, SearchSortTarget } from '../../../shared/components/search/types'
import type { Tag } from '../../../types/Tags'

// Page size for pagination.
const PAGE_SIZE = 12
const SERIES_FETCH_SIZE = 250
const SERIES_SORT_TARGET_OPTIONS: Array<{ value: SearchSortTarget; labelKey: string }> = [
  { value: 'name', labelKey: 'searchbar.sort.name' },
]

// Function to get the localized tag name based on the current language.
const getLocalizedTagName = (tag: Tag, language: string): string => {
  const normalizedLanguage = language.startsWith('en') ? 'en' : 'nl'
  return getTranslatedRecord(tag.name, normalizedLanguage, tag.display_name)
}

// Function to derive the timestamp used for date sorting.
const getTagSortTimestamp = (tag: Tag): number => {
  return Date.parse(tag.last_production_end ?? '') || Date.parse(tag.first_production_start ?? '')
}

// Function to sort the tag list based on the selected sort target and direction.
const sortTags = ({
  tagList,
  sortTarget,
  sortDirection,
  language,
}: {
  tagList: Tag[]
  sortTarget: SearchSortTarget
  sortDirection: SearchSortDirection
  language: string
}): Tag[] => {
  const sorted = [...tagList]

  sorted.sort((left, right) => {
    if (sortTarget === 'name') {
      const leftName = getLocalizedTagName(left, language)
      const rightName = getLocalizedTagName(right, language)
      const comparison = leftName.localeCompare(rightName, language)
      return sortDirection === 'asc' ? comparison : -comparison
    }

    const comparison = getTagSortTimestamp(left) - getTagSortTimestamp(right)
    return sortDirection === 'asc' ? comparison : -comparison
  })

  return sorted
}

// Fetch all enabled tags from the backend endpoint.
const fetchTagList = async ({ search }: { search?: string }): Promise<Tag[]> => {
  const tagList: Tag[] = []
  let page = 1
  let hasMore = true

  while (hasMore) {
    const response = await getTags({
      page,
      pageSize: SERIES_FETCH_SIZE,
      filters: {
        is_enabled: true,
        search,
      },
    })

    tagList.push(...response.results)
    hasMore = response.next !== null
    page += 1
  }

  return tagList
}

/**
 * Series list page with shared collection lifecycle hooks.
 *
 * The page derives series ordering in memory while the fetch hook
 * remains responsible for the request lifecycle.
 */
const SeriesPage = () => {
  const { t, i18n } = useTranslation()
  const theme = useTheme()
  const { showFloatingAlert } = useNotification()
  const isMobile = useMediaQuery(theme.breakpoints.down('lg'))

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

  // Force the page back to name sorting because the series page only supports that option.
  useEffect(() => {
    if (sortTarget === 'date') {
      setSortTarget('name')
    }
  }, [setSortTarget, sortTarget])

  const {
    isLoading,
    items: seriesList,
    error,
    retry,
  } = useCollectionQuery<Tag, Tag[]>({
    // sortTarget is intentionally excluded from deps — sorting is done in-memory,
    // so only a new search query should trigger a new fetch.
    deps: [searchValue],
    fetcher: () =>
      fetchTagList({
        search: searchValue.trim() || undefined,
      }),
    select: (response) => ({ items: response, count: response.length }),
    mapError: (error) => {
      // Backend error payloads are not guaranteed to be localized,
      // so we always show the translated fallback copy in the UI.
      if (error instanceof ApiError) {
        return { message: error.message, showFallback: false }
      }
      return { message: null, showFallback: true }
    },
  })

  // Show the floating alert once whenever a new error comes in.
  // Done via useEffect so the alert fires exactly once per fetch failure,
  // not on every re-render.
  const hasError = error.message !== null || error.showFallback
  useEffect(() => {
    if (hasError) {
      showFloatingAlert({
        message: t('series.home.error.notification'),
        severity: 'error',
      })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasError])

  const searchDraft = useSearchDraft({
    value: searchValue,
    trackDirty: true,
    onCommit: setSearchValue,
    onSameQuery: () => retry(),
  })

  const renderedErrorMessage = error.showFallback ? t('series.home.error.fallback') : error.message

  // Sort the derived series list in memory so the UI stays responsive.
  const sortedSeries = useMemo(
    () =>
      sortTags({
        tagList: seriesList,
        sortTarget,
        sortDirection,
        language: i18n.language,
      }),
    [i18n.language, seriesList, sortDirection, sortTarget],
  )

  // Keep the current page inside the available range after filtering or refreshes.
  useEffect(() => {
    if (!isLoading && sortedSeries.length > 0) {
      const lastPage = Math.ceil(sortedSeries.length / PAGE_SIZE)
      if (page > lastPage) {
        setPage(lastPage)
      }
    }
  }, [isLoading, page, setPage, sortedSeries.length])

  // Slice the current page of series before rendering.
  const pagedSeries = useMemo(() => {
    const start = (page - 1) * PAGE_SIZE
    return sortedSeries.slice(start, start + PAGE_SIZE)
  }, [page, sortedSeries])

  // Normalize the search input before pushing it into the URL state.
  const onSearchSubmit = (value: string) => {
    searchDraft.submit(value)
  }

  // Reuse the shared entity view to switch between list and grid cards.
  const resultsContent = (
    <CollectionView
      items={pagedSeries}
      layout={viewMode}
      getKey={(tag) => tag.id}
      renderListItem={(tag) => <SeriesListCard tag={tag} />}
      renderGridItem={(tag) => <SeriesGridCard tag={tag} />}
    />
  )

  // TODO: Fetch series list from API and display them here
  return (
    <CollectionPageLayout
      isMobile={isMobile}
      searchPlaceholder={
        isMobile ? t('series.home.searchPlaceholderMobile') : t('series.home.searchPlaceholder')
      }
      searchValue={searchDraft.displayedValue}
      onSearchChange={searchDraft.setDraft}
      onSearchSubmit={onSearchSubmit}
      sortTarget={sortTarget}
      onSortTargetChange={setSortTarget}
      sortDirection={sortDirection}
      onSortDirectionChange={setSortDirection}
      sortTargetOptions={SERIES_SORT_TARGET_OPTIONS}
      viewMode={viewMode}
      onViewModeChange={setViewMode}
      resultCount={sortedSeries.length}
      resultsRegionAriaLabel={t('series.home.resultsRegionLabel')}
      isLoading={isLoading}
      loadingLabel={t('series.home.loading')}
      loadingContent={
        <CollectionResultsSkeleton layout={viewMode} isMobile={isMobile} cards={PAGE_SIZE} />
      }
      errorMessage={renderedErrorMessage}
      retryLabel={t('series.home.error.retry')}
      onRetry={retry}
      emptyTitle={t('series.home.empty.title')}
      emptyDescription={t('series.home.empty.description')}
      hasResults={pagedSeries.length > 0}
      resultsContent={resultsContent}
      page={page}
      pageSize={PAGE_SIZE}
      totalItems={sortedSeries.length}
      onPageChange={setPage}
      paginationI18nKeyPrefix="series.pagination"
    />
  )
}

export default SeriesPage
