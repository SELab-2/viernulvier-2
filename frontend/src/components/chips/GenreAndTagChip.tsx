import CloseIcon from '@mui/icons-material/Close'
import { Box, Chip, useTheme } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Link as RouterLink } from 'react-router-dom'

import { getTranslatedRecord } from '../../utils/translations'
import { getGenreAndTagChipStyles } from './genreAndTagChipStyles'
import { getQueryKeyForChipType } from './genreAndTagChipUtils'

import type { MouseEvent } from 'react'
import type { GenreAndTagChipProps } from '../../types/GenreAndTagChip'

/**
 * Generic chip component that supports both genre and series-tag scenarios.
 *
 * Context behavior:
 * - `search`: toggles the selected value via `onToggle`
 * - `description`: routes to homepage with the chip value in URL query
 * - `series`: routes to the series detail page `/series/:id`
 * - `static`: visual-only non-clickable chip
 *
 * Chip label resolution priority:
 * 1. The translated value from `labels` based on the active locale
 * 2. The raw `name` as a fallback
 *
 * The selected state and click behavior are only relevant in the 'search' context,
 * where chips act as filters.
 * In 'description' and 'series' contexts, chips function as navigation links.
 * The 'static' context renders a non-interactive chip for display purposes.
 */
const GenreAndTagChip = ({
  name,
  labels,
  selected = false,
  id,
  chipType = 'genre',
  context = 'static',
  onToggle,
  ariaLabel,
}: GenreAndTagChipProps) => {
  const theme = useTheme()
  const { i18n, t } = useTranslation()

  const label = getTranslatedRecord(labels, i18n.language, name)

  const isClickable = context !== 'static'
  const isSearchContext = context === 'search'
  const linkTo =
    context === 'series'
      ? `/series/${String(id)}`
      : context === 'description'
        ? `/archive?${getQueryKeyForChipType(chipType)}=${encodeURIComponent(String(id))}`
        : undefined
  const showSelectedIcon = context === 'search' && selected

  const resolvedAriaLabel =
    ariaLabel ??
    (context === 'search' && chipType === 'genre'
      ? t('genreChip.filterByGenre', { genre: label })
      : undefined)

  /** Handles click behavior for search context */
  const handleSearchClick = (event: MouseEvent) => {
    event.stopPropagation()
    onToggle?.(id, chipType)
  }

  return (
    <Chip
      label={
        <Box
          component="span"
          sx={{
            display: 'flex',
            alignItems: 'center',
            minWidth: 0,
            gap: showSelectedIcon ? 0.75 : 0,
            transition: 'gap 0.2s cubic-bezier(.4,1.3,.6,1), width 0.2s cubic-bezier(.4,1.3,.6,1)',
          }}
        >
          <Box
            component="span"
            sx={{
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              minWidth: 0,
              transition: 'color 0.2s',
            }}
          >
            {label}
          </Box>

          {showSelectedIcon ? (
            <Box
              component="span"
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                lineHeight: 0,
              }}
            >
              <CloseIcon sx={{ fontSize: 18 }} />
            </Box>
          ) : null}
        </Box>
      }
      clickable={isClickable}
      onClick={isSearchContext ? handleSearchClick : undefined}
      sx={getGenreAndTagChipStyles({ theme, selected, context, chipType })}
      aria-pressed={context === 'search' ? selected : undefined}
      aria-label={resolvedAriaLabel}
      tabIndex={isClickable ? 0 : -1}
      {...(linkTo ? { component: RouterLink, to: linkTo } : { component: 'div' })}
    />
  )
}

export default GenreAndTagChip
