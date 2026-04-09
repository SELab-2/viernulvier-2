import { useMediaQuery, useTheme } from '@mui/material'
import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import CollectionPageLayout from '../components/CollectionPageLayout'
import FloatingAlert from '../components/FloatingAlert'
import ProductionView from '../components/ProductionView'
import ProductionFilterPanel from '../components/production/ProductionFilterPanel'
import { useSearchBarUrlState } from '../components/searchbar/useSearchBarUrlState'
import { ApiError } from '../services/ApiTypes'
import { getGenres } from '../services/genres/Genres'
import { getProductions } from '../services/productions/Productions'
import { getTags } from '../services/tags/Tags'
import type { Genre } from '../types/Genres'
import type { Production } from '../types/Productions'
import type { Tag } from '../types/Tags'

// Page size for the productions list pagination. This is a constant for now but could be made configurable in the future if needed.
const PAGE_SIZE = 12

// Function to determine the ordering parameter for the API based on the current sort target and direction.
// Currently broken because the backend has no field for translations__title
// TODO fix
const getOrderingValue = (sortTarget: 'name' | 'date', sortDirection: 'asc' | 'desc'): string => {
  const targetField = sortTarget === 'name' ? 'translations__title' : 'first_event_start'
  return sortDirection === 'desc' ? `-${targetField}` : targetField
}

const toIsoDateBoundary = (value: string, boundary: 'start' | 'end'): string | undefined => {
  if (!value) {
    return undefined
  }

  const suffix = boundary === 'start' ? 'T00:00:00.000Z' : 'T23:59:59.999Z'
  return new Date(`${value}${suffix}`).toISOString()
}

// Home page component that displays a list of productions with search, sorting, and pagination functionality.
const HomePage = () => {
  const { t } = useTranslation()
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  // The useSearchBarUrlState hook is used to synchronize the search bar state with the URL query parameters
  const {
    searchValue,
    sortTarget,
    sortDirection,
    viewMode,
    page,
    attendanceModes,
    performerTypes,
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
  const [isFloatingErrorOpen, setIsFloatingErrorOpen] = useState(false)
  const [retryKey, setRetryKey] = useState(0)
  const [searchDraft, setSearchDraft] = useState(searchValue)

  const renderedErrorMessage = showFallbackError
    ? t('productions.home.error.fallback')
    : errorMessage
  const floatingErrorMessage = t('productions.home.error.notification')

  // Memoized value for the API ordering parameter to avoid unnecessary recalculations on every render.
  const ordering = useMemo(
    () => getOrderingValue(sortTarget, sortDirection),
    [sortDirection, sortTarget],
  )
  const selectedAttendanceMode = attendanceModes[0]
  const selectedPerformerType = performerTypes[0]
  const selectedGenreId = selectedGenreIds[0]
  const selectedTagId = selectedTagIds[0]

  // Effect to synchronize the search draft state with the actual search value from the URL
  useEffect(() => {
    setSearchDraft(searchValue)
  }, [searchValue])

  useEffect(() => {
    let isActive = true

    const fetchFilterOptions = async () => {
      try {
        const [genreResponse, tagResponse] = await Promise.all([
          getGenres({ page: 1, pageSize: 100 }),
          getTags({ page: 1, pageSize: 100 }),
        ])

        if (!isActive) {
          return
        }

        setGenres(genreResponse.results)
        setTags(tagResponse.results)
      } catch {
        if (!isActive) {
          return
        }

        setGenres([])
        setTags([])
      }
    }

    void fetchFilterOptions()

    return () => {
      isActive = false
    }
  }, [])

  // Effect to fetch productions data from the API whenever the ordering, page, retryKey, or searchValue changes.
  useEffect(() => {
    let isActive = true

    const fetchProductions = async () => {
      setIsLoading(true)
      setErrorMessage(null)
      setShowFallbackError(false)
      setIsFloatingErrorOpen(false)

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
          setErrorMessage(error.message)
          setShowFallbackError(false)
        } else {
          setErrorMessage(null)
          setShowFallbackError(true)
        }
        setIsFloatingErrorOpen(true)
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

  // Function to handle retrying the API call when there is an error
  const onRetry = () => {
    setIsFloatingErrorOpen(false)
    setRetryKey((value) => value + 1)
  }

  const onFloatingErrorClose = () => {
    setIsFloatingErrorOpen(false)
  }

  // Function to handle search submission, which updates the search value
  const onSearchSubmit = (value: string) => {
    setSearchValue(value.trim())
  }

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
        sidebarContent={
          <ProductionFilterPanel
            attendanceModes={attendanceModes}
            performerTypes={performerTypes}
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
        }
        resultsRegionAriaLabel={t('productions.home.resultsRegionLabel')}
        isLoading={isLoading}
        loadingLabel={t('productions.home.loading')}
        errorMessage={renderedErrorMessage}
        retryLabel={t('productions.home.error.retry')}
        onRetry={onRetry}
        emptyTitle={t('productions.home.empty.title')}
        emptyDescription={t('productions.home.empty.description')}
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
        open={isFloatingErrorOpen}
        onClose={onFloatingErrorClose}
        severity="error"
        message={floatingErrorMessage}
      />
    </>
  )
}

export default HomePage
