import { Box, Typography, useMediaQuery } from '@mui/material'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useLocation, useParams, useNavigate } from 'react-router-dom'

import ProductionDetailPageSkeleton from './ProductionDetailPageSkeleton'
import Breadcrumbs from '../components/detail/Breadcrumbs'
import Description from '../components/detail/Description'
import EventsList from '../components/detail/EventList'
import MediaList from '../components/detail/MediaList'
import MetaPanel from '../components/detail/MetaPanel'
import RelatedBlogs from '../components/detail/RelatedBlogs'
import RelatedProductions from '../components/detail/RelatedProductions'
import ImageWithFallback from '../../../shared/components/ImageWithFallback'
import { getProduction } from '../../../services/productions/Productions'
import { tokens } from '../../../theme/tokens'
import type { Production } from '../../../types/Productions'
import { getLocalizedValue } from '../../../utils/localization'
import { resolveCurrentLanguage, toLocalizedPath } from '../../../utils/localizedRoutes'
import { ApiError } from '../../../services/ApiTypes'
import { ALERT_SEVERITIES } from '../../../types/FloatingAlertConfig'
import { redirectWithFloatingAlert } from '../../../utils/navigation'


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

type ProductionDetailContentProps = {
  id: string
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
const ProductionDetailContent = ({ id }: ProductionDetailContentProps) => {
  const navigate = useNavigate()
  const location = useLocation()
  const { i18n, t } = useTranslation()
  const isMobile = useMediaQuery('(max-width:900px)')
  const lang = i18n.language
  const currentLanguage = resolveCurrentLanguage(
    location.pathname,
    i18n.language,
    i18n.resolvedLanguage,
  )
  const archivePath = toLocalizedPath('/archive', currentLanguage)
  const currentPath = location.pathname

  const [prod, setProd] = useState<Production | null>(null)
  const [loading, setLoading] = useState<boolean>(true)

  // useEffect to fetch the production given the id in the URL.
  useEffect(() => {
    const parsed = Number(id)
    if (Number.isNaN(parsed)) {
      const errMsg = t('productions.detail.error.invalidId', 'Invalid production ID')
      redirectWithFloatingAlert(navigate, archivePath, {
        message: errMsg,
        severity: ALERT_SEVERITIES.error,
      })
      return
    }

    const fetchProduction = async () => {
      try {
        const data = await getProduction(parsed, ['events', 'related', 'blogs'])
        setProd(data)
      } catch (error: unknown) {
        if (error instanceof ApiError && error.status === 429) {
          const errMsg = error.message
          redirectWithFloatingAlert(navigate, currentPath, {
            message: errMsg,
            severity: ALERT_SEVERITIES.warning,
          })
        } else {
          const errMsg = t('productions.detail.error.loadFailed', 'Could not load production')
          redirectWithFloatingAlert(navigate, toLocalizedPath('/404', currentLanguage), {
            message: errMsg,
            severity: ALERT_SEVERITIES.error,
          })
        }
      } finally {
        setLoading(false)
      }
    }

    fetchProduction()
  }, [archivePath, currentLanguage, currentPath, id, navigate, t])

  // If the page is still loading, show a full-page skeleton.
  if (loading) {
    return <ProductionDetailPageSkeleton />
  }

  // If there was an error or no production was found, show an error message.
  if (!prod) {
    return (
      <Box sx={{ p: 5 }}>
        <Box>{t('productions.detail.notFound', 'Productie niet gevonden.')}</Box>
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
  const relatedProductions = production.related ?? []
  const relatedBlogs = production.blogs ?? []
  const video1 = getLocalizedValue(production.video_1, lang) || null
  const video2 = getLocalizedValue(production.video_2, lang) || null
  const videoUrls = [video1, video2].filter(Boolean) as string[]

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
          {isMobile && (
            <Typography
              component="h1"
              sx={{
                fontSize: tokens.typography.sizes['3xl'],
                fontWeight: tokens.typography.weights.bold,
                lineHeight: 1.15,
                letterSpacing: '-0.02em',
                color: 'text.primary',
                mt: 3,
                mb: 3,
              }}
            >
              {title}
            </Typography>
          )}
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
              loading="eager"
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
          <MetaPanel
            production={production}
            language={lang}
            showHeader={!isMobile}
            sx={{ borderLeft: 'none' }}
          />
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

      {(videoUrls.length > 0 || (production.media_gallery?.media_items?.length ?? 0) > 0) && (
        <Box sx={{ pb: 4 }}>
          <MediaList
            mediaItems={production.media_gallery?.media_items ?? []}
            videoUrls={videoUrls}
          />
        </Box>
      )}

      {relatedProductions.length > 0 && (
        <Box sx={{ px: 2, pb: 4 }}>
          <RelatedProductions related={relatedProductions} lang={lang} />
        </Box>
      )}

      {relatedBlogs.length > 0 && (
        <Box sx={{ px: 2, pb: 4 }}>
          <RelatedBlogs blogs={relatedBlogs} />
        </Box>
      )}
    </Box>
  )
}

const ProductionDetailsPage = () => {
  const { id } = useParams()

  if (!id) {
    return null
  }

  return <ProductionDetailContent key={id} id={id} />
}

export default ProductionDetailsPage
