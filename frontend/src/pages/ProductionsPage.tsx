import { useMediaQuery, useTheme } from '@mui/material'
import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useLocation } from 'react-router-dom'

import CollectionPageLayout from '../components/CollectionPageLayout'
import FloatingAlert from '../components/FloatingAlert'
import ProductionView from '../components/ProductionView'
import { useSearchBarUrlState } from '../components/searchbar/useSearchBarUrlState'
import CollectionResultsSkeleton from '../components/skeletons/CollectionResultsSkeleton'
import { ApiError } from '../services/ApiTypes'
import { getProductions } from '../services/productions/Productions'

import type { Production } from '../types/Productions'

// Page size for pagination.
const PAGE_SIZE = 12

// Function to determine the ordering parameter for the API based on the current sort target and direction.
const getOrderingValue = (sortTarget: 'name' | 'date', sortDirection: 'asc' | 'desc'): string => {
  const targetField = sortTarget === 'name' ? 'title_sort' : 'first_event_start'
  return sortDirection === 'desc' ? `-${targetField}` : targetField
}

// Page component that displays a list of productions with search, sorting, and pagination functionality.
const ProductionsPage = () => {
  const { t } = useTranslation()
  const theme = useTheme()
  const location = useLocation()
  // Type for optional navigation state used to show a one-time floating alert when arriving at the page.
  type NavState = { floatingAlert?: { open?: boolean; message?: string } }
  const nav = location as { state?: NavState }
  const navFloatingAlertOpen = Boolean(nav.state?.floatingAlert?.open)
  const navFloatingAlertMessage = nav.state?.floatingAlert?.message ?? null
  const initialFloatingAlertOpen = Boolean(nav.state?.floatingAlert?.open)
  const initialFloatingAlertMessage = nav.state?.floatingAlert?.message ?? null
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  // The useSearchBarUrlState hook is used to synchronize the search bar state with the URL query parameters
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

  const selectedGenreIds = useMemo(() => [], [])

  // Local state for managing the productions data, loading state, error messages, and a retry key to trigger refetching
  const [isLoading, setIsLoading] = useState(true)
  const [productions, setProductions] = useState<Production[]>([])
  const [totalCount, setTotalCount] = useState(0)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [showFallbackError, setShowFallbackError] = useState(false)
  const [isFloatingErrorOpen, setIsFloatingErrorOpen] = useState(initialFloatingAlertOpen)
  const [floatingAlertMessage, setFloatingAlertMessage] = useState<string | null>(
    initialFloatingAlertMessage,
  )
  const [retryKey, setRetryKey] = useState(0)
  const [searchDraft, setSearchDraft] = useState(searchValue)

  // Error message to display in the UI, preferring the translated fallback message
  const renderedErrorMessage = showFallbackError ? t('archive.home.error.fallback') : errorMessage
  const floatingErrorMessage = t('archive.home.error.notification')

  // Memoized value for the API ordering parameter to avoid unnecessary recalculations on every render.
  const ordering = useMemo(
    () => getOrderingValue(sortTarget, sortDirection),
    [sortDirection, sortTarget],
  )

  // Effect to fetch the productions data from the API whenever the ordering, page, retryKey, or searchValue changes
  useEffect(() => {
    let isActive = true

    const fetchProductions = async () => {
      setIsLoading(true)
      setErrorMessage(null)
      setShowFallbackError(false)
      setIsFloatingErrorOpen(false)
      setFloatingAlertMessage(null)

      try {
        const response = await getProductions({
          page,
          pageSize: PAGE_SIZE,
          filters: {
            search: searchValue.trim() || undefined,
            ordering,
          },
        })

        if (!isActive) {
          return
        }

        setProductions(response.results)
        setTotalCount(response.count)
      } catch (error: unknown) {
        if (!isActive) {
          return
        }

        if (error instanceof ApiError) {
          // Backend error payloads are not guaranteed to be localized,
          // so we always show the translated fallback copy in the UI.
          setErrorMessage(null)
          setShowFallbackError(true)
        } else {
          setErrorMessage(null)
          setShowFallbackError(true)
        }
        setIsFloatingErrorOpen(true)
        setFloatingAlertMessage(null)
        setProductions([])
        setTotalCount(0)
      } finally {
        if (isActive) {
          setIsLoading(false)
        }
      }
    }

    void fetchProductions()

    return () => {
      isActive = false
    }
  }, [ordering, page, retryKey, searchValue])

  // Handler for retrying the data fetch when an error occurs, triggered by the retry button in the UI.
  const onRetry = () => {
    setIsFloatingErrorOpen(false)
    setFloatingAlertMessage(null)
    setRetryKey((value) => value + 1)
  }

  // Handler for closing the floating error alert.
  const onFloatingErrorClose = () => {
    setIsFloatingErrorOpen(false)
    setFloatingAlertMessage(null)
  }

  // Handler for submitting the search form, which updates the searchValue and triggers a new data fetch
  const onSearchSubmit = (value: string) => {
    const nextQuery = value.trim()
    if (nextQuery === searchValue.trim()) {
      setRetryKey((current) => current + 1)
      return
    }

    setSearchValue(nextQuery)
    setSearchDraft(nextQuery)
  }

  // If a page navigated here with a floatingAlert in location.state, clear it once.
  useEffect(() => {
    const { state } = nav
    if (state?.floatingAlert?.open) {
      try {
        window.history.replaceState({}, document.title)
      } catch {
        /* ignore */
      }
    }
  }, [nav])

  // The component renders the CollectionPageLayout with all the necessary props for displaying the productions list, search controls, sorting options, and pagination.
  // It also handles the different UI states such as loading, error, and empty results.
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
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        resultCount={totalCount}
        sidebarAriaLabel={t('archive.home.filterPanelLabel')}
        sidebarTitle={t('archive.home.filterPanelTitle')}
        sidebarDescription={t('archive.home.filterPanelPlaceholder')}
        resultsRegionAriaLabel={t('archive.home.resultsRegionLabel')}
        isLoading={isLoading}
        loadingLabel={t('archive.home.loading')}
        loadingContent={
          <CollectionResultsSkeleton layout={viewMode} isMobile={isMobile} cards={PAGE_SIZE} />
        }
        errorMessage={renderedErrorMessage}
        retryLabel={t('archive.home.error.retry')}
        onRetry={onRetry}
        emptyTitle={t('archive.home.empty.title')}
        emptyDescription={t('archive.home.empty.description')}
        hasResults={productions.length > 0}
        resultsContent={
          <ProductionView
            productions={productions}
            layout={viewMode}
            selectedGenreIds={selectedGenreIds}
          />
        }
        page={page}
        pageSize={PAGE_SIZE}
        totalItems={totalCount}
        onPageChange={setPage}
      />

      <FloatingAlert
        open={isFloatingErrorOpen || navFloatingAlertOpen}
        onClose={onFloatingErrorClose}
        severity="error"
        message={navFloatingAlertMessage ?? floatingAlertMessage ?? floatingErrorMessage}
      />
    </>
  )
}

export default ProductionsPage
