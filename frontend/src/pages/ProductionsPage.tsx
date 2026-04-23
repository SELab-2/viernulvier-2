import { useMediaQuery, useTheme } from '@mui/material'
import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useLocation } from 'react-router-dom'

import CollectionPageLayout from '../components/CollectionPageLayout'
import EntityView from '../components/entity/EntityView'
import FilterPanel from '../components/filter-panel/FilterPanel'
import FloatingAlert from '../components/FloatingAlert'
import ProductionGridCard from '../components/productions/ProductionGridCard'
import ProductionListCard from '../components/productions/ProductionListCard'
import { useSearchBarUrlState } from '../components/searchbar/useSearchBarUrlState'
import CollectionResultsSkeleton from '../components/skeletons/CollectionResultsSkeleton'
import { ApiError } from '../services/ApiTypes'
import { getAllGenres } from '../services/genres/Genres'
import { getProductions } from '../services/productions/Productions'
import { getAllTags } from '../services/tags/Tags'

import type { Genre } from '../types/Genres'
import type { Production } from '../types/Productions'
import type { Tag } from '../types/Tags'

// Page size for pagination.
const PAGE_SIZE = 12

// Function to determine the ordering parameter for the API based on the current sort target and direction.
const getOrderingValue = (sortTarget: 'name' | 'date', sortDirection: 'asc' | 'desc'): string => {
  const targetField = sortTarget === 'name' ? 'title_sort' : 'first_event_start'
  return sortDirection === 'desc' ? `-${targetField}` : targetField
}

const toIsoDateBoundary = (value: string, boundary: 'start' | 'end'): string | undefined => {
  if (!value) {
    return undefined
  }

  const suffix = boundary === 'start' ? 'T00:00:00.000Z' : 'T23:59:59.999Z'
  return new Date(`${value}${suffix}`).toISOString()
}

