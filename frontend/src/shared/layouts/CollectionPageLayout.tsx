/**
 * Reusable collection page layout component.
 *
 * This component provides a standardized structure for pages that display
 * searchable, sortable, and paginated collections of items (e.g. blogs,
 * productions, media lists, etc.).
 *
 * It centralizes common UI concerns such as:
 * - Search + filtering controls (via SearchControlsBar)
 * - Sidebar rendering (desktop inline + mobile dialog variant)
 * - Loading, error, and empty states
 * - Results rendering
 * - Pagination handling
 *
 * The layout is responsive and adapts between desktop and mobile:
 * - Desktop: sidebar is shown inline next to results
 * - Mobile: sidebar is moved into a full-screen dialog
 *
 * This ensures consistent UX across all collection-type pages.
 */

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

import { tokens } from '../../theme/tokens'
import { DarkMode } from '../../types/Theme'
import LoadingSpinner from '../components/LoadingSpinner'
import Pagination from '../components/Pagination'
import SearchControlsBar from '../components/search/SearchControlsBar'

import type {
  SearchSortDirection,
  SearchSortTarget,
  SearchViewMode,
} from '../components/search/types'

/**
 * Fixed card width used across grid layouts.
 * Must stay in sync with grid system defined in common styles.
 */
const CARD_WIDTH_PX = tokens.card.gridCardWidthPx

/**
 * Horizontal spacing between cards in grid layout.
 */
const CARD_GAP_PX = 24

/**
 * Sidebar width expressed in MUI spacing units.
 */
const SIDEBAR_WIDTH_SPACING = 39

/**
 * Sidebar width converted to pixels (8px per spacing unit).
 */
const SIDEBAR_WIDTH_PX = SIDEBAR_WIDTH_SPACING * 8

/**
 * Gap between sidebar and main content column.
 */
const SIDEBAR_GAP_PX = 24

/**
 * Horizontal padding applied by the outer Container component.
 */
const CONTAINER_PADDING_PX = 24 * 2

/**
 * Calculates total pixel width of N cards in a row.
 */
const widthForCols = (n: number): number => n * CARD_WIDTH_PX + Math.max(0, n - 1) * CARD_GAP_PX

/**
 * Calculates viewport width threshold required to fit N columns
 * plus optional sidebar.
 *
 * Used to dynamically switch max-width constraints for the content column
 * so the layout only expands when space is actually available.
 */
const viewportThresholdForCols = (n: number, withSidebar: boolean): number =>
  widthForCols(n) + (withSidebar ? SIDEBAR_WIDTH_PX + SIDEBAR_GAP_PX : 0) + CONTAINER_PADDING_PX

/**
 * Props for CollectionPageLayout.
 *
 * This defines all UI state required to render:
 * - search controls
 * - sorting
 * - view mode switching
 * - sidebar content
 * - results and pagination
 * - loading/error/empty states
 */
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
 * Main layout component for collection-based pages.
 *
 * Responsibilities:
 * - Orchestrates search, sorting, and view controls
 * - Handles loading / error / empty UI states
 * - Manages sidebar rendering (responsive behavior)
 * - Provides pagination at bottom of results
 *
 * It does NOT fetch data itself; it is purely presentational.
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

  /**
   * Derived UI state flags controlling rendering branches.
   */
  const isEmpty = !isLoading && !errorMessage && !hasResults
  const shouldRenderSidebar = Boolean(showSidebar && sidebarContent)

  /**
   * Sidebar is inline only on desktop viewports.
   * On mobile it is moved into a full-screen dialog.
   */
  const sidebarInline = shouldRenderSidebar && !isMobile

  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false)

  /**
   * Button label for opening mobile filter sidebar.
   */
  const mobileSidebarLabel = t('searchbar.filters')

  /**
   * Button used in mobile search controls to open sidebar dialog.
   */
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
                theme.palette.mode === DarkMode ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)',
            },
          }}
        >
          <FilterAltIcon fontSize="small" />
        </IconButton>
      </Tooltip>
    ) : null

  /**
   * Close button rendered inside mobile sidebar dialog header.
   */
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

  /**
   * Injects extra props into sidebar component when rendered in mobile mode.
   * This allows sidebar components to adapt to dialog usage (header actions, apply callbacks).
   */
  const mobileSidebarContent =
    isMobile &&
    isValidElement<{ headerActions?: ReactNode; onMobileApply?: () => void }>(sidebarContent)
      ? cloneElement(sidebarContent, {
          headerActions: mobileSidebarHeaderAction,
          onMobileApply: () => setIsMobileSidebarOpen(false),
        })
      : sidebarContent

  /**
   * Main results section handling loading, error, empty, and success states.
   */
  const resultsSection = (
    <Box component="section" aria-label={resultsRegionAriaLabel} sx={{ minWidth: 0 }}>
      {isLoading ? (
        <Box sx={{ py: 8 }}>{loadingContent ?? <LoadingSpinner label={loadingLabel} />}</Box>
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
  )

  /**
   * Responsive width behavior for the main content column.
   *
   * This ensures grid/list layouts only expand when enough space is available
   * to fit additional card columns, preventing awkward partial rows.
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
        <Box
          sx={{
            display: 'flex',
            alignItems: 'flex-start',
            justifyContent: 'center',
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
