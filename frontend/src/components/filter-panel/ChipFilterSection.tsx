import SearchIcon from '@mui/icons-material/Search'
import { Box, InputAdornment, Stack, TextField, Typography } from '@mui/material'
import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'

import { tokens } from '../../theme/tokens'
import GenreAndTagChip from '../chips/GenreAndTagChip'

const VISIBLE_CHIP_COUNT = 5
const CHIP_ROW_HEIGHT_PX = 32
const CHIP_ROW_GAP_PX = 6
const CHIP_ROW_PEEK_PX = 12
const SCROLL_CONTAINER_MAX_HEIGHT_PX =
  VISIBLE_CHIP_COUNT * CHIP_ROW_HEIGHT_PX +
  (VISIBLE_CHIP_COUNT - 1) * CHIP_ROW_GAP_PX +
  CHIP_ROW_PEEK_PX

export type ChipOption = {
  id: number
  name: string
  labels: Record<string, string>
  chipType: 'genre' | 'seriesTag'
}

type ChipFilterSectionProps = {
  options: ChipOption[]
  selectedIds: number[]
  emptyLabel: string
  onToggle: (id: number) => void
}

/**
 * A filter section that displays a list of options as chips, with an optional search field if there are many options.
 * The options are sorted with selected ones first, and then alphabetically. When the number of options exceeds a certain threshold,
 * a search field is shown to filter the options by name. The container becomes scrollable to show all options while hinting at overflow.
 */
const ChipFilterSection = ({
  options,
  selectedIds,
  emptyLabel,
  onToggle,
}: ChipFilterSectionProps) => {
  const { t } = useTranslation()
  const [query, setQuery] = useState('')

  const hasOverflow = options.length > VISIBLE_CHIP_COUNT

  // Determine which search placeholder to use based on chipType
  const chipType = options.length > 0 ? options[0].chipType : 'genre'
  const searchPlaceholder =
    chipType === 'genre'
      ? t('productions.home.filters.searchGenres')
      : t('productions.home.filters.searchTags')

  const sortedOptions = useMemo(
    () =>
      [...options].sort((a, b) => {
        const aSelected = selectedIds.includes(a.id)
        const bSelected = selectedIds.includes(b.id)
        if (aSelected !== bSelected) {
          return aSelected ? -1 : 1
        }
        return a.name.localeCompare(b.name)
      }),
    [options, selectedIds],
  )

  const filteredOptions = useMemo(() => {
    const trimmed = query.trim().toLowerCase()
    if (!trimmed) {
      return sortedOptions
    }
    return sortedOptions.filter((option) => option.name.toLowerCase().includes(trimmed))
  }, [sortedOptions, query])

  if (!sortedOptions.length) {
    return (
      <Typography variant="body2" color="text.secondary">
        {emptyLabel}
      </Typography>
    )
  }

  return (
    <Stack spacing={tokens.spacing.numericXs}>
      {hasOverflow && (
        <TextField
          size="small"
          fullWidth
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={searchPlaceholder}
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon sx={{ fontSize: 16, color: 'text.disabled' }} />
                </InputAdornment>
              ),
            },
          }}
          sx={(theme) => ({
            '& .MuiOutlinedInput-root': {
              mb: 1 / 3,
              borderRadius: tokens.borderRadius.md,
              fontSize: theme.typography.body2.fontSize,
              '& fieldset': {
                borderColor: theme.palette.divider,
              },
            },
            '& .MuiOutlinedInput-input': {
              py: '6px',
            },
          })}
        />
      )}

      {!filteredOptions.length ? (
        <Typography variant="body2" color="text.secondary">
          {emptyLabel}
        </Typography>
      ) : (
        <Box
          role={hasOverflow ? 'region' : undefined}
          aria-label={hasOverflow ? t('productions.home.filters.scrollHint') : undefined}
          tabIndex={hasOverflow ? 0 : undefined}
          sx={(theme) => ({
            maxHeight: hasOverflow ? `${SCROLL_CONTAINER_MAX_HEIGHT_PX}px` : 'none',
            overflowY: hasOverflow ? 'auto' : 'visible',
            borderRadius: tokens.borderRadius.md,
            outline: 'none',
            scrollbarWidth: hasOverflow ? 'thin' : 'auto',
            scrollbarColor: hasOverflow
              ? `${theme.palette.text.disabled} ${theme.palette.action.hover}`
              : undefined,
            '&:focus-visible': {
              boxShadow: `0 0 0 2px ${theme.palette.primary.main}`,
            },
            '&::-webkit-scrollbar': { width: 6 },
            '&::-webkit-scrollbar-track': {
              backgroundColor: theme.palette.action.hover,
              borderRadius: tokens.borderRadius.full,
            },
            '&::-webkit-scrollbar-thumb': {
              backgroundColor: theme.palette.text.disabled,
              borderRadius: tokens.borderRadius.full,
            },
          })}
        >
          <Stack spacing={0.75}>
            {filteredOptions.map((option) => (
              <Box key={`${option.chipType}-${option.id}`}>
                <GenreAndTagChip
                  id={option.id}
                  name={option.name}
                  labels={option.labels}
                  chipType={option.chipType}
                  context="search"
                  selected={selectedIds.includes(option.id)}
                  onToggle={() => onToggle(option.id)}
                />
              </Box>
            ))}
          </Stack>
        </Box>
      )}
    </Stack>
  )
}

export default ChipFilterSection
