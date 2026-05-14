import { Button, Divider, Paper, Stack, Typography, Box } from '@mui/material'
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs'
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider'
import 'dayjs/locale/nl'
import { useMemo, type ReactNode } from 'react'
import { useTranslation } from 'react-i18next'

import ChipFilterSection, { type ChipOption } from './ChipFilterSection'
import FilterCheckbox from './FilterCheckbox'
import FilterDatePicker from './FilterDatePicker'
import FilterSection from './FilterSection'
import { tokens } from '../../../../theme/tokens'

import type { Genre } from '../../../../types/Genres'
import type { AttendanceMode, PerformerType } from '../../../../types/Productions'
import type { Tag } from '../../../../types/Tags'

/**
 * FilterPanel
 *
 * Central filtering UI for the productions page.
 *
 * Responsibilities:
 * - Date filtering (start/end range)
 * - Genre selection (multi-select chips)
 * - Tag selection (multi-select chips)
 * - Performer type filtering (solo/group)
 * - Attendance mode filtering (online/offline)
 * - Clearing all active filters
 *
 */

export interface FilterPanelProps {
  attendanceMode?: AttendanceMode
  performerType?: PerformerType
  firstEventStartAfter: string
  firstEventStartBefore: string
  selectedGenreIds: number[]
  selectedTagIds: number[]
  genres: Genre[]
  tags: Tag[]
  onAttendanceModeToggle: (value: AttendanceMode) => void
  onPerformerTypeToggle: (value: PerformerType) => void
  onFirstEventStartAfterChange: (value: string) => void
  onFirstEventStartBeforeChange: (value: string) => void
  onGenreSelectionChange: (ids: number[]) => void
  onTagSelectionChange: (ids: number[]) => void
  onClearFilters: () => void
  headerActions?: ReactNode
  onMobileApply?: () => void
}

/**
 * Toggles a numeric ID inside an array immutably.
 * Used for genre/tag selection logic.
 */
const toggleIdInArray = (values: number[], id: number): number[] =>
  values.includes(id) ? values.filter((v) => v !== id) : [...values, id]

/**
 * Resolves a human-readable display name for a filter entry.
 *
 * Supports:
 * - Precomputed `display_name`
 * - Multilingual `name` fallback object
 */
const getLocalizedName = (
  entry: Pick<Genre, 'display_name' | 'name'> | Pick<Tag, 'display_name' | 'name'>,
  language: string,
): string => {
  if (entry.display_name) {
    return entry.display_name
  }

  if (!entry.name) {
    return ''
  }

  return (
    entry.name[language] ?? entry.name[language.split('-')[0]] ?? Object.values(entry.name)[0] ?? ''
  )
}

/**
 * Converts API genre/tag entries into chip-compatible UI options.
 */
const toChipOptions = (
  entries: Array<Genre | Tag>,
  chipType: ChipOption['chipType'],
  language: string,
): ChipOption[] =>
  entries
    .map((entry) => {
      const name = getLocalizedName(entry, language)

      return {
        id: entry.id,
        name,
        labels: entry.name ?? { [language]: name },
        chipType,
      }
    })
    .filter((option) => option.name)

