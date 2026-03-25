import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import type { Production } from '../types/Productions'
import type { Event } from '../types/Events'
import type { Genre } from '../types/Genres'
import type { Tag as TagType } from '../types/Tags'
import Tag from '../components/Tag'
import LoadingSpinner from '../components/LoadingSpinner'
import { getProduction } from '../services/productions/Productions'
import sanitizeHtml from '../utils/SanitizeHtml'

// TODO: evenementen tonen
// TODO: media tonen
// TODO: check tags
// TODO: andere producties in reeks tonen
// TODO: gsm view

// ---- Helpers ----

/**
 * Select a localized value from a translation object.
 *
 * Preference order: current language -> Dutch -> English -> first available -> empty.
 *
 * @param obj Object with language keys, e.g. `{ nl: '...', en: '...' }`
 * @param lang Desired language code (default `nl`)
 * @returns Text in the best matching language or empty string
 */
function getLocalizedValue(obj: Record<string, string>, lang: string = 'nl'): string {
  return obj[lang] || obj['nl'] || obj['en'] || Object.values(obj)[0] || ''
}

/**
 * Format an ISO date string into a readable Belgian date.
 *
 * @param dateStr ISO date (e.g. `2026-03-25T20:00:00Z`) or `null`/`undefined`
 * @returns Formatted date (e.g. `25 March 2026`) or empty string
 */
function formatDate(dateStr?: string | null): string {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('nl-BE', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}

/**
 * Calculate a date range for a list of events.
 *
 * - Empty list -> empty string
 * - Single day -> that date
 * - Multiple days -> first to last date
 *
 * @param events List of events (can be `null` or `undefined`)
 * @returns Formatted date range or empty string
 */
function getDateRange(events?: Event[] | null): string {
  const list = (events || []).filter((e) => !!e.starts_at) as Event[]
  if (!list.length) return ''
  const dates = list.map((e) => new Date(e.starts_at as string).getTime()).sort((a, b) => a - b)
  const first = new Date(dates[0])
  const last = new Date(dates[dates.length - 1])
  if (first.toDateString() === last.toDateString()) return formatDate(list[0].starts_at)
  return `${formatDate(first.toString())} – ${formatDate(last.toString())}`
}

/**
 * Returns a unique comma-separated list of venues from event data.
 *
 * @param events List of events (can be `null` or `undefined`)
 * @returns Comma-separated unique venue names
 */
function getUniqueVenues(events?: Event[] | null): string {
  const list = events || []
  const venues = [...new Set(list.map((e) => e.hall_display).filter(Boolean))] as string[]
  return venues.join(', ')
}

/**
 * Helper function to get the most suitable image URL for the production details page.
 * Looks for a media item of type 'foto', tries crops in priority order (`FE3_header`, `hd_ready`),
 * falls back to the first available crop, or returns null when no image is available.
 *
 * @param production Production object with media gallery data.
 * @returns URL of the selected image, or null if nothing is found.
 */
function getProductionHeroImageUrl(production: Production): string | null {
  // Find the first media item of type 'foto'
  const mediaItems = production.media_gallery.media_items
  const firstPhoto = mediaItems.find((item) => item.type === 'foto')

  // return null if there is no item with type 'foto'
  if (!firstPhoto) {
    return null
  }

  // find one of the preferred crops
  const cropPriority = ['FE3_header', 'hd_ready']
  const bestCrop = cropPriority
    .map((name) => firstPhoto.crops.find((crop) => crop.name === name && !!crop.image_url))
    .find(Boolean)

  // return the best crop if found
  if (bestCrop?.image_url) {
    return bestCrop.image_url
  }

  // fallback to the first available crop if there was not a crop with FE3_header or hd_ready
  if (firstPhoto.crops.length > 0 && firstPhoto.crops[0].image_url) {
    return firstPhoto.crops[0].image_url
  }

  return null
}

// Sub-components

function MetaRow({ label, value }: { label: string; value: string }) {
  if (!value) return null
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '140px 1fr',
        gap: '8px',
        padding: '14px 0',
        borderBottom: '1px solid #ebebeb',
        alignItems: 'start',
      }}
    >
      <span style={{ color: '#999', fontSize: '0.82rem', paddingTop: '2px' }}>{label}</span>
      <span style={{ fontSize: '0.92rem', color: '#111', fontWeight: 500 }}>{value}</span>
    </div>
  )
}

