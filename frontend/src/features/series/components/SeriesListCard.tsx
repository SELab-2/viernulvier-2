/*
 * Displays a clickable list-card for a single series (Tag entity).
 *
 * Responsibilities:
 * - Renders localized series title + excerpt
 * - Displays optional date range (first -> last production)
 * - Provides navigation to the series detail page
 * - Uses full-card clickable layout via React Router link
 *
 * Notes:
 * - All localization is derived from i18n + resolved language
 * - HTML excerpts are sanitized and converted to plain text
 * - Layout is optimized for horizontal list views
 */

import ArrowForwardOutlinedIcon from '@mui/icons-material/ArrowForwardOutlined'
import DateRangeOutlinedIcon from '@mui/icons-material/DateRangeOutlined'
import { Box, Stack, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Link as RouterLink, useLocation } from 'react-router-dom'

import ImageWithFallback from '../../../shared/components/ImageWithFallback'
import { formatDate } from '../../../utils/dateUtils'
import { resolveCurrentLanguage, toLocalizedPath } from '../../../utils/localizedRoutes'
import { htmlToPlainText } from '../../../utils/SanitizeHtml'
import { getLocalizedTagName, getLocalizedTagExcerpt } from '../../../utils/translations'

import type { SeriesCardProps } from '../../../types/SeriesCardProps'

const SeriesListCard = ({ tag }: SeriesCardProps) => {
  const { i18n, t } = useTranslation()
  const location = useLocation()
  const { language } = i18n

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
   * Builds a compact human-readable date range label.
   * Falls back gracefully when only one endpoint exists.
   */
  const dateLabel =
    startLabel && endLabel
      ? startLabel === endLabel
        ? startLabel
        : `${startLabel} - ${endLabel}`
      : startLabel || endLabel

  return (
    // Entire card acts as navigation link to series detail page.
    <Stack
      component={RouterLink}
      to={detailPath}
      direction="row"
      sx={(theme) => ({
        gap: 3,
        height: 170,
        p: 3,
        borderRadius: '4px',
        overflow: 'hidden',
        backgroundColor: theme.palette.background.paper,
        border: `1px solid ${theme.palette.divider}`,
        textDecoration: 'none',
        transition: 'box-shadow 0.2s ease',
        '&:hover': {
          boxShadow: theme.shadows[3],
        },
      })}
    >
      {/* Series thumbnail image */}
      <ImageWithFallback
        src={tag.image}
        alt={title}
        height="100%"
        sx={{ aspectRatio: 16 / 9, borderRadius: '4px' }}
      />

      {/* Main content block (title, excerpt, metadata) */}
      <Stack
        sx={{
          flex: 1,
          minWidth: 0,
          height: '100%',
          justifyContent: 'space-between',
          gap: 1,
          overflow: 'hidden',
        }}
      >
        <Stack>
          {/* Series title */}
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

      {/* Navigation affordance icon */}
      <Box sx={{ alignSelf: 'center', pr: 2 }}>
        <ArrowForwardOutlinedIcon color="action" />
      </Box>
    </Stack>
  )
}

export default SeriesListCard
