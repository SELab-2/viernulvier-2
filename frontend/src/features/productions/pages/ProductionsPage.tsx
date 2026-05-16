/*
 * ProductionsPage
 *
 * Displays a searchable, filterable, and sortable list of productions.
 * Big Floppa: this page orchestrates data fetching, URL-synced state, filters, and layout only.
 */

import { useMediaQuery, useTheme } from '@mui/material'
import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'

import { useNotification } from '../../../contexts/notificationContextShared'
import { getGenres } from '../../../services/genres/Genres'
import { getProductions } from '../../../services/productions/Productions'
import { getTags } from '../../../services/tags/Tags'
import CollectionView from '../../../shared/components/CollectionView'
import CollectionResultsSkeleton from '../../../shared/components/skeletons/CollectionResultsSkeleton'
import useCollectionQuery from '../../../shared/hooks/useCollectionQuery'
import { useSearchBarUrlState } from '../../../shared/hooks/useSearchBarUrlState'
import useSearchDraft from '../../../shared/hooks/useSearchDraft'
import CollectionPageLayout from '../../../shared/layouts/CollectionPageLayout'
import ProductionGridCard from '../components/cards/ProductionGridCard'
import ProductionListCard from '../components/cards/ProductionListCard'
import FilterPanel from '../components/filter-panel/FilterPanel'

import type { Genre } from '../../../types/Genres'
import type { Production } from '../../../types/Productions'
import type { Tag } from '../../../types/Tags'

const PAGE_SIZE = 12
const FILTER_METADATA_PAGE_SIZE = 250

/**
 * Builds ordering string for API based on UI sort state.
 */
const getOrderingValue = (sortTarget: 'name' | 'date', sortDirection: 'asc' | 'desc'): string => {
  const targetField = sortTarget === 'name' ? 'title_sort' : 'first_event_start'
  return sortDirection === 'desc' ? `-${targetField}` : targetField
}

/**
 * Converts YYYY-MM-DD into ISO boundary timestamps.
 */
const toIsoDateBoundary = (value: string, boundary: 'start' | 'end'): string | undefined => {
  if (!value) {
    return undefined
  }

  const suffix = boundary === 'start' ? 'T00:00:00.000Z' : 'T23:59:59.999Z'
  return new Date(`${value}${suffix}`).toISOString()
}

/**
 * Parses comma-separated ID strings into numeric arrays.
 */
const parseCommaSeparatedIds = (value: string): number[] | undefined => {
  if (!value) {
    return undefined
  }
  return value.split(',').map(Number)
}

/**
 * Fetches all genres across paginated API responses.
 */
const fetchGenres = async (): Promise<Genre[]> => {
  const firstPage = await getGenres({
    page: 1,
    pageSize: FILTER_METADATA_PAGE_SIZE,
  })

  const pageSize = Math.max(1, firstPage.results.length || FILTER_METADATA_PAGE_SIZE)
  const totalPages = Math.max(1, Math.ceil(firstPage.count / pageSize))

  if (totalPages === 1) {
    return firstPage.results
  }

  const remainingPages = Array.from({ length: totalPages - 1 }, (_, i) => i + 2)

  const remainingResponses = await Promise.all(
    remainingPages.map((page) =>
      getGenres({
        page,
        pageSize: FILTER_METADATA_PAGE_SIZE,
      }),
    ),
  )

  return [...firstPage.results, ...remainingResponses.flatMap((r) => r.results)]
}

/**
 * Fetches all enabled tags across paginated API responses.
 */
const fetchTags = async (): Promise<Tag[]> => {
  const tagsById = new Map<number, Tag>()
  let page = 1
  let hasMore = true

  while (hasMore) {
    const response = await getTags({
      page,
      pageSize: 250,
      filters: { is_enabled: true },
    })

    response.results.forEach((tag) => tagsById.set(tag.id, tag))

    hasMore = response.next !== null
    page += 1
  }

  return Array.from(tagsById.values())
}

/**
 * Returns true if production has at least one selected genre.
 */
const hasSelectedGenre = (production: Production, selectedGenreIds: number[]): boolean =>
  production.genres.some((genre) => selectedGenreIds.includes(genre.id))

const ProductionsPage = () => {
  const { t } = useTranslation()
  const theme = useTheme()
  const { showFloatingAlert } = useNotification()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))

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

  const ordering = useMemo(
    () => getOrderingValue(sortTarget, sortDirection),
    [sortTarget, sortDirection],
  )

  const selectedGenres = selectedGenreIds.join(',')
  const selectedTags = selectedTagIds.join(',')

  /**
   * Load filter metadata (genres + tags).
   */
  useEffect(() => {
    let isActive = true

    const fetchFilterMetadata = async () => {
      try {
        const [fetchedGenres, fetchedTags] = await Promise.all([fetchGenres(), fetchTags()])

        if (!isActive) {
          return
        }

        setGenres(fetchedGenres)
        setTags(fetchedTags)
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

  const {
    isLoading,
    items: productions,
    count: totalCount,
    error,
    retry,
  } = useCollectionQuery<Production, { results: Production[]; count: number }>({
    deps: [
      ordering,
      page,
      searchValue,
      attendanceMode,
      performerType,
      selectedGenres,
      selectedTags,
      firstEventStartAfter,
      firstEventStartBefore,
    ],
    fetcher: () =>
      getProductions({
        page,
        pageSize: PAGE_SIZE,
        filters: {
          search: searchValue.trim() || undefined,
          ordering,
          attendance_mode: attendanceMode,
          performer_type: performerType,
          genre: parseCommaSeparatedIds(selectedGenres),
          tag: parseCommaSeparatedIds(selectedTags),
          first_event_start_after: toIsoDateBoundary(firstEventStartAfter, 'start'),
          first_event_start_before: toIsoDateBoundary(firstEventStartBefore, 'end'),
        },
      }),
    select: (response) => ({ items: response.results, count: response.count }),
    mapError: () => {
      showFloatingAlert({
        message: t('productions.home.error.notification'),
        severity: 'error',
      })

      return { message: null, showFallback: true }
    },
  })

  const searchDraft = useSearchDraft({
    value: searchValue,
    trackDirty: true,
    onCommit: setSearchValue,
    onSameQuery: () => retry(),
  })

  const renderedErrorMessage = error.showFallback
    ? t('productions.home.error.fallback')
    : error.message

  const onSearchSubmit = (value: string) => {
    searchDraft.submit(value)
  }

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

  const resultsContent = (
    <CollectionView
      items={productions}
      layout={viewMode}
      getKey={(p) => p.id}
      renderListItem={(p) => (
        <ProductionListCard
          production={p}
          selectedGenreIds={selectedGenreIds}
          selectedTagIds={selectedTagIds}
        />
      )}
      renderGridItem={(p) => (
        <ProductionGridCard
          production={p}
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
  )
}

export default ProductionsPage