// Main Component

interface ProductionDetailsPageProps {
  production?: Production
  /** Optional: override hero image URL */
  heroImageUrl?: string
}

export default function ProductionDetailsPage({
  production: initialProduction,
}: ProductionDetailsPageProps) {
  const { id } = useParams()
  const navigate = useNavigate()
  const { i18n, t } = useTranslation()
  const lang = i18n.language

  const [prod, setProd] = useState<Production | null>(initialProduction ?? null)
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  // useEffect to fetch the production given the id in the URL.
  useEffect(() => {
    if (prod) return
    if (!id) return

    setLoading(true)

    const parsed = Number(id)
    if (Number.isNaN(parsed)) {
      const errMsg = t('productions.detail.error.invalidId', 'Invalid production ID')
      navigate('/', {
        state: { floatingAlert: { open: true, message: errMsg, severity: 'error' } },
      })
      setError(errMsg)
      setLoading(false)
      return
    }

    const fetchProduction = async () => {
      try {
        const data = await getProduction(parsed, ['events'])
        console.log(data)
        setProd(data)
      } catch {
        const errMsg = t('productions.detail.error.loadFailed', 'Could not load production')
        navigate('/', {
          state: { floatingAlert: { open: true, message: errMsg, severity: 'error' } },
        })
        setError(errMsg)
      } finally {
        setLoading(false)
      }
    }

    fetchProduction()
  }, [id, prod, t, navigate])

  if (loading && !prod) return <LoadingSpinner fullScreen />

  if (!prod) {
    return (
      <div style={{ padding: 40 }}>
        {error ? (
          <div>{error}</div>
        ) : (
          <div>{t('productions.detail.notFound', 'Productie niet gevonden.')}</div>
        )}
      </div>
    )
  }

  const production = prod

  const title =
    getLocalizedValue(production.title, lang) ||
    production.display_title ||
    t('productions.detail.unknownProduction', 'Unknown production')

  const artistName =
    getLocalizedValue(production.artist_name, lang) || production.display_artist_name || ''

  const tagline = getLocalizedValue(production.tagline, lang) || ''
  const description = getLocalizedValue(production.description, lang) || ''
  const teaser = getLocalizedValue(production.teaser, lang) || ''

  const heroImage = getProductionHeroImageUrl(production)

  const events = production.events ?? []
  const dateRange = getDateRange(events)
  const venues = getUniqueVenues(events)

  const genreLabels = (production.genres || [])
    .map((g: Genre) => g.display_name || getLocalizedValue(g.name || {}, lang))
    .filter(Boolean)

  const genres = genreLabels.join(', ')
  const typeName = production.uit_database_type?.name ?? ''

  const tagLabels = (production.tags || [])
    .map(
      (t: TagType) =>
        t.display_name ||
        getLocalizedValue(t.name || {}, lang) ||
        getLocalizedValue(t.url_title || {}, lang) ||
        t.type ||
        '',
    )
    .filter(Boolean)

  const allTags = [...tagLabels, ...(typeName ? [typeName] : []), ...genreLabels]

  return (
    <div
      style={{
        fontFamily: "'Georgia', 'Times New Roman', serif",
        backgroundColor: '#fff',
        color: '#111',
        minHeight: '100vh',
      }}
    >
      {/* ── Main layout ── */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1.3fr 360px',
          gap: '0',
          maxWidth: '1250px',
          margin: '0 auto',
          padding: '0 40px 60px',
        }}
      >
        {/* LEFT: Breadcrumb + Hero + Description */}
        <div style={{ paddingRight: '48px', paddingTop: '32px' }}>
          {/* Breadcrumb */}
          <div
            style={{
              paddingBottom: '12px',
              fontSize: '0.90rem',
              color: '#999',
              borderBottom: '1px solid #ebebeb',
              fontFamily: "'Helvetica Neue', Arial, sans-serif",
            }}
          >
            <button
              onClick={() => navigate('/')}
              style={{
                background: 'none',
                border: 'none',
                padding: 0,
                margin: 0,
                color: '#999',
                cursor: 'pointer',
                textDecoration: 'underline',
                font: 'inherit',
              }}
            >
              {t('nav.home')}
            </button>
            {' / '}
            <button
              onClick={() => navigate('/productions')}
              style={{
                background: 'none',
                border: 'none',
                padding: 0,
                margin: 0,
                color: '#999',
                cursor: 'pointer',
                textDecoration: 'underline',
                font: 'inherit',
              }}
            >
              {t('productions.title')}
            </button>
            {' / '}
            <span style={{ color: '#111' }}>{title}</span>
          </div>

          {/* Hero image */}
          <div
            style={{
              width: '100%',
              aspectRatio: '16/7',
              backgroundColor: '#1a1a1a',
              borderRadius: '4px',
              overflow: 'hidden',
              marginBottom: '32px',
            }}
          >
            {heroImage ? (
              <img
                src={heroImage}
                alt={title}
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              />
            ) : (
              <div
                style={{
                  width: '100%',
                  height: '100%',
                  background: 'linear-gradient(135deg, #1a1a1a 0%, #333 100%)',
                }}
              />
            )}
          </div>

          <div>
            {teaser && (
              <div
                style={{
                  fontSize: '1.05rem',
                  lineHeight: 1.7,
                  color: '#333',
                  fontStyle: 'italic',
                  marginBottom: '20px',
                }}
                dangerouslySetInnerHTML={{ __html: sanitizeHtml(teaser) }}
              />
            )}
            {description ? (
              <div
                style={{
                  fontSize: '0.95rem',
                  lineHeight: 1.8,
                  color: '#444',
                }}
                dangerouslySetInnerHTML={{ __html: sanitizeHtml(description) }}
              />
            ) : (
              <p
                style={{
                  fontSize: '0.9rem',
                  color: '#bbb',
                  fontStyle: 'italic',
                  fontFamily: 'sans-serif',
                }}
              >
                {t('productions.detail.noDescription', 'No description available.')}
              </p>
            )}
          </div>
        </div>

        {/* RIGHT: Metadata panel */}
        <div
          style={{
            paddingTop: '32px',
            borderLeft: '1px solid #ebebeb',
            paddingLeft: '40px',
          }}
        >
          {/* Title block */}
          <h1
            style={{
              fontSize: '2rem',
              fontWeight: 700,
              lineHeight: 1.15,
              margin: '0 0 8px',
              letterSpacing: '-0.02em',
            }}
          >
            {title}
          </h1>

          {(tagline || artistName) && (
            <p
              style={{
                fontSize: '0.95rem',
                color: '#666',
                margin: '0 0 24px',
                fontStyle: 'italic',
              }}
            >
              {tagline || artistName}
            </p>
          )}

          <div style={{ borderTop: '1px solid #ebebeb', marginBottom: '4px' }} />

          {/* Meta rows */}
          <div style={{ fontFamily: "'Helvetica Neue', Arial, sans-serif" }}>
            {dateRange && (
              <MetaRow label={t('productions.detail.meta.period', 'Periode')} value={dateRange} />
            )}
            {venues && (
              <MetaRow label={t('productions.detail.meta.venues', 'Locaties')} value={venues} />
            )}
            {genres && (
              <MetaRow label={t('productions.detail.meta.genre', 'Genre')} value={genres} />
            )}
            {typeName && (
              <MetaRow label={t('productions.detail.meta.type', 'Type')} value={typeName} />
            )}
            <MetaRow
              label={t('productions.detail.meta.performerType', 'Uitvoering')}
              value={
                production.performer_type === 'group'
                  ? t('productions.detail.meta.group', 'Groep')
                  : production.performer_type === 'solo'
                    ? t('productions.detail.meta.solo', 'Solo')
                    : ''
              }
            />
            <MetaRow
              label={t('productions.detail.meta.attendance', 'Aanwezigheid')}
              value={
                production.attendance_mode === 'offline'
                  ? t('productions.detail.meta.offline', 'Fysiek')
                  : production.attendance_mode === 'online'
                    ? t('productions.detail.meta.online', 'Online')
                    : ''
              }
            />
          </div>

          {/* Tags */}
          {allTags.length > 0 && (
            <div
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: '8px',
                marginTop: '28px',
              }}
            >
              {allTags.map((tag, i) => (
                <Tag key={i} tagName={tag} context="description" />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
