import { tokens } from '../../theme/tokens'

import type { SxProps, Theme } from '@mui/material'
import type { GetGenreAndTagChipStylesInput } from '../../types/GenreAndTagChip'

/**
 * Returns CSS styles for a genre or series-tag chip, depending on the selected context,
 * chip type, and whether the chip is selected or not.
 *
 * @param {GetGenreAndTagChipStylesInput} props - Input properties for the chip.
 * @returns {SxProps<Theme>} - CSS styles for the chip.
 */
export const getGenreAndTagChipStyles = ({
  theme,
  selected,
  context,
  chipType,
}: GetGenreAndTagChipStylesInput): SxProps<Theme> => {
  const accentMain = theme.palette.accent?.main ?? theme.palette.primary.main
  const accentHover = theme.palette.accent?.dark ?? accentMain
  const seriesMain = tokens.colors.series.main
  const seriesHover = tokens.colors.series.dark
  const selectedBg = chipType === 'genre' ? accentMain : seriesMain
  const selectedHoverBg = chipType === 'genre' ? accentHover : seriesHover
  const selectedHoverStyles =
    context !== 'static'
      ? {
          '&:hover': {
            backgroundColor: `${selectedHoverBg} !important`,
            color: theme.palette.getContrastText(selectedHoverBg),
            borderColor: selectedBg,
          },
        }
      : {}
  const unselectedHoverStyles =
    context !== 'static'
      ? {
          '&:hover': {
            backgroundColor: selectedBg,
            color: theme.palette.getContrastText(selectedBg),
            borderColor: selectedBg,
          },
        }
      : {}

  const base: SxProps<Theme> = {
    borderRadius: tokens.borderRadius.full,
    fontWeight: tokens.typography.weights.medium,
    fontSize: '0.95rem',
    px: 0.1,
    py: 0.3,
    minWidth: 0,
    transition: 'background 0.2s, color 0.2s, border 0.1s, padding 0.2s cubic-bezier(.4,1.3,.6,1)',
    userSelect: 'none',
    borderWidth: 1,
    borderStyle: 'solid',
    position: 'relative',
    '&:focus': {
      boxShadow: 'none',
    },
  }

  if (selected) {
    return {
      ...base,
      backgroundColor: `${selectedBg} !important`,
      color: theme.palette.getContrastText(selectedBg),
      borderColor: selectedBg,
      boxShadow: 'none',
      ...selectedHoverStyles,
    }
  }

  if (context !== 'static') {
    return {
      ...base,
      backgroundColor: theme.palette.background.paper,
      color: theme.palette.text.primary,
      borderColor: selectedBg,
      ...unselectedHoverStyles,
    }
  }

  return {
    ...base,
    backgroundColor: theme.palette.background.paper,
    color: theme.palette.text.primary,
    borderColor: theme.palette.text.primary,
    ...unselectedHoverStyles,
  }
}
