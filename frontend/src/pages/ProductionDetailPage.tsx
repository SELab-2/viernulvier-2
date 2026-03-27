import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Box, Typography, useTheme } from '@mui/material'
import { useTranslation } from 'react-i18next'
import type { Production } from '../types/Productions'
import type { Event } from '../types/Events'
import type { Genre } from '../types/Genres'
import type { Tag as TagType } from '../types/Tags'
import LoadingSpinner from '../components/LoadingSpinner'
import Breadcrumbs from '../components/production/Breadcrumbs'
import HeroImage from '../components/production/HeroImage'
import Description from '../components/production/Description'
import MetaPanel from '../components/production/MetaPanel'
import MediaList from '../components/production/MediaList'
import { getProduction } from '../services/productions/Productions'
import getLocationName from '../utils/locations'
import EventsList from '../components/production/EventList'

// TODO: evenementen tonen (aparte component ?)
// TODO: check tags
// TODO: andere producties in reeks tonen (aparte component ?)

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

function formatDateTime(dateStr?: string | null): string {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('nl-BE', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
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

  if (!list.length) {
    return ''
  }

  const dates = list.map((e) => new Date(e.starts_at as string).getTime()).sort((a, b) => a - b)
  const first = new Date(dates[0])
  const last = new Date(dates[dates.length - 1])

  if (first.toDateString() === last.toDateString()) {
    return formatDate(list[0].starts_at)
  }

  return `${formatDate(first.toString())} - ${formatDate(last.toString())}`
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
  const theme = useTheme()
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
      className="production-details-page"
      style={{
        backgroundColor: theme.palette.background.default,
        color: theme.palette.text.primary,
      }}
    >
      <div
        className="production-details-container"
        style={{ backgroundColor: theme.palette.background.default }}
      >
        {/* LEFT: Breadcrumb + Hero + Description */}
        <div
          className="production-details-left"
          style={{ backgroundColor: theme.palette.background.paper }}
        >
          <Breadcrumbs
            items={[
              { label: 'Home', translationKey: 'nav.home', to: '/' },
              { label: 'Producties', translationKey: 'productions.title', to: '/productions' },
              { label: title },
            ]}
          />
          <HeroImage title={title} imageUrl={heroImage ?? null} />
          <Description teaser={teaser} description={description} />
        </div>
        {/* RIGHT: Metadata panel */}
        <div
          className="production-details-right"
          style={{
            backgroundColor: theme.palette.background.paper,
            borderLeft: `1px solid ${theme.palette.divider}`,
          }}
        >
          <MetaPanel
            title={title}
            tagline={tagline}
            artistName={artistName}
            dateRange={dateRange}
            venues={venues}
            genres={genres}
            typeName={typeName}
            performerType={production.performer_type}
            attendanceMode={production.attendance_mode}
            allTags={allTags}
            style={{ borderLeft: 'none' }}
          />
          <Box sx={(theme) => ({ mt: 3, p: 2, border: `1px solid ${theme.palette.divider}`, borderRadius: '4px' })}>
            <Typography
              variant="subtitle1"
              fontWeight={600}
              sx={{ mb: 1, color: theme.palette.text.primary }}
            >
              {t('productions.detail.events', 'Events')}
            </Typography>
            <EventsList events={events} />
          </Box>
        </div>
      </div>

      {production.media_gallery?.media_items?.length > 0 && (
        <div style={{ padding: '0 16px 32px' }}>
          <MediaList mediaItems={production.media_gallery.media_items} />
        </div>
      )}
    </div>
  )
}
