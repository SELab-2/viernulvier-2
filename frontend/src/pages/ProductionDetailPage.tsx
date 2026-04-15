import { Box, Typography } from '@mui/material'
import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useParams, useNavigate } from 'react-router-dom'

import ProductionDetailPageSkeleton from './ProductionDetailPageSkeleton'
import ImageWithFallback from '../components/ImageWithFallback'
import Breadcrumbs from '../components/production/Breadcrumbs'
import Description from '../components/production/Description'
import EventsList from '../components/production/EventList'
import MediaList from '../components/production/MediaList'
import MetaPanel from '../components/production/MetaPanel'
import RelatedProductions from '../components/production/RelatedProductions'
import { getProduction } from '../services/productions/Productions'
import { tokens } from '../theme/tokens'
import { getLocalizedValue } from '../utils/localization'

import type { Production } from '../types/Productions'

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
  const mediaItems = production.media_gallery?.media_items
  const firstPhoto = mediaItems?.find((item) => item.type === 'foto')

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
 */
const ProductionDetailsPage = () => {
  const { id } = useParams() // Get the id from the URL params (e.g. /productions/123 -> id = 123)
  const navigate = useNavigate()
  const { i18n, t } = useTranslation()
  const lang = i18n.language

  const [prod, setProd] = useState<Production | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const tRef = useRef(t)
  tRef.current = t

  // useEffect to fetch the production given the id in the URL.
  useEffect(() => {
    if (!id) {
      return
    }
    setLoading(true)

    const parsed = Number(id)
    if (Number.isNaN(parsed)) {
      const errMsg = tRef.current('productions.detail.error.invalidId', 'Invalid production ID')
      navigate('/', {
        state: { floatingAlert: { open: true, message: errMsg, severity: 'error' } },
      })
      setError(errMsg)
      setLoading(false)
      return
    }

    const fetchProduction = async () => {
      try {
        const data = await getProduction(parsed, ['events', 'related'])
        setProd(data)
      } catch {
        const errMsg = tRef.current(
          'productions.detail.error.loadFailed',
          'Could not load production',
        )
        navigate('/', {
          state: { floatingAlert: { open: true, message: errMsg, severity: 'error' } },
        })
        setError(errMsg)
      } finally {
        setLoading(false)
      }
    }

    fetchProduction()
  }, [id, navigate])

  // If the page is still loading, show a full-page skeleton.
  if (loading) {
    return <ProductionDetailPageSkeleton />
  }

  // If there was an error or no production was found, show an error message.
  if (!prod) {
    return (
      <Box sx={{ p: 5 }}>
        {error ? (
          <Box>{error}</Box>
        ) : (
          <Box>{tRef.current('productions.detail.notFound', 'Productie niet gevonden.')}</Box>
        )}
      </Box>
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
    <Box
      className="production-details-page"
      sx={(theme) => ({
        backgroundColor: theme.palette.background.default,
        color: theme.palette.text.primary,
      })}
    >
      <Box
        className="production-details-container"
        sx={(theme) => ({ backgroundColor: theme.palette.background.default })}
      >
        {/* LEFT: Breadcrumb + Hero + Description */}
        <Box
          className="production-details-left"
          sx={(theme) => ({ backgroundColor: theme.palette.background.default })}
        >
          <Breadcrumbs
            items={[
              { label: 'Home', translationKey: 'nav.home', to: '/' },
              { label: 'Producties', translationKey: 'productions.title', to: '/productions' },
              { label: title },
            ]}
          />
          <Box
            className="hero-image"
            sx={{
              width: '100%',
              aspectRatio: '16 / 7',
              backgroundColor: 'transparent',
              borderRadius: tokens.borderRadius.sm,
              overflow: 'hidden',
              mb: 4,
            }}
          >
            <ImageWithFallback
              src={heroImage ?? null}
              alt={title}
              sx={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          </Box>
          <Description teaser={teaser} description={description} />
        </Box>
        {/* RIGHT: Metadata panel */}
        <Box
          className="production-details-right"
          sx={(theme) => ({
            backgroundColor: theme.palette.background.default,
            borderLeft: `1px solid ${theme.palette.divider}`,
          })}
        >
          <MetaPanel production={production} language={lang} sx={{ borderLeft: 'none' }} />
          <Box
            sx={(theme) => ({
              mt: 3,
              p: 2,
              border: `1px solid ${theme.palette.divider}`,
              backgroundColor: theme.palette.background.paper,
              borderRadius: tokens.borderRadius.sm,
            })}
          >
            <Typography
              variant="subtitle1"
              sx={{ mb: 1, color: 'text.primary', fontWeight: tokens.typography.weights.bold }}
            >
              {t('productions.detail.events', 'Events')}
            </Typography>
            <EventsList events={events} />
          </Box>
        </Box>
      </Box>

      {production.media_gallery?.media_items?.length > 0 && (
        <Box sx={{ px: 2, pb: 4 }}>
          <MediaList mediaItems={production.media_gallery.media_items} />
        </Box>
      )}

      {production.related && production.related.length > 0 && (
        <Box sx={{ px: 2, pb: 4 }}>
          <RelatedProductions related={production.related ?? []} lang={lang} />
        </Box>
      )}
    </Box>
  )
}

export default ProductionDetailsPage
