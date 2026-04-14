import ArrowForwardOutlinedIcon from '@mui/icons-material/ArrowForwardOutlined'
import DateRangeOutlinedIcon from '@mui/icons-material/DateRangeOutlined'
import { Box, Stack, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Link as RouterLink } from 'react-router-dom'
import type { Series } from '../../types/Series'
import { formatDate } from '../../utils/dateUtils'
import { getTranslatedRecord } from '../../utils/translations'
import ImageWithFallback from '../ImageWithFallback'

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
  const language = i18n.language

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
      gap={3}
      height={170}
      padding={3}
      borderRadius="4px"
      overflow="hidden"
      sx={(theme) => ({
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
        borderRadius="4px"
        sx={{ aspectRatio: 16 / 9 }}
      />

      <Stack
        flex={1}
        minWidth={0}
        height="100%"
        justifyContent="space-between"
        gap={1}
        overflow="hidden"
      >
        <Stack>
          <Typography component="h2" variant="h6" color="textPrimary" fontWeight="bold" noWrap>
            {title}
          </Typography>

          {description ? (
            <Typography component="p" color="textSecondary" noWrap>
              {description}
            </Typography>
          ) : null}
        </Stack>

        {dateLabel ? (
          <Stack direction="row" alignItems="center" spacing={1} color="text.secondary">
            <DateRangeOutlinedIcon fontSize="inherit" />
            <Typography variant="body2" noWrap>
              {dateLabel}
            </Typography>
          </Stack>
        ) : null}
      </Stack>

      {/* Arrow affordance for the detail link. */}
      <Box alignSelf="center" paddingRight={2}>
        <ArrowForwardOutlinedIcon color="action" />
      </Box>
    </Stack>
  )
}

export default SeriesListCard
