import ArrowForwardOutlinedIcon from '@mui/icons-material/ArrowForwardOutlined'
import DateRangeOutlinedIcon from '@mui/icons-material/DateRangeOutlined'
import { Box, Stack, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Link as RouterLink } from 'react-router-dom'

import { formatDate } from '../../utils/dateUtils'
import { getTranslatedRecord } from '../../utils/translations'
import HtmlText from '../HtmlText'
import ImageWithFallback from '../ImageWithFallback'
import { sanitizeHtml, forbidImagesRule, forbidEmbedsRule } from '../../utils/SanitizeHtml'

import type { Series } from '../../types/Series'

export interface SeriesListCardProps {
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

const SeriesListCard = ({ series }: SeriesListCardProps) => {
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
    // Render the series as a full-card link.
    <Stack
      component={RouterLink}
      to={`/series/${series.tag.id}`}
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
      <ImageWithFallback
        src={series.lastProductionImage}
        alt={title}
        height="100%"
        sx={{ aspectRatio: 16 / 9, borderRadius: '4px' }}
      />

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
            <HtmlText
              html={sanitizeHtml(description, [forbidImagesRule, forbidEmbedsRule])}
              variant="body2"
              component="div"
              sx={{
                fontSize: 'inherit',
                color: 'text.secondary',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            />
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

      {/* Arrow affordance for the detail link. */}
      <Box sx={{ alignSelf: 'center', pr: 2 }}>
        <ArrowForwardOutlinedIcon color="action" />
      </Box>
    </Stack>
  )
}

export default SeriesListCard
