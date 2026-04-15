import ExpandLessIcon from '@mui/icons-material/ExpandLess'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Button,
  Checkbox,
  Divider,
  FormControlLabel,
  Paper,
  Stack,
  Typography,
} from '@mui/material'
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs'
import { DatePicker } from '@mui/x-date-pickers/DatePicker'
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider'
import dayjs, { type Dayjs } from 'dayjs'
import 'dayjs/locale/nl'
import { useMemo, useRef, useState, type KeyboardEvent, type ReactNode } from 'react'
import { useTranslation } from 'react-i18next'

import { tokens } from '../../theme/tokens'
import GenreAndTagChip from '../chips/GenreAndTagChip'

import type { Genre } from '../../types/Genres'
import type { AttendanceMode, PerformerType } from '../../types/Productions'
import type { Tag } from '../../types/Tags'

const DEFAULT_VISIBLE_FILTER_OPTIONS = 5
const DATE_PICKER_FORMAT = 'DD/MM/YYYY'

type FilterSectionProps = {
  title: string
  children: ReactNode
  defaultExpanded?: boolean
}

type ChipOption = {
  id: number
  name: string
  labels: Record<string, string>
  chipType: 'genre' | 'seriesTag'
}

type DateFieldState = {
  sourceValue: string
  draft: Dayjs | null
  hasError: boolean
}

export interface ProductionFilterPanelProps {
  attendanceModes: AttendanceMode[]
  performerTypes: PerformerType[]
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
}

const getLocalizedDisplayName = (
  entry: Pick<Genre, 'display_name' | 'name'> | Pick<Tag, 'display_name' | 'name'>,
  language: string,
): string => {
  if (entry.display_name) {
    return entry.display_name
  }

  if (!entry.name) {
    return ''
  }

  const exactMatch = entry.name[language]
  if (exactMatch) {
    return exactMatch
  }

  const shortLanguage = language.split('-')[0]
  const partialMatch = entry.name[shortLanguage]
  if (partialMatch) {
    return partialMatch
  }

  return Object.values(entry.name)[0] ?? ''
}

const toggleIdInArray = (values: number[], id: number): number[] => {
  if (values.includes(id)) {
    return values.filter((value) => value !== id)
  }

  return [...values, id]
}

const parseDateValue = (value: string): Dayjs | null => {
  if (!value) {
    return null
  }

  const parsed = dayjs(value)
  return parsed.isValid() ? parsed : null
}

const formatDateValue = (value: Dayjs | null): string => {
  if (!value?.isValid()) {
    return ''
  }

  return value.format('YYYY-MM-DD')
}

const createDateFieldState = (sourceValue: string): DateFieldState => ({
  sourceValue,
  draft: parseDateValue(sourceValue),
  hasError: false,
})

const FilterSection = ({ title, children, defaultExpanded = true }: FilterSectionProps) => {
  return (
    <Accordion defaultExpanded={defaultExpanded} disableGutters elevation={0}>
      <AccordionSummary expandIcon={<ExpandMoreIcon fontSize="small" />}>
        <Typography
          variant="body2"
          sx={{ fontWeight: tokens.typography.weights.medium }}
          component="h2"
        >
          {title}
        </Typography>
      </AccordionSummary>
      <AccordionDetails sx={{ paddingTop: 0 }}>{children}</AccordionDetails>
    </Accordion>
  )
}