const FilterPanel = ({
  attendanceMode,
  performerType,
  firstEventStartAfter,
  firstEventStartBefore,
  selectedGenreIds,
  selectedTagIds,
  genres,
  tags,
  onAttendanceModeToggle,
  onPerformerTypeToggle,
  onFirstEventStartAfterChange,
  onFirstEventStartBeforeChange,
  onGenreSelectionChange,
  onTagSelectionChange,
  onClearFilters,
  headerActions,
  onMobileApply,
}: FilterPanelProps) => {
  const { i18n, t } = useTranslation()

  // Determine correct locale for date picker
  const adapterLocale = i18n.language.startsWith('nl') ? 'nl' : 'en'

  // Memoized filter options to avoid recalculations on re-render
  const genreOptions = useMemo(
    () => toChipOptions(genres, 'genre', i18n.language),
    [genres, i18n.language],
  )

  const tagOptions = useMemo(
    () => toChipOptions(tags, 'seriesTag', i18n.language),
    [tags, i18n.language],
  )

  /**
   * Determines whether any filter is currently active.
   * Used to enable/disable the "clear filters" button.
   */
  const hasActiveFilters =
    attendanceMode !== undefined ||
    performerType !== undefined ||
    Boolean(firstEventStartAfter) ||
    Boolean(firstEventStartBefore) ||
    selectedGenreIds.length > 0 ||
    selectedTagIds.length > 0

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs} adapterLocale={adapterLocale}>
      {/* Main filter panel container */}
      <Paper
        variant="outlined"
        sx={(theme) => ({
          borderRadius: tokens.borderRadius.lg,
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          height: { xs: '100dvh', md: 'auto' },
          maxHeight: { xs: '100dvh', md: 'none' },
          backgroundColor: theme.palette.background.paper,
        })}
      >
        {/* Header section */}
        <Stack
          direction="row"
          spacing={1}
          sx={(theme) => ({
            alignItems: 'center',
            justifyContent: 'space-between',
            px: tokens.spacing.numericMd,
            py: tokens.spacing.numericSm,
            backgroundColor: theme.palette.background.default,
            borderBottom: `1px solid ${theme.palette.divider}`,
          })}
        >
          <Typography
            variant="subtitle2"
            component="h2"
            sx={{
              fontWeight: tokens.typography.weights.medium,
              fontSize: tokens.typography.sizes.base,
              lineHeight: tokens.typography.lineHeights.tight,
            }}
          >
            {t('productions.home.filterPanelTitle')}
          </Typography>

          {/* Header actions (e.g. additional buttons) */}
          <Stack direction="row" spacing={1} sx={{ alignItems: 'center', flexShrink: 0 }}>
            <Button
              size="small"
              variant="outlined"
              onClick={onClearFilters}
              disabled={!hasActiveFilters}
              sx={{
                color: 'text.primary',
                borderColor: 'text.primary',
                fontSize: tokens.typography.sizes.xs,
                transition: tokens.transitions.fast,
                '&:hover': { borderColor: 'text.primary', backgroundColor: 'action.hover' },
              }}
            >
              {t('productions.home.filters.clear')}
            </Button>
            {headerActions}
          </Stack>
        </Stack>

        {/* Scrollable filter body */}
        <Box sx={{ flex: 1, minHeight: 0, overflowY: 'auto' }}>
          {/* Date filters */}
          <FilterSection title={t('productions.home.filters.date')}>
            <Stack spacing={tokens.spacing.numericMd}>
              <FilterDatePicker
                label={t('productions.home.filters.startAfter')}
                value={firstEventStartAfter}
                onChange={onFirstEventStartAfterChange}
              />
              <FilterDatePicker
                label={t('productions.home.filters.startBefore')}
                value={firstEventStartBefore}
                onChange={onFirstEventStartBeforeChange}
              />
            </Stack>
          </FilterSection>

          <Divider />

          {/* Genre filters */}
          <FilterSection title={t('productions.home.filters.genres')}>
            <ChipFilterSection
              options={genreOptions}
              selectedIds={selectedGenreIds}
              emptyLabel={t('productions.home.filters.noGenres')}
              onToggle={(id) => onGenreSelectionChange(toggleIdInArray(selectedGenreIds, id))}
            />
          </FilterSection>

          <Divider />

          {/* Tag filters */}
          <FilterSection title={t('productions.home.filters.tags')}>
            <ChipFilterSection
              options={tagOptions}
              selectedIds={selectedTagIds}
              emptyLabel={t('productions.home.filters.noTags')}
              onToggle={(id) => onTagSelectionChange(toggleIdInArray(selectedTagIds, id))}
            />
          </FilterSection>

          <Divider />

          {/* Performer type filters */}
          <FilterSection
            title={t('productions.home.filters.performerType')}
            defaultExpanded={false}
          >
            <Stack>
              <FilterCheckbox
                label={t('productions.detail.meta.solo')}
                checked={performerType === 'solo'}
                onChange={() => onPerformerTypeToggle('solo')}
              />
              <FilterCheckbox
                label={t('productions.detail.meta.group')}
                checked={performerType === 'group'}
                onChange={() => onPerformerTypeToggle('group')}
              />
            </Stack>
          </FilterSection>

          <Divider />

          {/* Attendance mode filters */}
          <FilterSection
            title={t('productions.home.filters.attendanceMode')}
            defaultExpanded={false}
          >
            <Stack>
              <FilterCheckbox
                label={t('productions.detail.meta.offline')}
                checked={attendanceMode === 'offline'}
                onChange={() => onAttendanceModeToggle('offline')}
              />
              <FilterCheckbox
                label={t('productions.detail.meta.online')}
                checked={attendanceMode === 'online'}
                onChange={() => onAttendanceModeToggle('online')}
              />
            </Stack>
          </FilterSection>
        </Box>

        {/* Mobile apply button */}
        {onMobileApply ? (
          <Box
            sx={(theme) => ({
              p: tokens.spacing.numericMd,
              display: { xs: 'block', md: 'none' },
              borderTop: `1px solid ${theme.palette.divider}`,
              backgroundColor: theme.palette.background.paper,
              pb: 'max(env(safe-area-inset-bottom), 16px)',
            })}
          >
            <Button
              fullWidth
              variant="contained"
              onClick={onMobileApply}
              aria-label={t('searchbar.search')}
              sx={{ fontSize: tokens.typography.sizes.sm, py: tokens.spacing.numericSm }}
            >
              {t('searchbar.search')}
            </Button>
          </Box>
        ) : null}
      </Paper>
    </LocalizationProvider>
  )
}

export default FilterPanel
