import { useMediaQuery, useTheme } from '@mui/material'
import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'

import CollectionView from '../../../shared/components/CollectionView'
import FloatingAlert from '../../../shared/components/FloatingAlert'
import CollectionResultsSkeleton from '../../../shared/components/skeletons/CollectionResultsSkeleton'
import { useSearchBarUrlState } from '../../../shared/hooks/useSearchBarUrlState'
import useCollectionQuery from '../../../shared/hooks/useCollectionQuery'
import useFloatingAlertOnce from '../../../shared/hooks/useFloatingAlertOnce'
import useSearchDraft from '../../../shared/hooks/useSearchDraft'
import CollectionPageLayout from '../../../shared/layouts/CollectionPageLayout'
import ProductionGridCard from '../components/cards/ProductionGridCard'
import ProductionListCard from '../components/cards/ProductionListCard'
import FilterPanel from '../../../components/filter-panel/FilterPanel'
import { getGenres } from '../../../services/genres/Genres'
import { getProductions } from '../../../services/productions/Productions'
import { getTags } from '../../../services/tags/Tags'

import type { Genre } from '../../../types/Genres'
import type { Production } from '../../../types/Productions'
import type { Tag } from '../../../types/Tags'

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

const parseCommaSeparatedIds = (value: string): number[] | undefined => {
  if (!value) {
    return undefined
  }

  return value.split(',').map(Number)
}

const fetchGenres = async (): Promise<Genre[]> => {
  const genres: Genre[] = []
  let page = 1
  let hasMore = true

  while (hasMore) {
    const response = await getGenres({
      page,
    })

    genres.push(...response.results)
    hasMore = response.next !== null
    page += 1
  }

  return genres
}

const fetchTags = async (): Promise<Tag[]> => {
  const tagsById = new Map<number, Tag>()
  let page = 1
  let hasMore = true

  while (hasMore) {
    const response = await getTags({
      page,
      pageSize: 250,
      filters: {
        is_enabled: true,
      },
    })

    response.results.forEach((tag) => {
      tagsById.set(tag.id, tag)
    })

    hasMore = response.next !== null
    page += 1
  }

  return Array.from(tagsById.values())
}

/**
 * Returns true if the production has at least one genre matching the selected genre IDs.
 */
const hasSelectedGenre = (production: Production, selectedGenreIds: number[]): boolean =>
  production.genres.some((genre) => selectedGenreIds.includes(genre.id))

/**
 * Productions list page with shared collection lifecycle hooks.
 *
 * - {@link useCollectionQuery} handles loading/error/retry state.
 * - {@link useSearchDraft} keeps input value decoupled from URL state.
 * - {@link useFloatingAlertOnce} shows navigation alerts one time.
 */
const ProductionsPage = () => {
  const { t } = useTranslation()
  const theme = useTheme()
  const navFloatingAlert = useFloatingAlertOnce()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))

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

  const [genres, setGenres] = useState<Genre[]>([])
  const [tags, setTags] = useState<Tag[]>([])

  // Memoized value for the API ordering parameter to avoid unnecessary recalculations on every render.
  const ordering = useMemo(
    () => getOrderingValue(sortTarget, sortDirection),
    [sortDirection, sortTarget],
  )
  const selectedAttendanceMode = attendanceMode
  const selectedPerformerType = performerType
  const selectedGenres = selectedGenreIds.join(',')
  const selectedTags = selectedTagIds.join(',')

  const {
    isLoading,
    items: productions,
    count: totalCount,
    error,
    floatingAlert,
    retry,
  } = useCollectionQuery<Production, { results: Production[]; count: number }>({
    deps: [
      firstEventStartAfter,
      firstEventStartBefore,
      ordering,
      page,
      searchValue,
      selectedAttendanceMode,
      selectedGenres,
      selectedPerformerType,
      selectedTags,
    ],
    fetcher: () =>
      getProductions({
        page,
        pageSize: PAGE_SIZE,
        filters: {
          search: searchValue.trim() || undefined,
          ordering,
          attendance_mode: selectedAttendanceMode,
          performer_type: selectedPerformerType,
          genre: parseCommaSeparatedIds(selectedGenres),
          tag: parseCommaSeparatedIds(selectedTags),
          first_event_start_after: toIsoDateBoundary(firstEventStartAfter, 'start'),
          first_event_start_before: toIsoDateBoundary(firstEventStartBefore, 'end'),
        },
      }),
    select: (response) => ({ items: response.results, count: response.count }),
    mapError: () => ({ message: null, showFallback: true }),
  })

  const searchDraft = useSearchDraft({
    value: searchValue,
    trackDirty: true,
    onCommit: setSearchValue,
    onSameQuery: () => retry(),
  })

  // Error message to display in the UI, preferring the translated fallback message
  const renderedErrorMessage = error.showFallback
    ? t('productions.home.error.fallback')
    : error.message
  const floatingErrorMessage = t('productions.home.error.notification')

  useEffect(() => {
    let isActive = true

    const fetchFilterMetadata = async () => {
      try {
        const [genres, tags] = await Promise.all([fetchGenres(), fetchTags()])

        if (!isActive) {
          return
        }

        setGenres(genres)
        setTags(tags)
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

  const onSearchSubmit = (value: string) => {
    searchDraft.submit(value)
  }

  /**
   * Sorts productions with a selected genre to the front of the list,
   * preserving the relative order within each group.
   */
  const sortProductionsBySelectedGenres = useMemo(
    () =>
      selectedGenreIds.length === 0
        ? undefined
        : (items: Production[]) =>
            [...items].sort((a, b) => {
              const aMatch = hasSelectedGenre(a, selectedGenreIds) ? 0 : 1
              const bMatch = hasSelectedGenre(b, selectedGenreIds) ? 0 : 1
              return aMatch - bMatch
            }),
    [selectedGenreIds],
  )

  // Main results content.
  const resultsContent = (
    <CollectionView
      items={productions}
      layout={viewMode}
      getKey={(production) => production.id}
      renderListItem={(production) => (
        <ProductionListCard
          production={production}
          selectedGenreIds={selectedGenreIds}
          selectedTagIds={selectedTagIds}
        />
      )}
      renderGridItem={(production) => (
        <ProductionGridCard
          production={production}
          selectedGenreIds={selectedGenreIds}
          selectedTagIds={selectedTagIds}
        />
      )}
      transformItems={sortProductionsBySelectedGenres}
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
        onRetry={retry}
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
        open={floatingAlert.isOpen || navFloatingAlert.isOpen}
        onClose={() => {
          floatingAlert.close()
          navFloatingAlert.close()
        }}
        severity="error"
        message={navFloatingAlert.message ?? floatingAlert.message ?? floatingErrorMessage}
      />
    </>
  )
}

export default ProductionsPage