const ChipFilterSection = ({
  options,
  selectedIds,
  emptyLabel,
  onToggle,
}: {
  options: ChipOption[]
  selectedIds: number[]
  emptyLabel: string
  onToggle: (id: number) => void
}) => {
  const { t } = useTranslation()
  const [showAll, setShowAll] = useState(false)

  const sortedOptions = useMemo(() => {
    return [...options].sort((left, right) => {
      const leftSelected = selectedIds.includes(left.id)
      const rightSelected = selectedIds.includes(right.id)

      if (leftSelected !== rightSelected) {
        return leftSelected ? -1 : 1
      }

      return left.name.localeCompare(right.name)
    })
  }, [options, selectedIds])

  const visibleOptions = showAll
    ? sortedOptions
    : sortedOptions.slice(0, DEFAULT_VISIBLE_FILTER_OPTIONS)
  const hasOverflow = sortedOptions.length > DEFAULT_VISIBLE_FILTER_OPTIONS
  const visibleSelectedOptions = visibleOptions.filter((option) => selectedIds.includes(option.id))
  const visibleUnselectedOptions = visibleOptions.filter(
    (option) => !selectedIds.includes(option.id),
  )

  if (!sortedOptions.length) {
    return (
      <Typography variant="body2" color="text.secondary">
        {emptyLabel}
      </Typography>
    )
  }

  return (
    <Stack spacing={tokens.spacing.numericXs}>
      <Stack spacing={0.75}>
        {visibleSelectedOptions.map((option) => (
          <Box key={`${option.chipType}-${option.id}`}>
            <GenreAndTagChip
              id={option.id}
              name={option.name}
              labels={option.labels}
              chipType={option.chipType}
              context="search"
              selected
              onToggle={() => onToggle(option.id)}
            />
          </Box>
        ))}

        {visibleUnselectedOptions.map((option) => (
          <Box key={`${option.chipType}-${option.id}`}>
            <GenreAndTagChip
              id={option.id}
              name={option.name}
              labels={option.labels}
              chipType={option.chipType}
              context="search"
              selected={false}
              onToggle={() => onToggle(option.id)}
            />
          </Box>
        ))}
      </Stack>

      {hasOverflow ? (
        <Box>
          <Button
            size="small"
            onClick={() => setShowAll((value) => !value)}
            endIcon={
              showAll ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />
            }
            sx={{
              color: 'text.secondary',
              px: 0,
              fontSize: tokens.typography.sizes.xs,
            }}
          >
            {showAll
              ? t('productions.home.filters.showLess')
              : t('productions.home.filters.showMore')}
          </Button>
        </Box>
      ) : null}
    </Stack>
  )
}

const FilterCheckbox = ({
  label,
  checked,
  onChange,
}: {
  label: string
  checked: boolean
  onChange: () => void
}) => (
  <FormControlLabel
    slotProps={{ typography: { variant: 'body2' } }}
    sx={{ height: 24 }}
    label={label}
    control={<Checkbox size="small" checked={checked} onChange={onChange} color="default" />}
  />
)

