import { useEffect, useMemo, useState } from 'react'
import { useMediaQuery, useTheme } from '@mui/material'
import { useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import CollectionPageLayout from '../components/CollectionPageLayout'
import EntityView from '../components/entity/EntityView'
import FloatingAlert from '../components/FloatingAlert'
import ProductionGridCard from '../components/productions/ProductionGridCard'
import ProductionListCard from '../components/productions/ProductionListCard'
import CollectionResultsSkeleton from '../components/skeletons/CollectionResultsSkeleton'
import { useSearchBarUrlState } from '../components/searchbar/useSearchBarUrlState'
import { ApiError } from '../services/ApiTypes'
import { getProductions } from '../services/productions/Productions'
import type { Production } from '../types/Productions'

// Page size for pagination.
const PAGE_SIZE = 12

// Function to determine the ordering parameter for the API based on the current sort target and direction.
// Currently broken because the backend has no field for translations__title
// TODO fix
const getOrderingValue = (sortTarget: 'name' | 'date', sortDirection: 'asc' | 'desc'): string => {
  const targetField = sortTarget === 'name' ? 'translations__title' : 'first_event_start'
  return sortDirection === 'desc' ? `-${targetField}` : targetField
}

const HomePage = () => {
  const { t } = useTranslation()
  const theme = useTheme()
  const location = useLocation()
  // Type for optional navigation state used to show a one-time floating alert when arriving
  type NavState = { floatingAlert?: { open?: boolean; message?: string } }
  const nav = location as { state?: NavState }
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

  // Local state for managing the productions data, loading state, error messages, and a retry key to trigger refetching
  const [isLoading, setIsLoading] = useState(true)
  const [productions, setProductions] = useState<Production[]>([])
  const [totalCount, setTotalCount] = useState(0)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [showFallbackError, setShowFallbackError] = useState(false)
  const [isFloatingErrorOpen, setIsFloatingErrorOpen] = useState(false)
  const [floatingAlertMessage, setFloatingAlertMessage] = useState<string | null>(null)
  const [retryKey, setRetryKey] = useState(0)
  const [searchDraft, setSearchDraft] = useState(searchValue)

  const renderedErrorMessage = showFallbackError
    ? t('productions.home.error.fallback')
    : errorMessage
  const floatingErrorMessage = t('productions.home.error.notification')

  const ordering = useMemo(
    () => getOrderingValue(sortTarget, sortDirection),
    [sortDirection, sortTarget],
  )

  useEffect(() => {
    setSearchDraft(searchValue)
  }, [searchValue])

  useEffect(() => {
    let isActive = true

    const fetchPageData = async () => {
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

    void fetchPageData()

    return () => {
      isActive = false
    }
  }, [ordering, page, retryKey, searchValue])

  const onRetry = () => {
    setIsFloatingErrorOpen(false)
    setFloatingAlertMessage(null)
    setRetryKey((value) => value + 1)
  }

  const onFloatingErrorClose = () => {
    setIsFloatingErrorOpen(false)
    setFloatingAlertMessage(null)
  }

  const onSearchSubmit = (value: string) => {
    const nextQuery = value.trim()
    if (nextQuery === searchValue.trim()) {
      setRetryKey((current) => current + 1)
      return
    }

    setSearchValue(nextQuery)
  }

  // If a page navigated here with a floatingAlert in location.state, show it once.
  useEffect(() => {
    const state = nav.state
    if (state?.floatingAlert && state.floatingAlert.open) {
      setErrorMessage(null)
      setShowFallbackError(false)
      setFloatingAlertMessage(state.floatingAlert.message ?? null)
      setIsFloatingErrorOpen(true)
      // Clear the history state so the alert won't reappear on back/refresh
      try {
        window.history.replaceState({}, document.title)
      } catch {
        /* ignore */
      }
    }
  }, [nav])

  // Main results content.
  const resultsContent = (
    <EntityView
      items={productions}
      layout={viewMode}
      getKey={(production) => production.id}
      renderListItem={(production) => <ProductionListCard production={production} />}
      renderGridItem={(production) => <ProductionGridCard production={production} />}
    />
  )

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
        sidebarAriaLabel={t('productions.home.filterPanelLabel')}
        sidebarTitle={t('productions.home.filterPanelTitle')}
        sidebarDescription={t('productions.home.filterPanelPlaceholder')}
        resultsRegionAriaLabel={t('productions.home.resultsRegionLabel')}
        isLoading={isLoading}
        loadingLabel={t('productions.home.loading')}
        loadingContent={
          <CollectionResultsSkeleton layout={viewMode} isMobile={isMobile} cards={PAGE_SIZE} />
        }
        errorMessage={renderedErrorMessage}
        retryLabel={t('productions.home.error.retry')}
        onRetry={onRetry}
        emptyTitle={t('productions.home.empty.title')}
        emptyDescription={t('productions.home.empty.description')}
        hasResults={productions.length > 0}
        resultsContent={resultsContent}
        page={page}
        pageSize={PAGE_SIZE}
        totalItems={totalCount}
        onPageChange={setPage}
      />

      <FloatingAlert
        open={isFloatingErrorOpen}
        onClose={onFloatingErrorClose}
        severity="error"
        message={floatingAlertMessage ?? floatingErrorMessage}
      />
    </>
  )
}

export default HomePage
