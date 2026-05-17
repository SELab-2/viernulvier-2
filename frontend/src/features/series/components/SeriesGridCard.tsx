/*
 * Displays a compact grid card for a series.
 */

import DateRangeOutlinedIcon from '@mui/icons-material/DateRangeOutlined'
import { Stack, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Link as RouterLink, useLocation } from 'react-router-dom'

import ImageWithFallback from '../../../shared/components/ImageWithFallback'
import { tokens } from '../../../theme/tokens'
import { formatDate } from '../../../utils/dateUtils'
import { resolveCurrentLanguage, toLocalizedPath } from '../../../utils/localizedRoutes'
import { htmlToPlainText } from '../../../utils/SanitizeHtml'
import { getTranslatedRecord } from '../../../utils/translations'

import type { Tag } from '../../../types/Tags'

export interface SeriesGridCardProps {
  tag: Tag
}

/**
 * Returns the localized name for a tag based on current UI language.
 * Falls back to default display values if translation is missing.
 */
const getLocalizedTagName = (tag: Tag, language: string): string => {
  const normalizedLanguage = language.startsWith('en') ? 'en' : 'nl'
  return getTranslatedRecord(tag.name, normalizedLanguage, tag.display_name)
}

/**
 * Returns the localized excerpt for a tag based on current UI language.
 * Used for short preview text in card layouts.
 */
const getLocalizedTagExcerpt = (tag: Tag, language: string): string => {
  // const normalizedLanguage = language.startsWith('en') ? 'en' : 'nl'
  return getTranslatedRecord(tag.excerpt, language, tag.display_excerpt)
}

const SeriesGridCard = ({ tag }: SeriesGridCardProps) => {
  const { i18n, t } = useTranslation()
  const location = useLocation()
  const { language } = i18n

  // Resolve locale-aware routing path for the current series detail page
  const currentLanguage = resolveCurrentLanguage(
    location.pathname,
    i18n.language,
    i18n.resolvedLanguage,
  )
  const detailPath = toLocalizedPath(`/series/${tag.id}`, currentLanguage)

  const title = getLocalizedTagName(tag, language) || t('series.untitled')
  const excerpt = htmlToPlainText(getLocalizedTagExcerpt(tag, language))
  const startLabel = formatDate(tag.first_production_start, language)
  const endLabel = formatDate(tag.last_production_end, language)

  /**
   * Build a compact date label:
   * - single date if equal
   * - range if both exist
   * - fallback to whichever is available
   */
  const dateLabel =
    startLabel && endLabel
      ? startLabel === endLabel
        ? startLabel
        : `${startLabel} - ${endLabel}`
      : startLabel || endLabel

  return (
    // Entire card acts as a navigation link to the series detail page
    <Stack
      component={RouterLink}
      to={detailPath}
      sx={(theme) => ({
        width: '100%',
        maxWidth: tokens.card.gridCardWidthPx,
        borderRadius: 4,
        overflow: 'hidden',
        textDecoration: 'none',
        border: `1px solid ${theme.palette.divider}`,
        backgroundColor: theme.palette.background.paper,
        transition: 'box-shadow 0.2s ease',
        '&:hover': {
          boxShadow: theme.shadows[3],
        },
      })}
    >
      {/* Series image preview */}
      <ImageWithFallback src={tag.image} alt={title} sx={{ aspectRatio: 16 / 9 }} />

      {/* Card content section */}
      <Stack sx={{ flex: 1, justifyContent: 'space-between', gap: 1, p: 3 }}>
        <Stack>
          {/* Title */}
          <Typography
            component="h2"
            variant="h6"
            color="textPrimary"
            noWrap
            sx={{ fontWeight: 'bold' }}
          >
            {title}
          </Typography>

          <Typography
            component="div"
            variant="body2"
            sx={{
              fontSize: 'inherit',
              color: 'text.secondary',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {excerpt || t('blogs.home.noExcerpt')}
          </Typography>
        </Stack>

        {/* Date range indicator */}
        {dateLabel ? (
          <Stack direction="row" spacing={1} sx={{ alignItems: 'center', color: 'text.secondary' }}>
            <DateRangeOutlinedIcon fontSize="inherit" />
            <Typography variant="body2" noWrap>
              {dateLabel}
            </Typography>
          </Stack>
        ) : null}
      </Stack>
    </Stack>
  )
}

export default SeriesGridCard
