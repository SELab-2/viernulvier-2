import DateRangeOutlinedIcon from '@mui/icons-material/DateRangeOutlined'
import { Stack, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Link as RouterLink } from 'react-router-dom'

import { tokens } from '../../theme/tokens'
import { formatDate } from '../../utils/dateUtils'
import { getTranslatedRecord } from '../../utils/translations'
import ImageWithFallback from '../ImageWithFallback'

import type { Series } from '../../types/Series'

export interface SeriesGridCardProps {
  series: Series
}

// Function to get the localized series name based on the current language.
const getLocalizedSeriesName = (series: Series, language: string): string => {
  const normalizedLanguage = language.startsWith('en') ? 'en' : 'nl'
  return getTranslatedRecord(series.tag.name, normalizedLanguage, series.tag.display_name)
}

// Function to get the localized series description based on the current language.
const getLocalizedSeriesDescription = (series: Series, language: string): string => {
  const normalizedLanguage = language.startsWith('en') ? 'en' : 'nl'
  return getTranslatedRecord(
    series.tag.short_description,
    normalizedLanguage,
    series.tag.display_short_description,
  )
}

const SeriesGridCard = ({ series }: SeriesGridCardProps) => {
  const { i18n } = useTranslation()
  const { language } = i18n

  const title = getLocalizedSeriesName(series, language)
  const description = getLocalizedSeriesDescription(series, language)
  const startLabel = formatDate(series.firstProductionStart, language)
  const endLabel = formatDate(series.lastProductionEnd, language)

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
      to={`/series/${series.tag.id}`}
      sx={(theme) => ({
        width: tokens.card.gridCardWidthPx,
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
      <ImageWithFallback
        src={series.lastProductionImage}
        alt={title}
        sx={{ aspectRatio: 16 / 9 }}
      />

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

          {description ? (
            <Typography component="p" color="textSecondary" noWrap>
              {description}
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