const ProductionFilterPanel = ({
  attendanceModes,
  performerTypes,
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
}: ProductionFilterPanelProps) => {
  const { i18n, t } = useTranslation()
  const adapterLocale = i18n.language.startsWith('nl') ? 'nl' : 'en'
  const [startAfterField, setStartAfterField] = useState<DateFieldState>(() =>
    createDateFieldState(firstEventStartAfter),
  )
  const startAfterFieldRef = useRef(startAfterField)
  const [startBeforeField, setStartBeforeField] = useState<DateFieldState>(() =>
    createDateFieldState(firstEventStartBefore),
  )
  const startBeforeFieldRef = useRef(startBeforeField)

  const currentStartAfterField =
    startAfterField.sourceValue === firstEventStartAfter
      ? startAfterField
      : createDateFieldState(firstEventStartAfter)
  const currentStartBeforeField =
    startBeforeField.sourceValue === firstEventStartBefore
      ? startBeforeField
      : createDateFieldState(firstEventStartBefore)

  const applyStartAfterDraft = () => {
    const latestField =
      startAfterFieldRef.current.sourceValue === firstEventStartAfter
        ? startAfterFieldRef.current
        : createDateFieldState(firstEventStartAfter)

    if (latestField.hasError) {
      return
    }

    onFirstEventStartAfterChange(formatDateValue(latestField.draft))
  }

  const applyStartBeforeDraft = () => {
    const latestField =
      startBeforeFieldRef.current.sourceValue === firstEventStartBefore
        ? startBeforeFieldRef.current
        : createDateFieldState(firstEventStartBefore)

    if (latestField.hasError) {
      return
    }

    onFirstEventStartBeforeChange(formatDateValue(latestField.draft))
  }

  const handleDateInputEnter = (event: KeyboardEvent, applyDraft: () => void) => {
    if (event.key !== 'Enter') {
      return
    }

    applyDraft()
  }

  const genreOptions = useMemo(
    () =>
      genres
        .map((genre) => {
          const name = getLocalizedDisplayName(genre, i18n.language)

          return {
            id: genre.id,
            name,
            labels: genre.name ?? { [i18n.language]: name },
            chipType: 'genre' as const,
          }
        })
        .filter((genre) => genre.name),
    [genres, i18n.language],
  )

  const tagOptions = useMemo(
    () =>
      tags
        .map((tag) => {
          const name = getLocalizedDisplayName(tag, i18n.language)

          return {
            id: tag.id,
            name,
            labels: tag.name ?? { [i18n.language]: name },
            chipType: 'seriesTag' as const,
          }
        })
        .filter((tag) => tag.name),
    [i18n.language, tags],
  )

  const hasActiveFilters =
    attendanceModes.length > 0 ||
    performerTypes.length > 0 ||
    Boolean(firstEventStartAfter) ||
    Boolean(firstEventStartBefore) ||
    selectedGenreIds.length > 0 ||
    selectedTagIds.length > 0

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs} adapterLocale={adapterLocale}>
      <Paper
        variant="outlined"
        sx={{
          borderRadius: tokens.borderRadius.lg,
          overflow: 'hidden',
          height: 'fit-content',
        }}
      >
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
              '&:hover': {
                borderColor: 'text.primary',
                backgroundColor: 'action.hover',
              },
            }}
          >
            {t('productions.home.filters.clear')}
          </Button>
        </Stack>

        <FilterSection title={t('productions.home.filters.date')}>
          <Stack spacing={tokens.spacing.numericMd}>
            <DatePicker
              label={t('productions.home.filters.startAfter')}
              value={currentStartAfterField.draft}
              format={DATE_PICKER_FORMAT}
              onChange={(value, context) => {
                const nextState = {
                  sourceValue: firstEventStartAfter,
                  draft: value,
                  hasError: context.validationError != null,
                }
                startAfterFieldRef.current = nextState
                setStartAfterField(nextState)
              }}
              onClose={applyStartAfterDraft}
              slotProps={{
                textField: {
                  size: 'small',
                  fullWidth: true,
                  slotProps: {
                    inputLabel: { shrink: true },
                  },
                  onBlur: applyStartAfterDraft,
                  onKeyDown: (event) => handleDateInputEnter(event, applyStartAfterDraft),
                },
                actionBar: {
                  actions: ['clear', 'accept'],
                },
              }}
            />
            <DatePicker
              label={t('productions.home.filters.startBefore')}
              value={currentStartBeforeField.draft}
              format={DATE_PICKER_FORMAT}
              onChange={(value, context) => {
                const nextState = {
                  sourceValue: firstEventStartBefore,
                  draft: value,
                  hasError: context.validationError != null,
                }
                startBeforeFieldRef.current = nextState
                setStartBeforeField(nextState)
              }}
              onClose={applyStartBeforeDraft}
              slotProps={{
                textField: {
                  size: 'small',
                  fullWidth: true,
                  slotProps: {
                    inputLabel: { shrink: true },
                  },
                  onBlur: applyStartBeforeDraft,
                  onKeyDown: (event) => handleDateInputEnter(event, applyStartBeforeDraft),
                },
                actionBar: {
                  actions: ['clear', 'accept'],
                },
              }}
            />
          </Stack>
        </FilterSection>

        <Divider />

        <FilterSection title={t('productions.home.filters.performerType')}>
          <Stack>
            <FilterCheckbox
              label={t('productions.detail.meta.solo')}
              checked={performerTypes.includes('solo')}
              onChange={() => onPerformerTypeToggle('solo')}
            />
            <FilterCheckbox
              label={t('productions.detail.meta.group')}
              checked={performerTypes.includes('group')}
              onChange={() => onPerformerTypeToggle('group')}
            />
          </Stack>
        </FilterSection>

        <Divider />

        <FilterSection title={t('productions.home.filters.genres')}>
          <ChipFilterSection
            options={genreOptions}
            selectedIds={selectedGenreIds}
            emptyLabel={t('productions.home.filters.noGenres')}
            onToggle={(id) => onGenreSelectionChange(toggleIdInArray(selectedGenreIds, id))}
          />
        </FilterSection>

        <Divider />

        <FilterSection title={t('productions.home.filters.tags')}>
          <ChipFilterSection
            options={tagOptions}
            selectedIds={selectedTagIds}
            emptyLabel={t('productions.home.filters.noTags')}
            onToggle={(id) => onTagSelectionChange(toggleIdInArray(selectedTagIds, id))}
          />
        </FilterSection>

        <Divider />

        <FilterSection title={t('productions.home.filters.attendanceMode')}>
          <Stack>
            <FilterCheckbox
              label={t('productions.detail.meta.offline')}
              checked={attendanceModes.includes('offline')}
              onChange={() => onAttendanceModeToggle('offline')}
            />
            <FilterCheckbox
              label={t('productions.detail.meta.online')}
              checked={attendanceModes.includes('online')}
              onChange={() => onAttendanceModeToggle('online')}
            />
          </Stack>
        </FilterSection>
      </Paper>
    </LocalizationProvider>
  )
}

export default ProductionFilterPanel
