import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Box, Typography, useTheme } from '@mui/material'
import { useTranslation } from 'react-i18next'
import type { Production } from '../types/Productions'
import LoadingSpinner from '../components/LoadingSpinner'
import Breadcrumbs from '../components/production/Breadcrumbs'
import ImageWithFallback from '../components/ImageWithFallback'
import Description from '../components/production/Description'
import MetaPanel from '../components/production/MetaPanel'
import { getProduction } from '../services/productions/Productions'
import EventsList from '../components/production/EventList'
import MediaList from '../components/production/MediaList'
import { getLocalizedValue } from '../utils/localization'

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

/**
 * Production detail page.
 *
 * Responsible for:
 * - fetching production by ID from URL params
 * - handling loading and error states
 * - rendering content sections:
 *   - breadcrumb, hero image, description
 *   - metadata panel (with MetaPanel component)
 *   - events list, media gallery
 *
 * Important: no business transformations here; MetaPanel handles production meta resolution.
 */
const ProductionDetailsPage = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const theme = useTheme()
  const { i18n, t } = useTranslation()
  const lang = i18n.language

  const [prod, setProd] = useState<Production | null>(null)
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  // useEffect to fetch the production given the id in the URL.
  useEffect(() => {
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
  }, [id, t, navigate])

  // If the page is still loading, show the spinner.
  if (loading && !prod) return <LoadingSpinner fullScreen />

  // If there was an error or no production was found, show an error message.
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

  const description = getLocalizedValue(production.description, lang) || ''
  const teaser = getLocalizedValue(production.teaser, lang) || ''

  const heroImage = getProductionHeroImageUrl(production)

  const events = production.events ?? []

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
          style={{ backgroundColor: theme.palette.background.default }}
        >
          <Breadcrumbs
            items={[
              { label: 'Home', translationKey: 'nav.home', to: '/' },
              { label: 'Producties', translationKey: 'productions.title', to: '/productions' },
              { label: title },
            ]}
          />
          <div
            className="hero-image"
            style={{
              width: '100%',
              aspectRatio: '16/7',
              backgroundColor: 'transparent',
              borderRadius: '4px',
              overflow: 'hidden',
              marginBottom: '32px',
            }}
          >
            <ImageWithFallback
              src={heroImage ?? null}
              alt={title}
              sx={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          </div>
          <Description teaser={teaser} description={description} />
        </div>
        {/* RIGHT: Metadata panel */}
        <div
          className="production-details-right"
          style={{
            backgroundColor: theme.palette.background.default,
            borderLeft: `1px solid ${theme.palette.divider}`,
          }}
        >
          <MetaPanel production={production} language={lang} style={{ borderLeft: 'none' }} />
          <Box
            sx={(theme) => ({
              mt: 3,
              p: 2,
              border: `1px solid ${theme.palette.divider}`,
              backgroundColor: theme.palette.background.paper,
              borderRadius: '4px',
            })}
          >
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

      {production.media_gallery.media_items.length > 0 && (
        <div style={{ padding: '0 16px 32px' }}>
          <MediaList mediaItems={production.media_gallery.media_items} />
        </div>
      )}
      <p> TODO: related productions tonen </p>
    </div>
  )
}

export default ProductionDetailsPage
