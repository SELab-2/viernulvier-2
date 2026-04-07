import { Box, Link, Stack, Typography } from '@mui/material'
import { Link as RouterLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import type { ProductionRelated, RelatedProduction, RelatedTag } from '../../types/Productions'
import Carousel from '../carousel/Carousel'
import ProductionGridCard from '../ProductionGridCard'
import { getTranslatedRecord } from '../../utils/translations'

/**
 * Define the props for the RelatedProductions component:
 * - related: Optional list of related entries grouped by tag (returned by the API on production detail).
 * - lang: Optional language code used to pick a display name for each tag (falls back to `display_name` or tag id).
 */
interface RelatedProductionsProps {
  related: ProductionRelated[]
  lang?: string
}

/**
 * Renders related productions grouped by tag from the production detail payload.
 */
function RelatedProductions({ lang = 'nl', related }: RelatedProductionsProps) {
  const { t, i18n } = useTranslation()
  const language = i18n.language || lang

  const visibleResults = related.filter((entry) => entry.productions.length > 0)

  /**
   * Extracts the best hero image from a production using the same crop preference as the rest of the app.
   */
  function getBestImageUrl(production: RelatedProduction): string | null {
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
  function getTagLabel(tag: RelatedTag): string {
    return getTranslatedRecord(tag.name, language, tag.display_name ?? `tag:${tag.id}`)
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
      {visibleResults.map((entry) => {
        const tagName = getTagLabel(entry.tag)

        return (
          <Box key={entry.tag.id}>
            <Link
              component={RouterLink}
              to={`/series/${entry.tag.id}`}
              variant="subtitle2"
              underline="hover"
              color="primary"
              sx={{
                mb: 1.5,
                display: 'inline-flex',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              {tagName}
            </Link>
            <Carousel
              ariaLabel={`${t('productions.detail.related', 'Related productions')} for ${tagName}`}
              maxWidth="100%"
              previousLabel={t('carousel.previousSlide', 'Previous slide')}
              nextLabel={t('carousel.nextSlide', 'Next slide')}
              slideLabel={t('carousel.goToSlide', 'Go to slide')}
              sx={{ width: '100%' }}
            >
              {entry.productions.map((production) => {
                const normalizedTitle = getTranslatedRecord(
                  production.title,
                  language,
                  production.display_title,
                )

                const normalizedArtist =
                  getTranslatedRecord(
                    production.artist_name,
                    language,
                    production.display_artist_name,
                  ) || ''

                return (
                  <ProductionGridCard
                    key={production.id}
                    production={{
                      ...production,
                      genres: production.genres ?? [],
                      display_title: normalizedTitle,
                      display_artist_name: normalizedArtist,
                    }}
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
