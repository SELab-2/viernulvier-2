import CloseIcon from '@mui/icons-material/Close'
import FilterAltIcon from '@mui/icons-material/FilterAlt'
import {
  Alert,
  Box,
  Button,
  Container,
  Dialog,
  DialogContent,
  IconButton,
  Paper,
  Stack,
  Tooltip,
  Typography,
} from '@mui/material'
import { useTheme, type SxProps, type Theme } from '@mui/material/styles'
import { cloneElement, isValidElement, useState, type ReactNode } from 'react'
import { useTranslation } from 'react-i18next'

import LoadingSpinner from './LoadingSpinner'
import Pagination from './Pagination'
import { tokens } from '../theme/tokens'
import SearchControlsBar from './searchbar/SearchControlsBar'

import type { SearchSortDirection, SearchSortTarget, SearchViewMode } from './searchbar/types'

/* ------------------------------------------------------------------------- */
/* Layout geometry                                                           */
/* ------------------------------------------------------------------------- */

/** Card width (px) shared with `createCommonStyles.gridContainer` tracks. */
const CARD_WIDTH_PX = tokens.card.gridCardWidthPx
/** Gap between cards within the grid (theme.spacing(3) = 24px). */
const CARD_GAP_PX = 24
/** Spacing units for the sidebar width (theme.spacing(39) = 312px). */
const SIDEBAR_WIDTH_SPACING = 39
const SIDEBAR_WIDTH_PX = SIDEBAR_WIDTH_SPACING * 8
/** Gap between the sidebar and the content column (theme.spacing(3) = 24px). */
const SIDEBAR_GAP_PX = 24
/** Total horizontal padding applied by the surrounding `<Container>`. */
const CONTAINER_PADDING_PX = 24 * 2

/** Pixel width occupied by N grid cards laid out in one row. */
const widthForCols = (n: number): number => n * CARD_WIDTH_PX + Math.max(0, n - 1) * CARD_GAP_PX

/**
 * Smallest viewport width at which N grid cards still fit next to the
 * (optional) sidebar inside the page container. Drives the column-count
 * breakpoints below so the step from N to N+1 happens exactly when the next
 * card would actually fit on screen.
 */