// Productions page component that displays a list of productions with search, sorting, and pagination functionality.
const ProductionsPage = () => {
  const { t } = useTranslation()
  const theme = useTheme()
  const location = useLocation()
  // Type for optional navigation state used to show a one-time floating alert when arriving
  type NavState = { floatingAlert?: { open?: boolean; message?: string } }
  const nav = location as { state?: NavState }
  const navFloatingAlertOpen = Boolean(nav.state?.floatingAlert?.open)
  const navFloatingAlertMessage = nav.state?.floatingAlert?.message ?? null
  const initialFloatingAlertOpen = Boolean(nav.state?.floatingAlert?.open)
  const initialFloatingAlertMessage = nav.state?.floatingAlert?.message ?? null
  const isMobile = useMediaQuery(theme.breakpoints.down('lg'))

  // The useSearchBarUrlState hook is used to synchronize the search bar state with the URL query parameters
  const {
    searchValue,
    sortTarget,
    sortDirection,
    viewMode,
    page,
    attendanceMode,
    performerType,
    firstEventStartAfter,
    firstEventStartBefore,
    selectedGenreIds,
    selectedTagIds,
    setSearchValue,
    setSortTarget,
    setSortDirection,
    setViewMode,
    setPage,
    toggleAttendanceMode,
    togglePerformerType,
    setFirstEventStartAfter,
    setFirstEventStartBefore,
    setSelectedGenreIds,
    setSelectedTagIds,
    clearFilters,
  } = useSearchBarUrlState({ isMobile })

  // Local state for managing the productions data, loading state, error messages, and a retry key to trigger refetching
  const [isLoading, setIsLoading] = useState(true)
  const [productions, setProductions] = useState<Production[]>([])
  const [genres, setGenres] = useState<Genre[]>([])
  const [tags, setTags] = useState<Tag[]>([])
  const [totalCount, setTotalCount] = useState(0)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [showFallbackError, setShowFallbackError] = useState(false)
  const [isFloatingErrorOpen, setIsFloatingErrorOpen] = useState(initialFloatingAlertOpen)
  const [floatingAlertMessage, setFloatingAlertMessage] = useState<string | null>(
    initialFloatingAlertMessage,
  )
  const [retryKey, setRetryKey] = useState(0)
  const [searchDraft, setSearchDraft] = useState(searchValue)
  const [isSearchDraftDirty, setIsSearchDraftDirty] = useState(false)

  // Error message to display in the UI, preferring the translated fallback message
  const renderedErrorMessage = showFallbackError
    ? t('productions.home.error.fallback')
    : errorMessage
  const floatingErrorMessage = t('productions.home.error.notification')

  // Memoized value for the API ordering parameter to avoid unnecessary recalculations on every render.
  const ordering = useMemo(
    () => getOrderingValue(sortTarget, sortDirection),
    [sortDirection, sortTarget],
  )
  const selectedAttendanceMode = attendanceMode
  const selectedPerformerType = performerType
  const selectedGenreId = selectedGenreIds[0]
  const selectedTagId = selectedTagIds[0]
  const displayedSearchValue = isSearchDraftDirty ? searchDraft : searchValue

  useEffect(() => {
    let isActive = true

    const fetchFilterMetadata = async () => {
      try {
        const [allGenres, allTags] = await Promise.all([getAllGenres(), getAllTags()])

        if (!isActive) {
          return
        }

        setGenres(allGenres)
        setTags(allTags)
      } catch {
        if (!isActive) {
          return
        }

        setGenres([])
        setTags([])
      }
    }

    void fetchFilterMetadata()

    return () => {
      isActive = false
    }
  }, [])

  // Effect to fetch the productions data from the API whenever the ordering, page, retryKey, or searchValue changes
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
            attendance_mode: selectedAttendanceMode,
            performer_type: selectedPerformerType,
            // TODO: Forward all selected genre ids once the backend supports multi-value filtering.
            genre: selectedGenreId,
            // TODO: Forward all selected tag ids once the backend supports multi-value filtering.
            tag: selectedTagId,
            first_event_start_after: toIsoDateBoundary(firstEventStartAfter, 'start'),
            first_event_start_before: toIsoDateBoundary(firstEventStartBefore, 'end'),
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
  }, [
    firstEventStartAfter,
    firstEventStartBefore,
    ordering,
    page,
    retryKey,
    searchValue,
    selectedAttendanceMode,
    selectedGenreId,
    selectedPerformerType,
    selectedTagId,
  ])

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
      setSearchDraft(nextQuery)
      setIsSearchDraftDirty(false)
      setRetryKey((current) => current + 1)
      return
    }

    setSearchValue(nextQuery)
    setSearchDraft(nextQuery)
    setIsSearchDraftDirty(false)
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

  // Main results content.
  const resultsContent = (
    <EntityView
      items={productions}
      layout={viewMode}
      getKey={(production) => production.id}
      renderListItem={(production) => (
        <ProductionListCard production={production} selectedGenreIds={selectedGenreIds} />
      )}
      renderGridItem={(production) => (
        <ProductionGridCard production={production} selectedGenreIds={selectedGenreIds} />
      )}
    />
  )

  const filterPanel = (
    <FilterPanel
      attendanceMode={attendanceMode}
      performerType={performerType}
      firstEventStartAfter={firstEventStartAfter}
      firstEventStartBefore={firstEventStartBefore}
      selectedGenreIds={selectedGenreIds}
      selectedTagIds={selectedTagIds}
      genres={genres}
      tags={tags}
      onAttendanceModeToggle={toggleAttendanceMode}
      onPerformerTypeToggle={togglePerformerType}
      onFirstEventStartAfterChange={setFirstEventStartAfter}
      onFirstEventStartBeforeChange={setFirstEventStartBefore}
      onGenreSelectionChange={setSelectedGenreIds}
      onTagSelectionChange={setSelectedTagIds}
      onClearFilters={clearFilters}
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
        searchValue={displayedSearchValue}
        onSearchChange={(value) => {
          setSearchDraft(value)
          setIsSearchDraftDirty(true)
        }}
        onSearchSubmit={onSearchSubmit}
        sortTarget={sortTarget}
        onSortTargetChange={setSortTarget}
        sortDirection={sortDirection}
        onSortDirectionChange={setSortDirection}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        resultCount={totalCount}
        sidebarContent={filterPanel}
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
        open={isFloatingErrorOpen || navFloatingAlertOpen}
        onClose={onFloatingErrorClose}
        severity="error"
        message={navFloatingAlertMessage ?? floatingAlertMessage ?? floatingErrorMessage}
      />
    </>
  )
}

export default ProductionsPage
