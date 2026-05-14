import { useMediaQuery, useTheme } from '@mui/material'
import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'

import { useNotification } from '../../../contexts/notificationContextShared'
import { getBlogs } from '../../../services/blogs/Blogs'
import CollectionView from '../../../shared/components/CollectionView'
import CollectionResultsSkeleton from '../../../shared/components/skeletons/CollectionResultsSkeleton'
import useCollectionQuery from '../../../shared/hooks/useCollectionQuery'
import { useSearchBarUrlState } from '../../../shared/hooks/useSearchBarUrlState'
import useSearchDraft from '../../../shared/hooks/useSearchDraft'
import CollectionPageLayout from '../../../shared/layouts/CollectionPageLayout'
import BlogGridCard from '../components/BlogGridCard'
import BlogListCard from '../components/BlogListCard'

import type { Blog } from '../../../types/Blogs'

/**
 * Number of items per page for pagination.
 * This is used for both grid and list layouts to keep UI consistent.
 */
const PAGE_SIZE = 12

/**
 * Builds the ordering string used by the API based on UI sort state.
 *
 * - name -> sorts by title (title_sort)
 * - date -> sorts by published_at
 *
 * Direction controls ascending/descending prefix.
 */
const getOrderingValue = (sortTarget: 'name' | 'date', sortDirection: 'asc' | 'desc'): string => {
  const targetField = sortTarget === 'name' ? 'title_sort' : 'published_at'
  return sortDirection === 'desc' ? `-${targetField}` : targetField
}

/**
 * BlogsPage
 *
 * Main container page for browsing blogs with:
 * - server-side pagination
 * - sorting (name/date)
 * - search with draft input handling
 * - grid/list view switching
 *
 * Data fetching is handled via useCollectionQuery which abstracts:
 * - loading state
 * - error state
 * - retry logic
 */
const BlogsPage = () => {
  const { t } = useTranslation()
  const theme = useTheme()
  const { showFloatingAlert } = useNotification()
  const isMobile = useMediaQuery(theme.breakpoints.down('lg'))

  /**
   * URL-synced state for search, sorting, view mode and pagination.
   * Keeps UI state shareable via URL parameters.
   */
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

  /**
   * Memoized ordering string to avoid recalculating on every render.
   */
  const ordering = useMemo(
    () => getOrderingValue(sortTarget, sortDirection),
    [sortDirection, sortTarget],
  )

  /**
   * Main data fetching hook.
   * Handles:
   * - fetching blogs from API
   * - mapping response format
   * - error handling
   * - retry logic
   */
  const {
    isLoading,
    items: blogs,
    count: totalCount,
    error,
    retry,
  } = useCollectionQuery<Blog, { results: Blog[]; count: number }>({
    deps: [ordering, page, searchValue],
    fetcher: () =>
      getBlogs({
        page,
        pageSize: PAGE_SIZE,
        filters: {
          published: true,
          search: searchValue.trim() || undefined,
          ordering,
        },
      }),
    select: (response) => ({ items: response.results, count: response.count }),
    mapError: () => {
      showFloatingAlert({
        message: t('blogs.home.error.notification'),
        severity: 'error',
      })
      return { message: null, showFallback: true }
    },
  })

  /**
   * Search draft handler keeps typing state separate from committed state.
   */
  const searchDraft = useSearchDraft({
    value: searchValue,
    trackDirty: true,
    onCommit: setSearchValue,
    onSameQuery: () => retry(),
  })

  /**
   * Derived error message depending on whether fallback UI should be shown.
   */
  const renderedErrorMessage = error.showFallback ? t('blogs.home.error.fallback') : error.message

  /**
   * Submits search from input field.
   */
  const onSearchSubmit = (value: string) => {
    searchDraft.submit(value)
  }

  return (
    <CollectionPageLayout
      isMobile={isMobile}
      showSidebar={false}
      searchPlaceholder={
        isMobile ? t('blogs.home.searchPlaceholderMobile') : t('blogs.home.searchPlaceholder')
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
      resultsRegionAriaLabel={t('blogs.home.resultsRegionLabel')}
      isLoading={isLoading}
      loadingLabel={t('blogs.home.loading')}
      loadingContent={
        <CollectionResultsSkeleton layout={viewMode} isMobile={isMobile} cards={PAGE_SIZE} />
      }
      errorMessage={renderedErrorMessage}
      retryLabel={t('blogs.home.error.retry')}
      onRetry={retry}
      emptyTitle={t('blogs.home.empty.title')}
      emptyDescription={t('blogs.home.empty.description')}
      hasResults={blogs.length > 0}
      resultsContent={
        <CollectionView
          items={blogs}
          layout={viewMode}
          getKey={(blog) => blog.id}
          renderListItem={(blog) => <BlogListCard blog={blog} />}
          renderGridItem={(blog) => <BlogGridCard blog={blog} />}
        />
      }
      page={page}
      pageSize={PAGE_SIZE}
      totalItems={totalCount}
      onPageChange={setPage}
      paginationI18nKeyPrefix="blogs.pagination"
    />
  )
}

export default BlogsPage
