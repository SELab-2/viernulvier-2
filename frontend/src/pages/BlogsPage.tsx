import { useMediaQuery, useTheme } from '@mui/material'
import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useLocation } from 'react-router-dom'

import BlogView from '../components/BlogView'
import CollectionPageLayout from '../components/CollectionPageLayout'
import FloatingAlert from '../components/FloatingAlert'
import { useSearchBarUrlState } from '../components/searchbar/useSearchBarUrlState'
import CollectionResultsSkeleton from '../components/skeletons/CollectionResultsSkeleton'
import { ApiError } from '../services/ApiTypes'
import { getBlogs } from '../services/blogs/Blogs'

import type { Blog } from '../types/Blogs'

const PAGE_SIZE = 12

const getOrderingValue = (sortTarget: 'name' | 'date', sortDirection: 'asc' | 'desc'): string => {
  const targetField = sortTarget === 'name' ? 'slug' : 'published_at'
  return sortDirection === 'desc' ? `-${targetField}` : targetField
}

const BlogsPage = () => {
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
  const [blogs, setBlogs] = useState<Blog[]>([])
  const [totalCount, setTotalCount] = useState(0)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [showFallbackError, setShowFallbackError] = useState(false)
  const [isFloatingErrorOpen, setIsFloatingErrorOpen] = useState(false)
  const [floatingAlertMessage, setFloatingAlertMessage] = useState<string | null>(null)
  const [retryKey, setRetryKey] = useState(0)
  const [searchDraft, setSearchDraft] = useState(searchValue)

  const renderedErrorMessage = showFallbackError ? t('blogs.home.error.fallback') : errorMessage
  const floatingErrorMessage = t('blogs.home.error.notification')

  const ordering = useMemo(
    () => getOrderingValue(sortTarget, sortDirection),
    [sortDirection, sortTarget],
  )

  useEffect(() => {
    setSearchDraft(searchValue)
  }, [searchValue])

  useEffect(() => {
    let isActive = true

    const fetchBlogs = async () => {
      setIsLoading(true)
      setErrorMessage(null)
      setShowFallbackError(false)
      setIsFloatingErrorOpen(false)
      setFloatingAlertMessage(null)

      try {
        const response = await getBlogs({
          page,
          pageSize: PAGE_SIZE,
          filters: {
            published: true,
            search: searchValue.trim() || undefined,
            ordering,
          },
        })

        if (!isActive) {
          return
        }

        setBlogs(response.results)
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
        setBlogs([])
        setTotalCount(0)
      } finally {
        if (isActive) {
          setIsLoading(false)
        }
      }
    }

    void fetchBlogs()

    return () => {
      isActive = false
    }
  }, [ordering, page, retryKey, searchValue])

  // If a page navigated here with a floatingAlert in location.state, show it once.
  useEffect(() => {
    const { state } = nav
    if (state?.floatingAlert?.open) {
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

  return (
    <>
      <CollectionPageLayout
        isMobile={isMobile}
        showSidebar={false}
        searchPlaceholder={
          isMobile ? t('blogs.home.searchPlaceholderMobile') : t('blogs.home.searchPlaceholder')
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
        resultsRegionAriaLabel={t('blogs.home.resultsRegionLabel')}
        isLoading={isLoading}
        loadingLabel={t('blogs.home.loading')}
        loadingContent={
          <CollectionResultsSkeleton layout={viewMode} isMobile={isMobile} cards={PAGE_SIZE} />
        }
        errorMessage={renderedErrorMessage}
        retryLabel={t('blogs.home.error.retry')}
        onRetry={onRetry}
        emptyTitle={t('blogs.home.empty.title')}
        emptyDescription={t('blogs.home.empty.description')}
        hasResults={blogs.length > 0}
        resultsContent={<BlogView blogs={blogs} layout={viewMode} />}
        page={page}
        pageSize={PAGE_SIZE}
        totalItems={totalCount}
        onPageChange={setPage}
        paginationI18nKeyPrefix="blogs.pagination"
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

export default BlogsPage
