import DateRangeOutlinedIcon from '@mui/icons-material/DateRangeOutlined'
import { Stack, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Link as RouterLink, useLocation } from 'react-router-dom'

import { tokens } from '../../theme/tokens'
import { formatDate } from '../../utils/dateUtils'
import { resolveCurrentLanguage, toLocalizedPath } from '../../utils/localizedRoutes'
import { getTranslatedRecord } from '../../utils/translations'
import ImageWithFallback from '../ImageWithFallback'

import type { Tag } from '../../types/Tags'

export interface SeriesGridCardProps {
  tag: Tag
}

// TODO: use the function in utils for this once the PR implementing it has been merged
const htmlToPlainText = (html: string): string => html.replace(/<[^>]*>/g, '').trim()

// Function to get the localized tag name based on the current language.
const getLocalizedTagName = (tag: Tag, language: string): string => {
  const normalizedLanguage = language.startsWith('en') ? 'en' : 'nl'
  return getTranslatedRecord(tag.name, normalizedLanguage, tag.display_name)
}

// Function to get the localized tag excerpt based on the current language.
const getLocalizedTagExcerpt = (tag: Tag, language: string): string => {
  const normalizedLanguage = language.startsWith('en') ? 'en' : 'nl'
  return getTranslatedRecord(tag.excerpt, normalizedLanguage, tag.display_excerpt)
}

const SeriesGridCard = ({ tag }: SeriesGridCardProps) => {
  const { i18n } = useTranslation()
  const location = useLocation()
  const { language } = i18n
  const currentLanguage = resolveCurrentLanguage(
    location.pathname,
    i18n.language,
    i18n.resolvedLanguage,
  )
  const detailPath = toLocalizedPath(`/series/${tag.id}`, currentLanguage)

  const title = getLocalizedTagName(tag, language)
  const excerpt = getLocalizedTagExcerpt(tag, language)
  const startLabel = formatDate(tag.first_production_start, language)
  const endLabel = formatDate(tag.last_production_end, language)

  // Keep the date label compact when both endpoints are available.
  const dateLabel =
    startLabel && endLabel
      ? startLabel === endLabel
        ? startLabel
        : `${startLabel} - ${endLabel}`
      : startLabel || endLabel

  return (
    // Render the series as a compact card-sized link.
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
      <ImageWithFallback src={tag.image} alt={title} sx={{ aspectRatio: 16 / 9 }} />

      <Stack sx={{ flex: 1, justifyContent: 'space-between', gap: 1, p: 3 }}>
        <Stack>
          <Typography
            component="h2"
            variant="h6"
            color="textPrimary"
            noWrap
            sx={{ fontWeight: 'bold' }}
          >
            {title}
          </Typography>

          {excerpt ? (
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
              {htmlToPlainText(excerpt)}
            </Typography>
          ) : null}
        </Stack>

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
