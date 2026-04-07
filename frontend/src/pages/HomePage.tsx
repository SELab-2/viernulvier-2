import { useEffect, useMemo, useState } from 'react'
import { useMediaQuery, useTheme } from '@mui/material'
import { useTranslation } from 'react-i18next'
import CollectionPageLayout from '../components/CollectionPageLayout'
import ProductionView from '../components/ProductionView'
import { useSearchBarUrlState } from '../components/searchbar/useSearchBarUrlState'
import { ApiError } from '../services/ApiTypes'
import { getProductions } from '../services/productions/Productions'
import type { Production } from '../types/Productions'

const PAGE_SIZE = 12

const getOrderingValue = (sortTarget: 'name' | 'date', sortDirection: 'asc' | 'desc'): string => {
  const targetField = sortTarget === 'name' ? 'translations__title' : 'first_event_start'
  return sortDirection === 'desc' ? `-${targetField}` : targetField
}

const HomePage = () => {
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
  const [productions, setProductions] = useState<Production[]>([])
  const [totalCount, setTotalCount] = useState(0)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [retryKey, setRetryKey] = useState(0)
  const [searchDraft, setSearchDraft] = useState(searchValue)

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

        const message =
          error instanceof ApiError ? error.message : t('productions.home.error.fallback')

        setErrorMessage(message)
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
  }, [ordering, page, retryKey, searchValue, t])

  const onRetry = () => {
    setRetryKey((value) => value + 1)
  }

  const onSearchSubmit = (value: string) => {
    setSearchValue(value)
  }

  return (
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
      errorMessage={errorMessage}
      retryLabel={t('productions.home.error.retry')}
      onRetry={onRetry}
      emptyTitle={t('productions.home.empty.title')}
      emptyDescription={t('productions.home.empty.description')}
      hasResults={productions.length > 0}
      resultsContent={<ProductionView productions={productions} layout={viewMode} />}
      page={page}
      pageSize={PAGE_SIZE}
      totalItems={totalCount}
      onPageChange={setPage}
    />
  )
}

export default HomePage
