import GridViewIcon from '@mui/icons-material/GridView'
import ViewListIcon from '@mui/icons-material/ViewList'
import {
  Box,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  Typography,
  useTheme,
} from '@mui/material'
import { useTranslation } from 'react-i18next'
import { FaSortAmountDown, FaSortAmountUp } from 'react-icons/fa'

import SearchBar from './SearchBar'
import {
  DEFAULT_SORT_TARGET_OPTIONS,
  type SearchSortDirection,
  type SearchSortTarget,
  type SearchViewMode,
} from './types'
import { tokens } from '../../../theme/tokens'
import { DarkMode } from '../../../types/Theme'

import type { ReactNode } from 'react'

/**
 * SearchControlsBarProps
 *
 * Defines all configurable inputs for the search toolbar.
 * This component controls:
 * - search input
 * - sorting (target + direction)
 * - view mode (grid/list)
 * - optional extra controls
 */
export interface SearchControlsBarProps {
  placeholder?: string
  searchValue: string
  onSearchChange: (value: string) => void
  onSearchSubmit?: (value: string) => void
  resultCount?: number

  sortTarget?: SearchSortTarget
  onSortTargetChange?: (sortTarget: SearchSortTarget) => void

  sortDirection?: SearchSortDirection
  onSortDirectionChange?: (sortDirection: SearchSortDirection) => void

  viewMode?: SearchViewMode
  onViewModeChange?: (viewMode: SearchViewMode) => void

  showViewModeToggle?: boolean
  sortTargetOptions?: Array<{ value: SearchSortTarget; labelKey: string }>

  extraControls?: ReactNode
}

/**
 * ARIA label id for the sort dropdown.
 * Used to correctly bind InputLabel -> Select for accessibility.
 */
const SORT_TARGET_LABEL_ID = 'searchbar-sort-target-label'

/**
 * No-op fallback handlers to avoid undefined checks in JSX.
 */
const NOOP_SORT_TARGET_CHANGE: NonNullable<SearchControlsBarProps['onSortTargetChange']> = () => {}
const NOOP_SORT_DIRECTION_CHANGE: NonNullable<
  SearchControlsBarProps['onSortDirectionChange']
> = () => {}
const NOOP_VIEW_MODE_CHANGE: NonNullable<SearchControlsBarProps['onViewModeChange']> = () => {}

/**
 * SearchControlsBar
 *
 * High-level toolbar component for collection/search pages.
 *
 * Responsibilities:
 * - Renders search input
 * - Controls sorting (field + direction)
 * - Controls layout (grid/list)
 * - Shows result count
 *
 * It is a pure UI component: state is fully controlled via props.
 */
