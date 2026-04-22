import { useMediaQuery, useTheme } from '@mui/material'
import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'

import CollectionPageLayout from '../components/CollectionPageLayout'
import EntityView from '../components/entity/EntityView'
import FloatingAlert from '../components/FloatingAlert'
import { useSearchBarUrlState } from '../components/searchbar/useSearchBarUrlState'
import SeriesGridCard from '../components/series/SeriesGridCard'
import SeriesListCard from '../components/series/SeriesListCard'
import CollectionResultsSkeleton from '../components/skeletons/CollectionResultsSkeleton'
import { ApiError } from '../services/ApiTypes'
import { getProductionSeries } from '../services/productions/Productions'
import { getTranslatedRecord } from '../utils/translations'

import type { SearchSortTarget, SearchSortDirection } from '../components/searchbar/types'
import type { Series } from '../types/Series'

// Page size for pagination.
const PAGE_SIZE = 12
const SERIES_FETCH_SIZE = 250
const SERIES_SORT_TARGET_OPTIONS: Array<{ value: SearchSortTarget; labelKey: string }> = [
  { value: 'name', labelKey: 'searchbar.sort.name' },
]

// Function to get the localized series name based on the current language.
const getLocalizedSeriesName = (series: Series, language: string): string => {
  const normalizedLanguage = language.startsWith('en') ? 'en' : 'nl'
  return getTranslatedRecord(series.tag.name, normalizedLanguage, series.tag.display_name)
}

// Function to derive the timestamp used for date sorting.
const getSeriesSortTimestamp = (series: Series): number => {
  return Date.parse(series.lastProductionEnd ?? '') || Date.parse(series.firstProductionStart ?? '')
}

// Function to sort the series list based on the selected sort target and direction.
const sortSeries = ({
  seriesList,
  sortTarget,
  sortDirection,
  language,
}: {
  seriesList: Series[]
  sortTarget: SearchSortTarget
  sortDirection: SearchSortDirection
  language: string
}): Series[] => {
  const sorted = [...seriesList]

  sorted.sort((left, right) => {
    if (sortTarget === 'name') {
      const leftName = getLocalizedSeriesName(left, language)
      const rightName = getLocalizedSeriesName(right, language)
      const comparison = leftName.localeCompare(rightName, language)
      return sortDirection === 'asc' ? comparison : -comparison
    }

    const comparison = getSeriesSortTimestamp(left) - getSeriesSortTimestamp(right)
    return sortDirection === 'asc' ? comparison : -comparison
  })

  return sorted
}

// Fetch all aggregated series rows from the backend endpoint.
const fetchSeriesList = async ({ search }: { search?: string }): Promise<Series[]> => {
  const seriesList: Series[] = []
  let page = 1
  let hasMore = true

  while (hasMore) {
    const response = await getProductionSeries({
      page,
      pageSize: SERIES_FETCH_SIZE,
      filters: {
        search,
      },
    })

    seriesList.push(...response.results)
    hasMore = response.next !== null
    page += 1
  }

  return seriesList
}

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

  const [isLoading, setIsLoading] = useState(true)
  const [seriesList, setSeriesList] = useState<Series[]>([])
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [showFallbackError, setShowFallbackError] = useState(false)
  const [isFloatingErrorOpen, setIsFloatingErrorOpen] = useState(false)
  const [retryKey, setRetryKey] = useState(0)
  const [searchDraft, setSearchDraft] = useState(searchValue)

  const renderedErrorMessage = showFallbackError ? t('series.home.error.fallback') : errorMessage
  const floatingErrorMessage = t('series.home.error.notification')

  // Force the page back to name sorting because the series page only supports that option.
  useEffect(() => {
    if (sortTarget === 'date') {
      setSortTarget('name')
    }
  }, [setSortTarget, sortTarget])

  // Fetch and cache the derived series list whenever the active query changes.
  useEffect(() => {
    let isActive = true

    const fetchPageData = async () => {
      setIsLoading(true)
      setErrorMessage(null)
      setShowFallbackError(false)
      setIsFloatingErrorOpen(false)

      try {
        const response = await fetchSeriesList({
          search: searchValue.trim() || undefined,
        })

        if (!isActive) {
          return
        }

        setSeriesList(response)
      } catch (error: unknown) {
        if (!isActive) {
          return
        }

        if (error instanceof ApiError) {
          setErrorMessage(error.message)
          setShowFallbackError(false)
        } else {
          setErrorMessage(null)
          setShowFallbackError(true)
        }

        setIsFloatingErrorOpen(true)
        setSeriesList([])
      } finally {
        if (isActive) {
          setIsLoading(false)
        }
      }
    }

    void fetchPageData()

    return () => {
      isActive = false
    }
  }, [retryKey, searchValue])

  // Sort the derived series list in memory so the UI stays responsive.
  const sortedSeries = useMemo(
    () =>
      sortSeries({
        seriesList,
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
  const onRetry = () => {
    setIsFloatingErrorOpen(false)
    setRetryKey((value) => value + 1)
  }

  // Close the floating error alert without changing page state.
  const onFloatingErrorClose = () => {
    setIsFloatingErrorOpen(false)
  }

  // Normalize the search input before pushing it into the URL state.
  const onSearchSubmit = (value: string) => {
    const nextValue = value.trim()
    setSearchValue(nextValue)
    setSearchDraft(nextValue)
  }

  // Reuse the shared entity view to switch between list and grid cards.
  const resultsContent = (
    <EntityView
      items={pagedSeries}
      layout={viewMode}
      getKey={(series) => series.tag.id}
      renderListItem={(series) => <SeriesListCard series={series} />}
      renderGridItem={(series) => <SeriesGridCard series={series} />}
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
        searchValue={searchDraft}
        onSearchChange={setSearchDraft}
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
        onRetry={onRetry}
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
        open={isFloatingErrorOpen}
        onClose={onFloatingErrorClose}
        severity="error"
        message={floatingErrorMessage}
      />
    </>
  )
}

export default SeriesPage
