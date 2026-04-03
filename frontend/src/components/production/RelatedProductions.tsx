import { useEffect, useMemo, useState } from 'react'
import { Box, Skeleton, Stack, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'
import type { Production } from '../../types/Productions'
import type { Tag } from '../../types/Tags'
import Carousel from '../carousel/Carousel'
import Card from '../carousel/Card'
import { getRelatedProductions } from '../../utils/productions'
import { getTranslatedRecord } from '../../utils/translations'

/**
 * Define the props for the RelatedProductions component:
 * - currentProductionId: Optional ID to exclude from related items so we don't show the same production.
 * - tags: Array of Tag objects to find related productions for.
 * - lang: Optional language code used to pick a display name for each tag (falls back to `display_name` or tag id).
 */
interface RelatedProductionsProps {
  tags: Tag[]
  lang?: string
  currentProductionId?: number
}

/**
 * RelatedProductions component fetches and displays a list of productions that share common tags with the current production.
 * The component is currently used in the ProductionDetailPage.
 *
 * @param tagIds - An array of tag IDs to find related productions.
 * @param currentProductionId - Current production ID which should be excluded from related items.
 * @param lang - Optional language code used to pick a display name for each tag (falls back to `display_name` or tag id).
 * @param tags - An array of Tag objects to find related productions for.
 * @returns A React component that displays a list of related productions based on shared tags.
 */
function RelatedProductions({ tags, lang = 'nl', currentProductionId }: RelatedProductionsProps) {
  const { t, i18n } = useTranslation()
  const language = i18n.language || lang

  const [perTagResults, setPerTagResults] = useState<Array<[Tag, Production[]]>>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const visibleResults = useMemo(
    () => perTagResults.filter(([, productions]) => productions.length > 0),
    [perTagResults],
  )

  /**
   * Extracts the best hero image from a production using the same crop preference as the rest of the app.
   */
  function getBestImageUrl(production: Production): string | null {
    const cropPriority = ['FE3_header', 'hd_ready']
    const firstPhoto = production.media_gallery?.media_items.find((item) => item.type === 'foto')

    if (!firstPhoto) {
      return null
    }

    const bestCrop = cropPriority
      .map((name) => firstPhoto.crops.find((crop) => crop.name === name && !!crop.image_url))
      .find(Boolean)

    if (bestCrop?.image_url) {
      return bestCrop.image_url
    }

    return firstPhoto.crops.find((crop) => !!crop.image_url)?.image_url ?? null
  }

  /**
   * Resolves the tag label for the active locale without reloading the production list.
   */
  function getTagLabel(tag: Tag): string {
    return getTranslatedRecord(tag.name, language, tag.display_name ?? `tag:${tag.id}`)
  }

  /**
   * Skeleton state that reserves roughly the same amount of vertical space as the final cards.
   */
  function RelatedProductionsSkeleton() {
    return (
      <Stack
        data-testid="related-productions-skeleton"
        spacing={1.5}
        sx={{ p: 2, width: '100%', maxWidth: 1250, mx: 'auto' }}
      >
        <Skeleton variant="text" width={240} height={32} />
        <Stack spacing={2.5}>
          <Skeleton variant="text" width={180} height={22} />
          <Carousel
            ariaLabel="Related productions"
            maxWidth="100%"
            showArrows={false}
            showDots={false}
            sx={{ width: '100%' }}
          >
            {Array.from({ length: 4 }).map((_, index) => (
              <Box
                key={index}
                sx={(theme) => ({
                  minHeight: 330,
                  borderRadius: 2.5,
                  overflow: 'hidden',
                  border: `1px solid ${theme.palette.divider}`,
                  backgroundColor: theme.palette.background.paper,
                })}
              >
                <Skeleton variant="rectangular" sx={{ height: 185, width: '100%' }} />
                <Stack spacing={0.75} sx={{ p: 1.5 }}>
                  <Skeleton variant="text" width="78%" height={24} />
                  <Skeleton variant="text" width="56%" height={18} />
                </Stack>
              </Box>
            ))}
          </Carousel>
        </Stack>
      </Stack>
    )
  }

  useEffect(() => {
    let cancelled = false

    const fetch = async () => {
      // The related-production payload is language-agnostic; translation happens at render time.
      if (tags.length === 0) {
        if (!cancelled) {
          setPerTagResults([])
          setLoading(false)
          setError(null)
        }
        return
      }

      setLoading(true)
      setError(null)

      try {
        const data = await getRelatedProductions(tags, currentProductionId)
        if (!cancelled) setPerTagResults(data)
      } catch (err) {
        if (cancelled) return
        console.error('Error fetching related productions:', err)
        setError('Kon gerelateerde producties niet laden')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    fetch()

    return () => {
      cancelled = true
    }
  }, [tags, currentProductionId])

  if (loading) {
    return <RelatedProductionsSkeleton />
  }

  if (error) {
    // TODO: betere error afhandeling (bv. de popup)
    return (
      <Box sx={{ p: 2 }}>
        <Typography color="error" variant="body2">
          {error}
        </Typography>
      </Box>
    )
  }

  /**
   * If there are no related productions found for any of the tags, nothing is rendered.
   */
  if (visibleResults.length === 0) {
    return null
  }

  return (
    <Stack spacing={3} sx={{ p: 2, width: '100%', maxWidth: 1250, mx: 'auto' }}>
      {/* This heading follows the active locale while the underlying data stays untouched. */}
      <Typography variant="h6">{t('productions.detail.related', 'Related productions')}</Typography>
      {visibleResults.map(([tag, productions]) => {
        const tagName = getTagLabel(tag)

        return (
          <Box key={tag.id}>
            <Typography variant="subtitle2" sx={{ mb: 1.5 }}>
              {tagName}
            </Typography>
            <Carousel
              ariaLabel={`${t('productions.detail.related', 'Related productions')} for ${tagName}`}
              maxWidth="100%"
              previousLabel={t('carousel.previousSlide', 'Previous slide')}
              nextLabel={t('carousel.nextSlide', 'Next slide')}
              slideLabel={t('carousel.goToSlide', 'Go to slide')}
              sx={{ width: '100%' }}
            >
              {productions.slice(0, 6).map((production) => {
                const title = getTranslatedRecord(production.title, language, production.display_title)
                const subtitle =
                  getTranslatedRecord(
                    production.artist_name,
                    language,
                    production.display_artist_name,
                  ) || undefined

                return (
                  <Card
                    key={production.id}
                    href={`/productions/${production.id}`}
                    title={title}
                    subtitle={subtitle}
                    imageSrc={getBestImageUrl(production)}
                    imageAlt={title}
                  />
                )
              })}
            </Carousel>
          </Box>
        )
      })}
    </Stack>
  )
}

export default RelatedProductions
