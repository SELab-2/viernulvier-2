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
  Stack,
  Typography,
} from '@mui/material'
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs'
import { DatePicker } from '@mui/x-date-pickers/DatePicker'
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider'
import dayjs, { type Dayjs } from 'dayjs'
import 'dayjs/locale/nl'
import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import type { Genre } from '../../types/Genres'
import type { AttendanceMode, PerformerType } from '../../types/Productions'
import type { Tag } from '../../types/Tags'
import GenreAndTagChip from '../chips/GenreAndTagChip'

const DEFAULT_VISIBLE_FILTER_OPTIONS = 8
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
  if (!value || !value.isValid()) {
    return ''
  }

  return value.format('YYYY-MM-DD')
}

const FilterSection = ({ title, children, defaultExpanded = true }: FilterSectionProps) => {
  return (
    <Accordion
      defaultExpanded={defaultExpanded}
      disableGutters
      elevation={0}
      sx={{
        border: (theme) => `1px solid ${theme.palette.divider}`,
        borderRadius: '12px !important',
        overflow: 'hidden',
        '&:before': { display: 'none' },
      }}
    >
      <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ px: 2, py: 0.5 }}>
        <Typography variant="subtitle1" component="h2">
          {title}
        </Typography>
      </AccordionSummary>
      <AccordionDetails sx={{ px: 2, pt: 0, pb: 2 }}>{children}</AccordionDetails>
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
    <Stack spacing={1}>
      <Stack spacing={1}>
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

        {visibleSelectedOptions.length > 0 && visibleUnselectedOptions.length > 0 ? (
          <Divider />
        ) : null}

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
            endIcon={showAll ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            sx={{
              color: 'text.primary',
              borderColor: 'text.primary',
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
  const [startAfterDraft, setStartAfterDraft] = useState<Dayjs | null>(
    parseDateValue(firstEventStartAfter),
  )
  const [startBeforeDraft, setStartBeforeDraft] = useState<Dayjs | null>(
    parseDateValue(firstEventStartBefore),
  )

  useEffect(() => {
    setStartAfterDraft(parseDateValue(firstEventStartAfter))
  }, [firstEventStartAfter])

  useEffect(() => {
    setStartBeforeDraft(parseDateValue(firstEventStartBefore))
  }, [firstEventStartBefore])

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
      <Stack spacing={2}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" gap={1}>
          <Typography variant="subtitle1" component="h2">
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
              '&:hover': {
                borderColor: 'text.primary',
                backgroundColor: 'action.hover',
              },
            }}
          >
            {t('productions.home.filters.clear')}
          </Button>
        </Stack>

        <FilterSection title={t('productions.home.filters.attendanceMode')}>
          <Stack>
            <FormControlLabel
              control={
                <Checkbox
                  checked={attendanceModes.includes('offline')}
                  onChange={() => onAttendanceModeToggle('offline')}
                  color="default"
                />
              }
              label={t('productions.detail.meta.offline')}
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={attendanceModes.includes('online')}
                  onChange={() => onAttendanceModeToggle('online')}
                  color="default"
                />
              }
              label={t('productions.detail.meta.online')}
            />
          </Stack>
        </FilterSection>

        <FilterSection title={t('productions.home.filters.performerType')}>
          <Stack>
            <FormControlLabel
              control={
                <Checkbox
                  checked={performerTypes.includes('solo')}
                  onChange={() => onPerformerTypeToggle('solo')}
                  color="default"
                />
              }
              label={t('productions.detail.meta.solo')}
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={performerTypes.includes('group')}
                  onChange={() => onPerformerTypeToggle('group')}
                  color="default"
                />
              }
              label={t('productions.detail.meta.group')}
            />
          </Stack>
        </FilterSection>

        <FilterSection title={t('productions.home.filters.genres')}>
          <ChipFilterSection
            options={genreOptions}
            selectedIds={selectedGenreIds}
            emptyLabel={t('productions.home.filters.noGenres')}
            onToggle={(id) => onGenreSelectionChange(toggleIdInArray(selectedGenreIds, id))}
          />
        </FilterSection>

        <FilterSection title={t('productions.home.filters.tags')}>
          <ChipFilterSection
            options={tagOptions}
            selectedIds={selectedTagIds}
            emptyLabel={t('productions.home.filters.noTags')}
            onToggle={(id) => onTagSelectionChange(toggleIdInArray(selectedTagIds, id))}
          />
        </FilterSection>

        <FilterSection title={t('productions.home.filters.date')}>
          <Stack spacing={2}>
            <DatePicker
              label={t('productions.home.filters.startAfter')}
              value={startAfterDraft}
              format={DATE_PICKER_FORMAT}
              onChange={(value) => setStartAfterDraft(value)}
              onAccept={(value) => onFirstEventStartAfterChange(formatDateValue(value))}
              slotProps={{
                textField: {
                  size: 'small',
                  fullWidth: true,
                },
                actionBar: {
                  actions: ['clear', 'accept'],
                },
              }}
            />
            <DatePicker
              label={t('productions.home.filters.startBefore')}
              value={startBeforeDraft}
              format={DATE_PICKER_FORMAT}
              onChange={(value) => setStartBeforeDraft(value)}
              onAccept={(value) => onFirstEventStartBeforeChange(formatDateValue(value))}
              slotProps={{
                textField: {
                  size: 'small',
                  fullWidth: true,
                },
                actionBar: {
                  actions: ['clear', 'accept'],
                },
              }}
            />
          </Stack>
        </FilterSection>
      </Stack>
    </LocalizationProvider>
  )
}

export default ProductionFilterPanel
