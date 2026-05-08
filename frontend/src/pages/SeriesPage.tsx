import { useMediaQuery, useTheme } from '@mui/material'
import { useEffect, useMemo } from 'react'
import { useTranslation } from 'react-i18next'

import CollectionPageLayout from '../components/CollectionPageLayout'
import CollectionView from '../components/CollectionView'
import FloatingAlert from '../components/FloatingAlert'
import { useSearchBarUrlState } from '../components/searchbar/useSearchBarUrlState'
import SeriesGridCard from '../components/series/SeriesGridCard'
import SeriesListCard from '../components/series/SeriesListCard'
import CollectionResultsSkeleton from '../components/skeletons/CollectionResultsSkeleton'
import useCollectionQuery from '../hooks/useCollectionQuery'
import useSearchDraft from '../hooks/useSearchDraft'
import { ApiError } from '../services/ApiTypes'
import { getTags } from '../services/tags/Tags'
import { getTranslatedRecord } from '../utils/translations'

import type { SearchSortTarget, SearchSortDirection } from '../components/searchbar/types'
import type { Tag } from '../types/Tags'

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

  const {
    isLoading,
    items: seriesList,
    error,
    floatingAlert,
    retry,
  } = useCollectionQuery<Tag, Tag[]>({
    deps: [searchValue],
    fetcher: () =>
      fetchTagList({
        search: searchValue.trim() || undefined,
      }),
    select: (items) => ({ items, count: items.length }),
    mapError: (error: unknown) => ({
      message: error instanceof ApiError ? error.message : null,
      showFallback: !(error instanceof ApiError),
    }),
  })

  const searchDraft = useSearchDraft({
    value: searchValue,
    onCommit: setSearchValue,
  })

  const renderedErrorMessage = error.showFallback ? t('series.home.error.fallback') : error.message
  const floatingErrorMessage = t('series.home.error.notification')

  // Force the page back to name sorting because the series page only supports that option.
  useEffect(() => {
    if (sortTarget === 'date') {
      setSortTarget('name')
    }
  }, [setSortTarget, sortTarget])

  // Fetch and cache the derived series list whenever the active query changes.
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

  // Retry the last failed fetch by invalidating the request key.
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
    <>
      <CollectionPageLayout
        isMobile={isMobile}
        searchPlaceholder={
          isMobile ? t('searchbar.searchPlaceholderMobile') : t('searchbar.searchPlaceholder')
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

      <FloatingAlert
        open={floatingAlert.isOpen}
        onClose={floatingAlert.close}
        severity="error"
        message={floatingErrorMessage}
      />
    </>
  )
}

export default SeriesPage
