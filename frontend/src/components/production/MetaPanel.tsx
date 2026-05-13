import { Box, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'
import type { ReactNode } from 'react'

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

/**
 * Format an event list into a human-readable date range for production metadata.
 *
 * Rules:
 * - empty event array => ''
 * - single-day events (same date) => one formatted date
 * - multi-day events => first date - last date
 *
 * `formatDate` is locale-aware.
 */
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

/**
 * Aggregate unique venue names from all events.
 * This avoids repeated venue descriptions by using a set.
 * Note: event.hall_display is expected to be a fallback provided by the API.
 */
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
  /**
   * The canonical tag value used for internal ID and tag link generation.
   */
  tagName: string
  /**
   * Optional localized labels by language code, e.g. { nl: 'Drama', en: 'Drama' }.
   */
  labels: ChipLabels
  context: GenreAndTagChipContext
  chipType: GenreAndTagChipType
  value: GenreAndTagChipId
}

/**
 * Build a list of translated genre objects from production data.
 *
 * Genres are shown as a chip list in the metadata panel.
 */
function formatGenreTags(production: Production, lang: string): ResolvedTag[] {
  return (production.genres || [])
    .map((genre) => ({
      tagName: genre.display_name || getLocalizedValue(genre.name || {}, lang),
      labels: genre.name || {},
      chipType: 'genre' as const,
      value: genre.id,
      context: 'description' as const,
    }))
    .filter((tag) => tag.tagName)
}

/**
 * Build a list of translated series/tag objects from production data.
 *
 * These are rendered separately from genres to make the metadata easier to scan.
 */
function formatSeriesTags(production: Production, lang: string): ResolvedTag[] {
  return (production.tags || [])
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
}

function renderTagList(tags: ResolvedTag[]) {
  if (!tags.length) {
    return ''
  }

  return (
    <Box
      sx={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: tokens.spacing.numericSm,
        alignItems: 'center',
      }}
    >
      {tags.map((tag, index) => (
        /* TODO: fix this to use the tag correctly instead of just the name */
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
  )
}

interface MetaPanelProps {
  production: Production
  language?: string
  sx?: SxProps<Theme>
  showHeader?: boolean
}

function MetaRow({ label, value }: { label: string; value: ReactNode }) {
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
          minWidth: 0,
        }}
      >
        {value}
      </Typography>
    </Box>
  )
}

/**
 * MetaPanel renders production metadata in the right-side details panel.
 *
 * Props:
 * - production: full production object from API response
 * - language: current UI language (defaults to 'nl')
 * - style: optional container style overrides
 *
 * Data derivation by component:
 * - title, tagline, artistName are localized from production fields
 * - date range + venues come from production.events
 * - genres and series are rendered as chip rows inside the metadata grid
 */
export default function MetaPanel({
  production,
  language = 'nl',
  sx,
  showHeader = true,
}: MetaPanelProps) {
  const { t } = useTranslation()

  const resolvedTitle =
    getLocalizedValue(production.title, language) || production.display_title || ''
  const resolvedArtistName =
    getLocalizedValue(production.artist_name, language) || production.display_artist_name || ''

  const resolvedDateRange = getDateRange(production.events, language)
  const resolvedVenues = getUniqueVenues(production.events, language)
  const genreTags = formatGenreTags(production, language)
  const seriesTags = formatSeriesTags(production, language)

  const resolvedTypeName = production.uit_database_type?.name || ''
  const capitalizedResolvedTypeName = resolvedTypeName
    ? resolvedTypeName[0].toUpperCase() + resolvedTypeName.slice(1)
    : ''

  const resolvedPerformerType = production.performer_type || ''
  const resolvedAttendanceMode = production.attendance_mode || ''

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
      {showHeader && (
        <>
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

          {resolvedArtistName && (
            <Typography
              component="h2"
              sx={{
                fontSize: tokens.typography.sizes.lg,
                fontWeight: tokens.typography.weights.medium,
                color: 'text.secondary',
                mb: 0.75,
              }}
            >
              {resolvedArtistName}
            </Typography>
          )}

          <Box sx={(theme) => ({ borderTop: `1px solid ${theme.palette.divider}`, mb: 0.5 })} />
        </>
      )}

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
        {genreTags.length > 0 && (
          <MetaRow
            label={t('productions.detail.meta.genres', 'Genres')}
            value={renderTagList(genreTags)}
          />
        )}
        {seriesTags.length > 0 && (
          <MetaRow
            label={t('productions.detail.meta.series', 'Reeksen')}
            value={renderTagList(seriesTags)}
          />
        )}
      </Box>
    </Box>
  )
}
