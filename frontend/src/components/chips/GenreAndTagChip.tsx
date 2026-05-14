import CloseIcon from '@mui/icons-material/Close'
import { Box, Chip, useTheme } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Link as RouterLink, useLocation, useNavigate } from 'react-router-dom'

import { getGenreAndTagChipStyles } from './genreAndTagChipStyles'
import { getQueryKeyForChipType } from './genreAndTagChipUtils'
import { resolveCurrentLanguage, toLocalizedPath } from '../../utils/localizedRoutes'
import { getTranslatedRecord } from '../../utils/translations'

import type { GenreAndTagChipProps } from '../../types/GenreAndTagChip'
import type { MouseEvent } from 'react'

const readMultiParamValues = (searchParams: URLSearchParams, paramName: string): string[] => {
  const repeatedValues = searchParams.getAll(paramName)
  if (repeatedValues.length > 0) {
    return repeatedValues.flatMap((value) =>
      value
        .split('-')
        .map((part) => part.trim())
        .filter(Boolean),
    )
  }

  const serialized = searchParams.get(paramName)
  if (!serialized) {
    return []
  }

  return serialized
    .split('-')
    .map((part) => part.trim())
    .filter(Boolean)
}

/**
 * Generic chip component that supports both genre and series-tag scenarios.
 *
 * Context behavior:
 * - `search`: toggles the selected value via `onToggle`
 * - `description`: routes to the archive with the chip value in URL query
 * - `series`: routes to the series detail page `/series/:id`
 * - `static`: visual-only non-clickable chip
 *
 * When `disableLink` is set, the chip renders as a `div` and navigates programmatically,
 * which keeps it interactive without creating nested anchors inside card links.
 *
 * Chip label resolution priority:
 * 1. The translated value from `labels` based on the active locale
 * 2. The raw `name` as a fallback
 *
 * Search chips act as filters. Description and series chips act as navigation targets.
 * Static chips are rendered for display only.
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
  disableLink = false,
}: GenreAndTagChipProps) => {
  const theme = useTheme()
  const { i18n, t } = useTranslation()
  const location = useLocation()
  const navigate = useNavigate()

  const label = getTranslatedRecord(labels, i18n.language, name)
  const currentLanguage = resolveCurrentLanguage(
    location.pathname,
    i18n.language,
    i18n.resolvedLanguage,
  )

  const isClickable = context !== 'static'
  const isSearchContext = context === 'search'
  const linkTo =
    context === 'series'
      ? toLocalizedPath(`/series/${String(id)}`, currentLanguage)
      : context === 'description'
        ? (() => {
            const archivePath = toLocalizedPath('/archive', currentLanguage)
            const queryKey = getQueryKeyForChipType(chipType)

            if (disableLink && chipType === 'genre') {
              const searchParams = new URLSearchParams(location.search)
              const currentGenreIds = readMultiParamValues(searchParams, queryKey)
              const nextGenreIds = Array.from(new Set([...currentGenreIds, String(id)]))

              if (nextGenreIds.length > 0) {
                searchParams.set(queryKey, nextGenreIds.join('-'))
              }

              const nextSearch = searchParams.toString()
              return nextSearch ? `${archivePath}?${nextSearch}` : archivePath
            }

            return `${archivePath}?${queryKey}=${encodeURIComponent(String(id))}`
          })()
        : undefined
  const showSelectedIcon = context === 'search' && selected

  const resolvedAriaLabel =
    ariaLabel ??
    (context === 'search' && chipType === 'genre'
      ? t('genreChip.filterByGenre', { genre: label })
      : undefined)

  /** Handles filter toggles in search context. */
  const handleSearchClick = (event: MouseEvent) => {
    event.preventDefault()
    event.stopPropagation()
    onToggle?.(id, chipType)
  }

  const handleLinkClick = (event: MouseEvent) => {
    event.preventDefault()
    event.stopPropagation()
    if (disableLink && linkTo) {
      navigate(linkTo)
    }
  }

  const chipOnClick = isSearchContext
    ? handleSearchClick
    : disableLink && isClickable
      ? handleLinkClick
      : undefined

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
      onClick={chipOnClick}
      sx={getGenreAndTagChipStyles({ theme, selected, context, chipType })}
      aria-pressed={context === 'search' ? selected : undefined}
      aria-label={resolvedAriaLabel}
      tabIndex={isClickable ? 0 : -1}
      {...(linkTo
        ? disableLink
          ? { component: 'div', onClick: handleLinkClick }
          : { component: RouterLink, to: linkTo }
        : { component: 'div' })}
    />
  )
}

export default GenreAndTagChip
