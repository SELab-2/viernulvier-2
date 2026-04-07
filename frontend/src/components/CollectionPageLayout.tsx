import { Alert, Box, Button, Container, Paper, Stack, Typography } from '@mui/material'
import { useTheme } from '@mui/material/styles'
import type { ReactNode } from 'react'
import LoadingSpinner from './LoadingSpinner'
import Pagination from './Pagination'
import SearchControlsBar from './searchbar/SearchControlsBar'
import type { SearchSortDirection, SearchSortTarget, SearchViewMode } from './searchbar/types'

export interface CollectionPageLayoutProps {
  isMobile: boolean
  searchPlaceholder: string
  searchValue: string
  onSearchChange: (value: string) => void
  onSearchSubmit: (value: string) => void
  sortTarget: SearchSortTarget
  onSortTargetChange: (value: SearchSortTarget) => void
  sortDirection: SearchSortDirection
  onSortDirectionChange: (value: SearchSortDirection) => void
  viewMode: SearchViewMode
  onViewModeChange: (value: SearchViewMode) => void
  resultCount: number
  sidebarAriaLabel: string
  sidebarTitle: string
  sidebarDescription: string
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

const CollectionPageLayout = ({
  isMobile,
  searchPlaceholder,
  searchValue,
  onSearchChange,
  onSearchSubmit,
  sortTarget,
  onSortTargetChange,
  sortDirection,
  onSortDirectionChange,
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

  return (
    <Box sx={{ py: { xs: 3, md: 4 } }}>
      <Container maxWidth="xl">
        <Stack spacing={3}>
          <SearchControlsBar
            placeholder={searchPlaceholder}
            searchValue={searchValue}
            onSearchChange={onSearchChange}
            onSearchSubmit={onSearchSubmit}
            sortTarget={sortTarget}
            onSortTargetChange={onSortTargetChange}
            sortDirection={sortDirection}
            onSortDirectionChange={onSortDirectionChange}
            viewMode={viewMode}
            onViewModeChange={onViewModeChange}
            resultCount={resultCount}
            showViewModeToggle={!isMobile}
          />

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

            <Box component="section" aria-label={resultsRegionAriaLabel} sx={{ flex: 1 }}>
              {isLoading ? (
                <Box py={8}>
                  <LoadingSpinner label={loadingLabel} />
                </Box>
              ) : null}

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

              {!isLoading && !errorMessage && hasResults ? resultsContent : null}
            </Box>
          </Box>

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
