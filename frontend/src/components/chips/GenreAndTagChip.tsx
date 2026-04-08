import CloseIcon from '@mui/icons-material/Close'
import { Chip, useTheme } from '@mui/material'
import { useState } from 'react'
import type { MouseEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { Link as RouterLink } from 'react-router-dom'
import type { GenreAndTagChipProps } from '../../types/GenreAndTagChip'
import { tokens } from '../../theme/tokens'
import { getGenreAndTagChipStyles } from './genreAndTagChipStyles'
import { getQueryKeyForChipType } from './genreAndTagChipUtils'
import { getTranslatedRecord } from '../../utils/translations'

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
 * 1. `display_name` (if present)
 * 2. Localized `name` or `url_title` based on active i18n language
 * 3. Fallback to `type` for tags or empty string for genres
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
  const [hovered, setHovered] = useState(false)

  const label = getTranslatedRecord(labels, i18n.language, name)

  const isClickable = context !== 'static'
  const isSearchContext = context === 'search'
  const linkTo =
    context === 'series'
      ? `/series/${String(id)}`
      : context === 'description'
        ? `/?${getQueryKeyForChipType(chipType)}=${encodeURIComponent(String(id))}`
        : undefined
  const showSelectedIcon = context === 'search' && selected
  const selectedChipColor =
    chipType === 'genre'
      ? (theme.palette.accent?.main ?? tokens.colors.accent.main)
      : theme.palette.primary.main
  const iconHoverBackground = tokens.colors.neutral.white

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
        <span
          style={{
            display: 'flex',
            alignItems: 'center',
            minWidth: 0,
            gap: showSelectedIcon ? 6 : 0,
            transition: 'gap 0.2s cubic-bezier(.4,1.3,.6,1), width 0.2s cubic-bezier(.4,1.3,.6,1)',
          }}
        >
          <span
            style={{
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              transition: 'color 0.2s',
            }}
          >
            {label}
          </span>

          {showSelectedIcon ? (
            <span
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: 18,
                height: 18,
                borderRadius: '50%',
                background: hovered ? iconHoverBackground : 'transparent',
                color: hovered ? selectedChipColor : tokens.colors.neutral.white,
                boxShadow: hovered ? `0 0 0 2px ${iconHoverBackground}` : undefined,
                cursor: 'pointer',
                transition: 'background 0.15s, color 0.15s',
                flexShrink: 0,
                opacity: 1,
              }}
            >
              <CloseIcon fontSize="small" />
            </span>
          ) : null}
        </span>
      }
      clickable={isClickable}
      onClick={isSearchContext ? handleSearchClick : undefined}
      sx={getGenreAndTagChipStyles({ theme, selected, context, chipType })}
      aria-pressed={context === 'search' ? selected : undefined}
      aria-label={resolvedAriaLabel}
      tabIndex={isClickable ? 0 : -1}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      {...(linkTo ? { component: RouterLink, to: linkTo } : { component: 'div' })}
    />
  )
}

export default GenreAndTagChip
