import { Alert, Box, Button, Container, Paper, Stack, Typography } from '@mui/material'
import { useTheme } from '@mui/material/styles'
import type { ReactNode } from 'react'
import LoadingSpinner from './LoadingSpinner'
import Pagination from './Pagination'
import SearchControlsBar from './searchbar/SearchControlsBar'
import type { SearchSortDirection, SearchSortTarget, SearchViewMode } from './searchbar/types'

export interface CollectionPageLayoutProps {
  isMobile: boolean
  showSidebar?: boolean
  searchPlaceholder: string
  searchValue: string
  onSearchChange: (value: string) => void
  onSearchSubmit: (value: string) => void
  sortTarget: SearchSortTarget
  onSortTargetChange: (value: SearchSortTarget) => void
  sortDirection: SearchSortDirection
  onSortDirectionChange: (value: SearchSortDirection) => void
  sortTargetOptions?: Array<{ value: SearchSortTarget; labelKey: string }>
  viewMode: SearchViewMode
  onViewModeChange: (value: SearchViewMode) => void
  resultCount: number
  sidebarAriaLabel?: string
  sidebarTitle?: string
  sidebarDescription?: string
  resultsRegionAriaLabel: string
  isLoading: boolean
  loadingLabel: string
  errorMessage: string | null
  retryLabel: string
  onRetry: () => void
  emptyTitle: string
  emptyDescription: string
  hasResults: boolean
  resultsContent: ReactNode
  page: number
  pageSize: number
  totalItems: number
  onPageChange: (page: number) => void
  paginationI18nKeyPrefix?: string
}

/**
 * Reusable layout component for collection pages that includes a search bar, sidebar, results area, and pagination.
 * Handles common UI states such as loading, error, and empty results. The layout is responsive and adapts to mobile screens.
 *
 * Uses {@link SearchControlsBar} for the search and sorting controls, and {@link Pagination} for page navigation.
 *
 * @param props.isMobile Boolean indicating if the layout is being rendered on a mobile device.
 * @param props.searchPlaceholder Placeholder text for the search input.
 * @param props.searchValue Current value of the search input.
 * @param props.onSearchChange Callback function to update the search value.
 * @param props.onSearchSubmit Callback function when the search is submitted.
 * @param props.sortTarget Current sort target (e.g. 'date' or 'name').
 * @param props.onSortTargetChange Callback function to update the sort target.
 * @param props.sortDirection Current sort direction ('asc' or 'desc').
 * @param props.onSortDirectionChange Callback function to update the sort direction.
 * @param props.viewMode Current view mode ('list' or 'grid').
 * @param props.onViewModeChange Callback function to update the view mode.
 * @param props.resultCount Number of results found, used for display in the search controls bar.
 * @param props.sidebarAriaLabel ARIA label for the sidebar region for accessibility.
 * @param props.sidebarTitle Title text displayed in the sidebar area.
 * @param props.sidebarDescription Description text displayed in the sidebar area.
 * @param props.resultsRegionAriaLabel ARIA label for the results region for accessibility.
 * @param props.isLoading Boolean indicating if the data is currently loading, used to show loading state.
 * @param props.loadingLabel Label text to display in the loading spinner.
 * @param props.errorMessage Error message to display if there was an error loading the data. If null, no error is shown.
 * @param props.retryLabel Label for the retry button shown when there is an error.
 * @param props.onRetry Callback function to call when the retry button is clicked.
 * @param props.emptyTitle Title text to display when there are no results.
 * @param props.emptyDescription Description text to display when there are no results.
 * @param props.hasResults Boolean indicating if there are results to display, used to determine whether to show results or empty state.
 * @param props.resultsContent ReactNode containing the content to display in the results area when there are results.
 * @param props.page Current page number for pagination.
 * @param props.pageSize Number of items per page for pagination.
 * @param props.totalItems Total number of items across all pages for pagination.
 * @param props.onPageChange Callback function to call when the page is changed, receives the new page number.
 * @param props.paginationI18nKeyPrefix Optional prefix for internationalization keys used in the Pagination component.
 *
 * @returns A React component that renders the collection page layout with the specified props.
 */

