import { Box, Stack, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'

import Carousel from '../../../../shared/components/Carousel'
import GenreAndTagChip from '../../../../shared/components/chips/GenreAndTagChip'
import { tokens } from '../../../../theme/tokens'
import { getTranslatedRecord } from '../../../../utils/translations'
import ProductionGridCard from '../cards/ProductionGridCard'

import type { ProductionRelated, RelatedTag } from '../../../../types/Productions'

/**
 * Define the props for the RelatedProductions component:
 * - related: Optional list of related entries grouped by tag (returned by the API on production detail).
 * - lang: Optional language code used to pick a display name for each tag (falls back to `display_name` or tag id).
 */
interface RelatedProductionsProps {
  related: ProductionRelated[]
  lang?: string
  showTag?: boolean
}

/**
 * Renders related productions grouped by tag from the production detail payload.
 */
function RelatedProductions({ lang = 'nl', related, showTag = true }: RelatedProductionsProps) {
  const { t, i18n } = useTranslation()
  const language = i18n.language || lang

  const visibleResults = related.filter((entry) => entry.productions.length > 0)

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
      <Typography
        variant="h5"
        sx={(theme) => ({
          fontWeight: tokens.typography.weights.bold,
          fontSize: { xs: '1.05rem', sm: '1.25rem' },
          letterSpacing: '-0.01em',
          color: theme.palette.text.primary,
        })}
      >
        {t('productions.detail.related', 'Related productions')}
      </Typography>
      {visibleResults.map((entry) => {
        const tagName = getTagLabel(entry.tag)

        return (
          <Box key={entry.tag.id}>
            {showTag && (
              <Box
                sx={{ mb: 1.5, display: 'inline-flex', fontWeight: tokens.typography.weights.bold }}
              >
                <GenreAndTagChip
                  name={tagName}
                  labels={entry.tag.name as Record<string, string>}
                  context="series"
                  chipType="seriesTag"
                  id={entry.tag.id}
                />
              </Box>
            )}
            <Carousel
              ariaLabel={
                showTag
                  ? `${t('productions.detail.related', 'Related productions')} for ${tagName}`
                  : t('productions.detail.related', 'Related productions')
              }
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

                // TODO:
                // Related productions don't have all the values of a production
                // It only contains the values required for the frontend to show the cards
                // We could change the API to return complete productions to avoid this normalization
                // Or we could make the ProductionGridCard work with the related production types
                // For now just use normalization, but maybe this should be looked at again?
                return (
                  <Box
                    key={production.id}
                    sx={{
                      display: 'flex',
                      alignItems: 'stretch',
                      // make the inner ProductionGridCard fill the slide height
                      '& > a': {
                        display: 'flex',
                        flexDirection: 'column',
                        height: '100%',
                      },
                      // Ensure the MUI Stack inside the link stretches to full height
                      '& > a > .MuiStack-root': {
                        height: '100%',
                      },
                    }}
                  >
                    <ProductionGridCard
                      production={{
                        ...production,
                        attendance_mode: '',
                        performer_type: '',
                        first_event_start: null,
                        last_event_end: null,
                        uit_database_type: null,
                        artist_name: production.artist_name ?? {},
                        tagline: {},
                        teaser: {},
                        description: {},
                        tags: [],
                        genres: [],
                        display_title: normalizedTitle,
                        display_artist_name: normalizedArtist,
                      }}
                    />
                  </Box>
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
