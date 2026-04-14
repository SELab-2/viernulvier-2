import { Box, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'

import { tokens } from '../../theme/tokens'
import { formatDate } from '../../utils/dateUtils'
import { getHallDisplayName } from '../../utils/hall'
import { getLocalizedValue } from '../../utils/localization'
import GenreAndTagChip from '../chips/GenreAndTagChip'

import type {
  ChipLabels,
  GenreAndTagChipContext,
  GenreAndTagChipId,
  GenreAndTagChipType,
} from '../../types/GenreAndTagChip'
import type { Production } from '../../types/Productions'
import type { SxProps, Theme } from '@mui/material/styles'

function getDateRange(events: Production['events'] | null | undefined, lang: string): string {
  const list = (events || []).filter((event) => !!event.starts_at)

  if (!list.length) {
    return ''
  }

  const dates = list
    .map((event) => new Date(event.starts_at as string).getTime())
    .sort((a, b) => a - b)
  const first = new Date(dates[0])
  const last = new Date(dates[dates.length - 1])

  if (first.toDateString() === last.toDateString()) {
    return formatDate(list[0].starts_at, lang)
  }

  return `${formatDate(first.toISOString(), lang)} - ${formatDate(last.toISOString(), lang)}`
}

function getUniqueVenues(events: Production['events'] | null | undefined, lang: string): string {
  const list = events || []
  const venues = [
    ...new Set(
      list.map((event) => getHallDisplayName(event, lang) || event.hall_display).filter(Boolean),
    ),
  ] as string[]

  return venues.join(', ')
}

interface ResolvedTag {
  tagName: string
  labels: ChipLabels
  context: GenreAndTagChipContext
  chipType: GenreAndTagChipType
  value: GenreAndTagChipId
}

function formatAllTags(production: Production, lang: string): ResolvedTag[] {
  const genreTags = (production.genres || [])
    .map((genre) => ({
      tagName: genre.display_name || getLocalizedValue(genre.name || {}, lang),
      labels: genre.name || {},
      chipType: 'genre' as const,
      value: genre.id,
      context: 'description' as const,
    }))
    .filter((tag) => tag.tagName)

  const explicitTags = (production.tags || [])
    .map((tag) => ({
      tagName:
        tag.display_name ||
        getLocalizedValue(tag.name || {}, lang) ||
        getLocalizedValue(tag.url_title || {}, lang) ||
        tag.type ||
        '',
      labels: tag.name || tag.url_title || {},
      chipType: 'seriesTag' as const,
      value: tag.id,
      context: 'series' as const,
    }))
    .filter((tag) => tag.tagName)

  const typeTag = production.uit_database_type?.name
    ? [
        {
          tagName: production.uit_database_type.name,
          labels: {},
          chipType: 'genre' as const,
          value: production.uit_database_type.name,
          context: 'description' as const,
        },
      ]
    : []

  return [...explicitTags, ...typeTag, ...genreTags]
}

interface MetaPanelProps {
  production: Production
  language?: string
  sx?: SxProps<Theme>
}

function MetaRow({ label, value }: { label: string; value: string }) {
  if (!value) {
    return null
  }

  return (
    <Box
      sx={(theme) => ({
        display: 'grid',
        gridTemplateColumns: '140px 1fr',
        gap: tokens.spacing.numericSm,
        py: 1.75,
        borderBottom: `1px solid ${theme.palette.divider}`,
        alignItems: 'start',
      })}
    >
      <Typography
        component="span"
        sx={{
          color: 'text.secondary',
          fontSize: tokens.typography.sizes.sm,
          pt: 0.25,
          fontWeight: tokens.typography.weights.bold,
        }}
      >
        {label}
      </Typography>
      <Typography
        component="span"
        sx={{
          fontSize: '0.92rem',
          color: 'text.primary',
          fontWeight: tokens.typography.weights.medium,
        }}
      >
        {value}
      </Typography>
    </Box>
  )
}

export default function MetaPanel({ production, language = 'nl', sx }: MetaPanelProps) {
  const { t } = useTranslation()

  const resolvedTitle =
    getLocalizedValue(production.title, language) || production.display_title || ''
  const resolvedTagline = getLocalizedValue(production.tagline, language)
  const resolvedArtistName =
    getLocalizedValue(production.artist_name, language) || production.display_artist_name || ''

  const resolvedDateRange = getDateRange(production.events, language)
  const resolvedVenues = getUniqueVenues(production.events, language)

  const resolvedGenres = (production.genres || [])
    .map((genre) => getLocalizedValue(genre.name || {}, language) || genre.display_name || '')
    .filter(Boolean)
    .join(', ')

  const resolvedTypeName = production.uit_database_type?.name || ''
  const capitalizedResolvedTypeName = resolvedTypeName
    ? resolvedTypeName[0].toUpperCase() + resolvedTypeName.slice(1)
    : ''

  const resolvedPerformerType = production.performer_type || ''
  const resolvedAttendanceMode = production.attendance_mode || ''
  const resolvedTags = formatAllTags(production, language)

  return (
    <Box
      className="meta-panel"
      sx={[
        (theme) => ({
          pt: 4,
          background: theme.palette.background.default,
          color: theme.palette.text.primary,
        }),
        ...(Array.isArray(sx) ? sx : sx ? [sx] : []),
      ]}
    >
      <Typography
        component="h1"
        sx={{
          fontSize: tokens.typography.sizes['3xl'],
          fontWeight: tokens.typography.weights.bold,
          lineHeight: 1.15,
          mb: 1,
          letterSpacing: '-0.02em',
        }}
      >
        {resolvedTitle}
      </Typography>

      {(resolvedTagline || resolvedArtistName) && (
        <Typography
          component="p"
          sx={{
            fontSize: tokens.typography.sizes.sm,
            color: 'text.secondary',
            mb: 3,
            fontStyle: 'italic',
          }}
        >
          {resolvedTagline || resolvedArtistName}
        </Typography>
      )}

      <Box sx={(theme) => ({ borderTop: `1px solid ${theme.palette.divider}`, mb: 0.5 })} />

      <Box sx={{ fontFamily: tokens.typography.fontFamily }}>
        {resolvedDateRange && (
          <MetaRow
            label={t('productions.detail.meta.period', 'Periode')}
            value={resolvedDateRange}
          />
        )}
        {resolvedVenues && (
          <MetaRow label={t('productions.detail.meta.venues', 'Locaties')} value={resolvedVenues} />
        )}
        {resolvedGenres && (
          <MetaRow label={t('productions.detail.meta.genre', 'Genre')} value={resolvedGenres} />
        )}
        {capitalizedResolvedTypeName && (
          <MetaRow
            label={t('productions.detail.meta.type', 'Type')}
            value={capitalizedResolvedTypeName}
          />
        )}
        <MetaRow
          label={t('productions.detail.meta.performerType', 'Uitvoering')}
          value={
            resolvedPerformerType === 'group'
              ? t('productions.detail.meta.group', 'Groep')
              : resolvedPerformerType === 'solo'
                ? t('productions.detail.meta.solo', 'Solo')
                : ''
          }
        />
        <MetaRow
          label={t('productions.detail.meta.attendance', 'Aanwezigheid')}
          value={
            resolvedAttendanceMode === 'offline'
              ? t('productions.detail.meta.offline', 'Fysiek')
              : resolvedAttendanceMode === 'online'
                ? t('productions.detail.meta.online', 'Online')
                : ''
          }
        />
      </Box>

      {resolvedTags.length > 0 && (
        <Box
          sx={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: tokens.spacing.numericSm,
            mt: 3.5,
          }}
        >
          {resolvedTags.map((tag, index) => (
            <GenreAndTagChip
              key={`${tag.tagName}-${index}`}
              name={tag.tagName}
              labels={tag.labels}
              chipType={tag.chipType}
              id={tag.value}
              context={tag.context}
            />
          ))}
        </Box>
      )}
    </Box>
  )
}