const CollectionPageLayout = ({
  isMobile,
  showSidebar = true,
  searchPlaceholder,
  searchValue,
  onSearchChange,
  onSearchSubmit,
  sortTarget,
  onSortTargetChange,
  sortDirection,
  onSortDirectionChange,
  sortTargetOptions,
  viewMode,
  onViewModeChange,
  resultCount,
  sidebarAriaLabel,
  sidebarTitle,
  sidebarDescription,
  resultsRegionAriaLabel,
  isLoading,
  loadingLabel,
  errorMessage,
  retryLabel,
  onRetry,
  emptyTitle,
  emptyDescription,
  hasResults,
  resultsContent,
  page,
  pageSize,
  totalItems,
  onPageChange,
  paginationI18nKeyPrefix,
}: CollectionPageLayoutProps) => {
  const theme = useTheme()
  const isEmpty = !isLoading && !errorMessage && !hasResults
  const shouldRenderSidebar = showSidebar && sidebarAriaLabel && sidebarTitle && sidebarDescription

  const resultsSection = (
    <Box component="section" aria-label={resultsRegionAriaLabel} sx={{ flex: 1, minWidth: 0 }}>
      {isLoading ? (
        <Box py={8}>
          <LoadingSpinner label={loadingLabel} />
        </Box>
      ) : null}

      {/* Error */}
      {!isLoading && errorMessage ? (
        <Alert
          severity="error"
          action={
            <Button color="inherit" size="small" onClick={onRetry}>
              {retryLabel}
            </Button>
          }
        >
          {errorMessage}
        </Alert>
      ) : null}

      {/* Empty */}
      {isEmpty ? (
        <Paper variant="outlined" sx={{ p: 4, borderRadius: 2 }}>
          <Stack spacing={1}>
            <Typography variant="h6" component="h2">
              {emptyTitle}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {emptyDescription}
            </Typography>
          </Stack>
        </Paper>
      ) : null}

      {/* Results */}
      {!isLoading && !errorMessage && hasResults ? resultsContent : null}
    </Box>
  )

  return (
    <Box sx={{ py: { xs: 3, md: 4 } }}>
      <Container maxWidth="xl">
        <Stack spacing={3}>
          {/* Search, sort, and view controls. */}
          <SearchControlsBar
            placeholder={searchPlaceholder}
            searchValue={searchValue}
            onSearchChange={onSearchChange}
            onSearchSubmit={onSearchSubmit}
            sortTarget={sortTarget}
            onSortTargetChange={onSortTargetChange}
            sortDirection={sortDirection}
            onSortDirectionChange={onSortDirectionChange}
            sortTargetOptions={sortTargetOptions}
            viewMode={viewMode}
            onViewModeChange={onViewModeChange}
            resultCount={resultCount}
            showViewModeToggle={!isMobile}
          />

          {shouldRenderSidebar ? (
            <Box
              display="flex"
              flexDirection={{ xs: 'column', md: 'row' }}
              gap={3}
              alignItems="flex-start"
            >
              <Paper
                component="aside"
                elevation={1}
                aria-label={sidebarAriaLabel}
                sx={{
                  width: { xs: '100%', md: 280 },
                  flexShrink: 0,
                  minHeight: 160,
                  p: 2.5,
                  borderRadius: 2,
                  border: `1px dashed ${theme.palette.divider}`,
                }}
              >
                <Stack spacing={1}>
                  <Typography variant="subtitle1" component="h2">
                    {sidebarTitle}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {sidebarDescription}
                  </Typography>
                </Stack>
              </Paper>

              {resultsSection}
            </Box>
          ) : (
            resultsSection
          )}

          {/* Pagination controls. */}
          <Pagination
            page={page}
            pageSize={pageSize}
            totalItems={totalItems}
            onPageChange={onPageChange}
            disabled={isLoading}
            i18nKeyPrefix={paginationI18nKeyPrefix}
          />
        </Stack>
      </Container>
    </Box>
  )
}

export default CollectionPageLayout
