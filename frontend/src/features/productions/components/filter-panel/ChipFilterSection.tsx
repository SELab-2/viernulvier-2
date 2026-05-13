import ExpandLessIcon from '@mui/icons-material/ExpandLess'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import { Box, Button, Stack, Typography } from '@mui/material'
import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'

import { tokens } from '../../../../theme/tokens'
import GenreAndTagChip from '../../../../shared/components/chips/GenreAndTagChip'

const DEFAULT_VISIBLE_COUNT = 5

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
 * Renders a list of genre/tag chips with show-more/less overflow handling.
 * Selected options are sorted to the top, then alphabetically within each group.
 */
const ChipFilterSection = ({
  options,
  selectedIds,
  emptyLabel,
  onToggle,
}: ChipFilterSectionProps) => {
  const { t } = useTranslation()
  const [showAll, setShowAll] = useState(false)

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

  const visibleOptions = showAll ? sortedOptions : sortedOptions.slice(0, DEFAULT_VISIBLE_COUNT)
  const hasOverflow = sortedOptions.length > DEFAULT_VISIBLE_COUNT

  return (
    <Stack spacing={tokens.spacing.numericXs}>
      <Stack spacing={0.75}>
        {visibleOptions.map((option) => (
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

      {hasOverflow && (
        <Box>
          <Button
            size="small"
            onClick={() => setShowAll((prev) => !prev)}
            endIcon={
              showAll ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />
            }
            sx={{ color: 'text.secondary', px: 0, fontSize: tokens.typography.sizes.xs }}
          >
            {showAll
              ? t('productions.home.filters.showLess')
              : t('productions.home.filters.showMore')}
          </Button>
        </Box>
      )}
    </Stack>
  )
}

export default ChipFilterSection
