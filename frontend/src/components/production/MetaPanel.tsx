import { useTheme } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { formatDate } from '../../utils/dateUtils'
import { getHallDisplayName } from '../../utils/hall'
import { getLocalizedValue } from '../../utils/localization'
import GenreAndTagChip from '../GenreAndTagChip'

import type { CSSProperties } from 'react'
import { Production } from '../../types/Productions'
import type {
  ChipLabels,
  GenreAndTagChipContext,
  GenreAndTagChipId,
  GenreAndTagChipType,
} from '../../types/GenreAndTagChip'

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
  const list = (events || []).filter((e) => !!e.starts_at)

  if (!list.length) return ''

  const dates = list.map((e) => new Date(e.starts_at as string).getTime()).sort((a, b) => a - b)
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
    ...new Set(list.map((e) => getHallDisplayName(e, lang) || e.hall_display).filter(Boolean)),
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
 * Build a list of translated tag objects from production data.
 *
 * A production can have:
 * - explicit tags (`production.tags`)
 * - type (`production.uit_database_type`) as one pseudo-tag
 * - genres (`production.genres`)
 *
 * The output order preserves semantic priority: explicit tags first, then type, then genres.
 */
function formatAllTags(production: Production, lang: string): ResolvedTag[] {
  const genreTags = (production.genres || [])
    .map((g) => ({
      tagName: g.display_name || getLocalizedValue(g.name || {}, lang),
      labels: g.name || {},
      chipType: 'genre' as const,
      value: g.id,
      context: 'description' as const,
    }))
    .filter((tag) => tag.tagName)

  const explicitTags = (production.tags || [])
    .map((t) => ({
      tagName:
        t.display_name ||
        getLocalizedValue(t.name || {}, lang) ||
        getLocalizedValue(t.url_title || {}, lang) ||
        t.type ||
        '',
      labels: t.name || t.url_title || {},
      chipType: 'seriesTag' as const,
      value: t.id,
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
  style?: CSSProperties
}

function MetaRow({ label, value }: { label: string; value: string }) {
  const theme = useTheme()
  if (!value) return null
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '140px 1fr',
        gap: '8px',
        padding: '14px 0',
        borderBottom: `1px solid ${theme.palette.divider}`,
        alignItems: 'start',
      }}
    >
      <span
        style={{
          color: theme.palette.text.secondary,
          fontSize: '0.95rem',
          paddingTop: '2px',
          fontWeight: 600,
        }}
      >
        {label}
      </span>
      <span style={{ fontSize: '0.92rem', color: theme.palette.text.primary, fontWeight: 500 }}>
        {value}
      </span>
    </div>
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
 * - genres/type/etc. are derived and displayed in MetaRow
 * - tags are normalized via formatAllTags and rendered as Tag chips
 */
export default function MetaPanel({ production, language = 'nl', style }: MetaPanelProps) {
  const theme = useTheme()
  const { t } = useTranslation()

  const resolvedTitle =
    getLocalizedValue(production.title, language) || production.display_title || ''

  const resolvedTagline = getLocalizedValue(production.tagline, language)

  const resolvedArtistName =
    getLocalizedValue(production.artist_name, language) || production.display_artist_name || ''

  const resolvedDateRange = getDateRange(production.events, language)
  const resolvedVenues = getUniqueVenues(production.events, language)

  const resolvedGenres = (production.genres || [])
    .map((g) => getLocalizedValue(g.name || {}, language) || g.display_name || '')
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
    <div
      className="meta-panel"
      style={{
        paddingTop: '32px',
        background: theme.palette.background.paper,
        color: theme.palette.text.primary,
        ...style,
      }}
    >
      <h1
        style={{
          fontSize: '2rem',
          fontWeight: 700,
          lineHeight: 1.15,
          margin: '0 0 8px',
          letterSpacing: '-0.02em',
        }}
      >
        {resolvedTitle}
      </h1>

      {(resolvedTagline || resolvedArtistName) && (
        <p
          style={{
            fontSize: '0.95rem',
            color: theme.palette.text.secondary,
            margin: '0 0 24px',
            fontStyle: 'italic',
          }}
        >
          {resolvedTagline || resolvedArtistName}
        </p>
      )}

      <div style={{ borderTop: '1px solid #ebebeb', marginBottom: '4px' }} />

      <div style={{ fontFamily: "'Helvetica Neue', Arial, sans-serif" }}>
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
      </div>

      {resolvedTags.length > 0 && (
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '8px',
            marginTop: '28px',
          }}
        >
          {resolvedTags.map((tag, i) => (
            <GenreAndTagChip
              key={`${tag.tagName}-${i}`}
              name={tag.tagName}
              labels={tag.labels}
              chipType={tag.chipType}
              id={tag.value}
              context={tag.context}
            />
          ))}
        </div>
      )}
    </div>
  )
}