const SearchControlsBar = ({
  placeholder,
  searchValue,
  onSearchChange,
  onSearchSubmit,
  resultCount,
  sortTarget = 'date',
  onSortTargetChange = NOOP_SORT_TARGET_CHANGE,
  sortDirection = 'desc',
  onSortDirectionChange = NOOP_SORT_DIRECTION_CHANGE,
  viewMode = 'grid',
  onViewModeChange = NOOP_VIEW_MODE_CHANGE,
  showViewModeToggle = true,
  sortTargetOptions = DEFAULT_SORT_TARGET_OPTIONS,
  extraControls,
}: SearchControlsBarProps) => {
  const { t } = useTranslation()
  const theme = useTheme()

  /**
   * Ensure sort target is always valid.
   * If invalid (e.g. removed option), fallback to first available option.
   */
  const effectiveSortTarget = sortTargetOptions.some((option) => option.value === sortTarget)
    ? sortTarget
    : (sortTargetOptions[0]?.value ?? 'name')

  /**
   * Theme-aware interaction colors for hover states.
   */
  const interactionColor =
    theme.palette.mode === DarkMode ? tokens.colors.neutral.white : tokens.colors.neutral.black

  const interactionHoverBackground =
    theme.palette.mode === DarkMode ? tokens.colors.overlay.white05 : tokens.colors.overlay.black05

  /**
   * Precomputed next direction for toggle behavior.
   */
  const nextSortDirection: SearchSortDirection = sortDirection === 'asc' ? 'desc' : 'asc'

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {/* Main toolbar row */}
      <Box
        sx={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: 2,
          alignItems: 'center',
          '& > *': { minWidth: 0 },
        }}
      >
        {/* Search input */}
        <Box sx={{ flex: '1 1 320px', minWidth: 240 }}>
          <SearchBar
            placeholder={placeholder}
            searchValue={searchValue}
            onSearchChange={onSearchChange}
            onSearchSubmit={onSearchSubmit}
          />
        </Box>

        {/* Controls cluster (sorting, view, extras, count) */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
          {/* Sort controls group */}
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 0.75,
              flexShrink: 0,
            }}
          >
            {/* Sort target selector */}
            <FormControl size="small" sx={{ minWidth: 180 }}>
              <InputLabel id={SORT_TARGET_LABEL_ID}>{t('searchbar.sort.targetLabel')}</InputLabel>

              <Select
                labelId={SORT_TARGET_LABEL_ID}
                value={effectiveSortTarget}
                label={t('searchbar.sort.targetLabel')}
                onChange={(event) => onSortTargetChange(event.target.value as SearchSortTarget)}
                sx={{
                  height: 40,
                  backgroundColor: theme.palette.background.default,
                }}
              >
                {sortTargetOptions.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {t(option.labelKey)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* Sort direction toggle */}
            <Tooltip
              title={
                nextSortDirection === 'asc'
                  ? t('searchbar.sort.switchToAscending')
                  : t('searchbar.sort.switchToDescending')
              }
            >
              <ToggleButton
                value={sortDirection}
                aria-label={
                  nextSortDirection === 'asc'
                    ? t('searchbar.sort.switchToAscending')
                    : t('searchbar.sort.switchToDescending')
                }
                onClick={() => onSortDirectionChange(nextSortDirection)}
                sx={{
                  width: 40,
                  minWidth: 40,
                  height: 40,
                  p: 0,
                  flexShrink: 0,
                  backgroundColor: theme.palette.background.default,
                  '&:hover': {
                    borderColor: interactionColor,
                    backgroundColor: interactionHoverBackground,
                  },
                }}
              >
                {sortDirection === 'asc' ? (
                  <FaSortAmountUp size={16} />
                ) : (
                  <FaSortAmountDown size={16} />
                )}
              </ToggleButton>
            </Tooltip>
          </Box>

          {/* Extra injected controls (filters, etc.) */}
          {extraControls}

          {/* View mode toggle */}
          {showViewModeToggle ? (
            <ToggleButtonGroup
              exclusive
              size="small"
              value={viewMode}
              onChange={(_event, nextMode: SearchViewMode | null) => {
                if (nextMode) {
                  onViewModeChange(nextMode)
                }
              }}
              sx={{
                height: 40,
                backgroundColor: theme.palette.background.default,
                borderRadius: '8px',
                border: `1px solid ${theme.palette.divider}`,
                '& .MuiToggleButton-root': {
                  border: 'none',
                  px: 1.2,
                  color: theme.palette.text.primary,
                  '&:not(:first-of-type)': {
                    borderLeft: `1px solid ${theme.palette.divider}`,
                  },
                  '&:hover': {
                    backgroundColor: interactionHoverBackground,
                  },
                  '&.Mui-selected': {
                    color: theme.palette.primary.main, // Of een andere accentkleur
                    backgroundColor: interactionHoverBackground,
                    '&:hover': {
                      backgroundColor: interactionHoverBackground,
                    },
                  },
                },
              }}
            >
              <Tooltip title={t('searchbar.layout.grid')}>
                <ToggleButton value="grid" aria-label={t('searchbar.layout.grid')}>
                  <GridViewIcon fontSize="small" />
                </ToggleButton>
              </Tooltip>

              <Tooltip title={t('searchbar.layout.list')}>
                <ToggleButton value="list" aria-label={t('searchbar.layout.list')}>
                  <ViewListIcon fontSize="small" />
                </ToggleButton>
              </Tooltip>
            </ToggleButtonGroup>
          ) : null}

          {/* Result count */}
          {typeof resultCount === 'number' ? (
            <Typography variant="body2" color="text.secondary" sx={{ whiteSpace: 'nowrap' }}>
              {t('searchbar.resultsFound', { count: resultCount })}
            </Typography>
          ) : null}
        </Box>
      </Box>
    </Box>
  )
}

export default SearchControlsBar
