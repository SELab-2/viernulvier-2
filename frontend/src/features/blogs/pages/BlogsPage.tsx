import { useMediaQuery, useTheme } from '@mui/material'
import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'

import BlogGridCard from '../components/BlogGridCard'
import BlogListCard from '../components/BlogListCard'
import CollectionView from '../../../shared/components/CollectionView'
import FloatingAlert from '../../../shared/components/FloatingAlert'
import CollectionResultsSkeleton from '../../../shared/components/skeletons/CollectionResultsSkeleton'
import { useSearchBarUrlState } from '../../../shared/hooks/useSearchBarUrlState'
import useCollectionQuery from '../../../shared/hooks/useCollectionQuery'
import useFloatingAlertOnce from '../../../shared/hooks/useFloatingAlertOnce'
import useSearchDraft from '../../../shared/hooks/useSearchDraft'
import CollectionPageLayout from '../../../shared/layouts/CollectionPageLayout'
import { getBlogs } from '../../../services/blogs/Blogs'

import type { Blog } from '../../../types/Blogs'

const PAGE_SIZE = 12

const getOrderingValue = (sortTarget: 'name' | 'date', sortDirection: 'asc' | 'desc'): string => {
  const targetField = sortTarget === 'name' ? 'title_sort' : 'published_at'
  return sortDirection === 'desc' ? `-${targetField}` : targetField
}

/**
 * Blog list page with shared collection lifecycle hooks.
 *
 * - {@link useCollectionQuery} handles loading/error/retry state.
 * - {@link useSearchDraft} keeps input value decoupled from URL state.
 * - {@link useFloatingAlertOnce} shows navigation alerts one time.
 */
const BlogsPage = () => {
  const { t } = useTranslation()
  const theme = useTheme()
  const navFloatingAlert = useFloatingAlertOnce()
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

  const ordering = useMemo(
    () => getOrderingValue(sortTarget, sortDirection),
    [sortDirection, sortTarget],
  )

  const {
    isLoading,
    items: blogs,
    count: totalCount,
    error,
    floatingAlert,
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
    mapError: () => ({ message: null, showFallback: true }),
  })

  const searchDraft = useSearchDraft({
    value: searchValue,
    trackDirty: true,
    onCommit: setSearchValue,
    onSameQuery: () => retry(),
  })

  const renderedErrorMessage = error.showFallback ? t('blogs.home.error.fallback') : error.message
  const floatingErrorMessage = t('blogs.home.error.notification')

  const onSearchSubmit = (value: string) => {
    searchDraft.submit(value)
  }

  return (
    <>
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

export default BlogsPage
