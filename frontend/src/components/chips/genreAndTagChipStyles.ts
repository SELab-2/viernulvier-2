import type { SxProps, Theme } from '@mui/material'

/**
 * Input for `getGenreAndTagChipStyles`.
 */
type GetGenreAndTagChipStylesInput = {
  theme: Theme
  selected: boolean
  context: 'search' | 'description' | 'series' | 'static'
  chipType: 'genre' | 'seriesTag'
}

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
  const seriesMain = theme.palette.primary.main
  const seriesHover = theme.palette.primary.dark
  const selectedBg = chipType === 'genre' ? accentMain : seriesMain
  const selectedHoverBg = chipType === 'genre' ? accentHover : seriesHover
  const selectedHoverStyles =
    context === 'search'
      ? {
          '&:hover': {
            backgroundColor: `${selectedHoverBg} !important`,
            color: theme.palette.getContrastText(selectedHoverBg),
            borderColor: selectedBg,
          },
        }
      : {}
  const unselectedHoverStyles =
    context === 'search'
      ? {
          '&:hover': {
            backgroundColor: selectedBg,
            color: theme.palette.getContrastText(selectedBg),
            borderColor: selectedBg,
          },
        }
      : {}

  const base: SxProps<Theme> = {
    borderRadius: '9999px',
    fontWeight: 500,
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

  if (context === 'series' || selected) {
    return {
      ...base,
      backgroundColor: `${selectedBg} !important`,
      color: theme.palette.getContrastText(selectedBg),
      borderColor: selectedBg,
      boxShadow: 'none',
      ...selectedHoverStyles,
    }
  }

  if (theme.palette.mode === 'light') {
    return {
      ...base,
      backgroundColor: theme.palette.background.paper,
      color: theme.palette.text.primary,
      borderColor: theme.palette.text.primary,
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
