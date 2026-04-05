import CloseIcon from '@mui/icons-material/Close'
import { Chip, useTheme } from '@mui/material'
import { useState } from 'react'
import type { MouseEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import type { GenreAndTagChipProps } from '../types/GenreAndTagChip'
import { getGenreAndTagChipStyles } from './chips/genreAndTagChipStyles'
import { getQueryKeyForChipType, resolveChipLabel } from './chips/genreAndTagChipUtils'

/**
 * Generic chip component that supports both genre and series-tag scenarios.
 *
 * Context behavior:
 * - `search`: toggles the selected value via `onToggle`
 * - `description`: routes to homepage with the chip value in URL query
 * - `series`: routes to the series detail page `/series/:id`
 * - `static`: visual-only non-clickable chip
 */
/**
 * Unified chip that replaces separate tag and genre chips.
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
  const navigate = useNavigate()
  const { i18n, t } = useTranslation()
  const [hovered, setHovered] = useState(false)

  const label = resolveChipLabel({
    fallback: name,
    labels,
    language: i18n.language,
  })

  const isClickable = context !== 'static'
  const showSelectedIcon = context === 'search' && selected
  const selectedChipColor =
    chipType === 'genre' ? (theme.palette.accent?.main ?? '#9333ea') : theme.palette.primary.main
  const iconHoverBackground = '#fff'

  const resolvedAriaLabel =
    ariaLabel ??
    (context === 'search' && chipType === 'genre'
      ? t('genreChip.filterByGenre', { genre: label })
      : undefined)

  /** Handles click behavior based on the selected context. */
  const handleClick = (event: MouseEvent) => {
    event.stopPropagation()

    if (!isClickable) {
      return
    }

    if (context === 'series') {
      navigate(`/series/${name}`)
      return
    }

    if (context === 'search') {
      onToggle?.(id, chipType)
      return
    }

    if (context === 'description') {
      const queryKey = getQueryKeyForChipType(chipType)
      navigate(`/?${queryKey}=${encodeURIComponent(String(id))}`)
    }
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
                color: hovered ? selectedChipColor : '#fff',
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
      onClick={handleClick}
      sx={getGenreAndTagChipStyles({ theme, selected, context, chipType })}
      aria-pressed={context === 'search' ? selected : undefined}
      aria-label={resolvedAriaLabel}
      tabIndex={isClickable ? 0 : -1}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    />
  )
}

export default GenreAndTagChip
