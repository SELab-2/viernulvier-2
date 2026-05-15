import { Box, Stack, Typography } from '@mui/material'
import { useMemo } from 'react'
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
 * Renders a list of genre/tag chips in a compact scroll area.
 * Selected options are sorted to the top, then alphabetically within each group.
 */
const ChipFilterSection = ({
  options,
  selectedIds,
  emptyLabel,
  onToggle,
}: ChipFilterSectionProps) => {
  const { t } = useTranslation()

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

  if (!sortedOptions.length) {
    return (
      <Typography variant="body2" color="text.secondary">
        {emptyLabel}
      </Typography>
    )
  }

  const hasOverflow = sortedOptions.length > VISIBLE_CHIP_COUNT

  return (
    <Stack spacing={tokens.spacing.numericXs}>
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
          '&::-webkit-scrollbar': {
            width: 6,
          },
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
          {sortedOptions.map((option) => (
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
    </Stack>
  )
}

export default ChipFilterSection
