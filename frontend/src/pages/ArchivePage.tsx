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

const PAGE_SIZE = 12

const getOrderingValue = (sortTarget: 'name' | 'date', sortDirection: 'asc' | 'desc'): string => {
  const targetField = sortTarget === 'name' ? 'title_sort' : 'first_event_start'
  return sortDirection === 'desc' ? `-${targetField}` : targetField
}

const ArchivePage = () => {
  const { t } = useTranslation()
  const theme = useTheme()
  const location = useLocation()
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

  const [isLoading, setIsLoading] = useState(true)
  const [productions, setProductions] = useState<Production[]>([])
  const [totalCount, setTotalCount] = useState(0)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [showFallbackError, setShowFallbackError] = useState(false)
  const [isFloatingErrorOpen, setIsFloatingErrorOpen] = useState(false)
  const [floatingAlertMessage, setFloatingAlertMessage] = useState<string | null>(null)
  const [retryKey, setRetryKey] = useState(0)
  const [searchDraft, setSearchDraft] = useState(searchValue)

  const renderedErrorMessage = showFallbackError ? t('archive.home.error.fallback') : errorMessage
  const floatingErrorMessage = t('archive.home.error.notification')

  const ordering = useMemo(
    () => getOrderingValue(sortTarget, sortDirection),
    [sortDirection, sortTarget],
  )

  useEffect(() => {
    setSearchDraft(searchValue)
  }, [searchValue])

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

  useEffect(() => {
    const { state } = nav
    if (state?.floatingAlert?.open) {
      setErrorMessage(null)
      setShowFallbackError(false)
      setFloatingAlertMessage(state.floatingAlert.message ?? null)
      setIsFloatingErrorOpen(true)
      try {
        window.history.replaceState({}, document.title)
      } catch {
        /* ignore */
      }
    }
  }, [nav])

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
        resultsContent={<ProductionView productions={productions} layout={viewMode} />}
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

export default ArchivePage
