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
import { FaSortAmountDown, FaSortAmountUp } from 'react-icons/fa'
import { useTranslation } from 'react-i18next'
import SearchBar from './SearchBar'
import type { SearchSortDirection, SearchSortTarget, SearchViewMode } from './types'
import { DEFAULT_SORT_TARGET_OPTIONS } from './types'

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
}

const SORT_TARGET_LABEL_ID = 'searchbar-sort-target-label'
const NOOP_SORT_TARGET_CHANGE: NonNullable<SearchControlsBarProps['onSortTargetChange']> = () => {}
const NOOP_SORT_DIRECTION_CHANGE: NonNullable<
  SearchControlsBarProps['onSortDirectionChange']
> = () => {}
const NOOP_VIEW_MODE_CHANGE: NonNullable<SearchControlsBarProps['onViewModeChange']> = () => {}

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
}: SearchControlsBarProps) => {
  const { t } = useTranslation()
  const theme = useTheme()

  // Fall back to the first allowed sort target when the current one is no longer valid.
  const effectiveSortTarget = sortTargetOptions.some((option) => option.value === sortTarget)
    ? sortTarget
    : (sortTargetOptions[0]?.value ?? 'name')
  const nextSortDirection: SearchSortDirection = sortDirection === 'asc' ? 'desc' : 'asc'

  return (
    <Box display="flex" flexDirection="column" gap={2}>
      {/* Search and control row. */}
      <Box
        display="flex"
        flexWrap="wrap"
        gap={2}
        alignItems="center"
        sx={{ '& > *': { minWidth: 0 } }}
      >
        <Box sx={{ flex: '1 1 320px', minWidth: 240 }}>
          <SearchBar
            placeholder={placeholder}
            searchValue={searchValue}
            onSearchChange={onSearchChange}
            onSearchSubmit={onSearchSubmit}
          />
        </Box>

        <Box display="flex" alignItems="center" gap={2} flexWrap="wrap">
          <FormControl size="small" sx={{ minWidth: 180 }}>
            <InputLabel id={SORT_TARGET_LABEL_ID}>{t('searchbar.sort.targetLabel')}</InputLabel>
            {/* Sort target selector. */}
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

          {/* Sort direction toggle. */}
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
                height: 40,
                px: 1.2,
                backgroundColor: theme.palette.background.default,
              }}
            >
              {sortDirection === 'asc' ? (
                <FaSortAmountUp size={16} />
              ) : (
                <FaSortAmountDown size={16} />
              )}
            </ToggleButton>
          </Tooltip>

          {/* View mode toggle. */}
          {showViewModeToggle ? (
            <ToggleButtonGroup
              exclusive
              size="small"
              value={viewMode}
              aria-label={t('searchbar.layout.label')}
              onChange={(_event, nextMode: SearchViewMode | null) => {
                if (nextMode) {
                  onViewModeChange(nextMode)
                }
              }}
              sx={{
                height: 40,
                '& .MuiToggleButton-root': {
                  px: 1.2,
                  backgroundColor: theme.palette.background.default,
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

          {/* Result count indicator. */}
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