const viewportThresholdForCols = (n: number, withSidebar: boolean): number =>
  widthForCols(n) + (withSidebar ? SIDEBAR_WIDTH_PX + SIDEBAR_GAP_PX : 0) + CONTAINER_PADDING_PX

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
  sidebarContent?: ReactNode
  resultsRegionAriaLabel: string
  isLoading: boolean
  loadingLabel: string
  loadingContent?: ReactNode
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
 * @param props.sidebarContent ReactNode containing the content to display in the sidebar area.
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
  sidebarContent,
  resultsRegionAriaLabel,
  isLoading,
  loadingLabel,
  loadingContent,
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
  const { t } = useTranslation()
  const theme = useTheme()
  const isEmpty = !isLoading && !errorMessage && !hasResults
  const shouldRenderSidebar = Boolean(showSidebar && sidebarContent)
  /**
   * The sidebar lives next to the content column on desktop. On mobile the
   * same content becomes a full-screen dialog triggered by a filter button,
   * so at that breakpoint the content column takes over the full width.
   */
  const sidebarInline = shouldRenderSidebar && !isMobile
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false)

  const mobileSidebarLabel = t('searchbar.filters')
  const mobileSidebarButton =
    isMobile && shouldRenderSidebar ? (
      <Tooltip title={mobileSidebarLabel}>
        <IconButton
          aria-label={mobileSidebarLabel}
          aria-haspopup="dialog"
          aria-expanded={isMobileSidebarOpen}
          onClick={() => setIsMobileSidebarOpen(true)}
          sx={{
            height: 40,
            width: 40,
            border: `1px solid ${theme.palette.divider}`,
            borderRadius: 1,
            backgroundColor: theme.palette.background.default,
            color: theme.palette.text.primary,
            '&:hover': {
              borderColor: 'text.primary',
              backgroundColor:
                theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)',
            },
          }}
        >
          <FilterAltIcon fontSize="small" />
        </IconButton>
      </Tooltip>
    ) : null
  const mobileSidebarHeaderAction =
    isMobile && shouldRenderSidebar ? (
      <IconButton
        aria-label="Close"
        onClick={() => setIsMobileSidebarOpen(false)}
        size="small"
        sx={{
          height: 32,
          width: 32,
          border: `1px solid ${theme.palette.text.primary}`,
          borderRadius: 1,
          color: 'text.primary',
          '&:hover': {
            borderColor: 'text.primary',
            backgroundColor: 'action.hover',
          },
        }}
      >
        <CloseIcon fontSize="small" />
      </IconButton>
    ) : null
  const mobileSidebarContent =
    isMobile && isValidElement<{ headerActions?: ReactNode }>(sidebarContent)
      ? cloneElement(sidebarContent, {
          headerActions: mobileSidebarHeaderAction,
        })
      : sidebarContent

  const resultsSection = (
    <Box component="section" aria-label={resultsRegionAriaLabel} sx={{ minWidth: 0 }}>
      {isLoading ? (
        <Box sx={{ py: 8 }}>{loadingContent ?? <LoadingSpinner label={loadingLabel} />}</Box>
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

  /**
   * Width of the content column (search bar + results + pagination).
   *
   * In grid view the column snaps to whole numbers of card tracks so a row
   * never leaves a half-card gap: 100% below the two-column threshold, then
   * two and three card widths as more cards fit next to the (optional)
   * sidebar. At the narrowest step the grid itself centers its lone track
   * via `commonStyles.gridContainer`.
   *
   * In list view rows don't need fixed tracks, so the column just scales
   * gradually and caps at the three-card width - matching the grid's
   * largest footprint without introducing an intermediate step.
   */
  const contentColumnSx: SxProps<Theme> = {
    flex: 1,
    minWidth: 0,
    // When the sidebar is visible we want cards, search bar, and list rows
    // to hug its right edge rather than re-centering inside the column, so
    // propagate the intent to `commonStyles.gridContainer` via a CSS
    // custom property.
    ...(sidebarInline ? { '--grid-align': 'start' } : null),
    ...(viewMode === 'grid'
      ? {
          maxWidth: '100%',
          [`@media (min-width: ${viewportThresholdForCols(2, sidebarInline)}px)`]: {
            maxWidth: `${widthForCols(2)}px`,
          },
          [`@media (min-width: ${viewportThresholdForCols(3, sidebarInline)}px)`]: {
            maxWidth: `${widthForCols(3)}px`,
          },
        }
      : {
          maxWidth: `${widthForCols(3)}px`,
        }),
  }

  return (
    <Box sx={{ py: { xs: 3, md: 4 } }}>
      <Container maxWidth="xl">
        {/*
          Single layout for every page: the (optional) sidebar and the
          content column live in one flex row. When the sidebar is visible
          we left-align the block so the filter panel hugs the container's
          left edge; otherwise the content column (and any free space from
          its stepped cap) center horizontally in the container.
        */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'flex-start',
            justifyContent: sidebarInline ? 'flex-start' : 'center',
            gap: 3,
          }}
        >
          {sidebarInline ? (
            <Box sx={{ flexShrink: 0, width: theme.spacing(SIDEBAR_WIDTH_SPACING) }}>
              {sidebarContent}
            </Box>
          ) : null}

          <Stack spacing={3} sx={contentColumnSx}>
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
              extraControls={mobileSidebarButton}
              viewMode={viewMode}
              onViewModeChange={onViewModeChange}
              resultCount={resultCount}
              showViewModeToggle={!isMobile}
            />

            {resultsSection}

            <Pagination
              page={page}
              pageSize={pageSize}
              totalItems={totalItems}
              onPageChange={onPageChange}
              disabled={isLoading}
              i18nKeyPrefix={paginationI18nKeyPrefix}
            />
          </Stack>
        </Box>

        {shouldRenderSidebar && isMobile ? (
          <Dialog
            open={isMobileSidebarOpen}
            onClose={() => setIsMobileSidebarOpen(false)}
            fullScreen
            slotProps={{
              paper: {
                'aria-label': mobileSidebarLabel,
                sx: {
                  m: 0,
                  maxWidth: '100%',
                  borderRadius: 0,
                  backgroundImage: 'none',
                },
              },
            }}
          >
            <DialogContent sx={{ p: 0 }}>
              <Box
                sx={{
                  '& > .MuiPaper-root': {
                    border: 'none',
                    borderRadius: 0,
                    boxShadow: 'none',
                  },
                }}
              >
                {mobileSidebarContent}
              </Box>
            </DialogContent>
          </Dialog>
        ) : null}
      </Container>
    </Box>
  )
}

export default CollectionPageLayout
