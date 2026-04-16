import ArrowForwardOutlinedIcon from '@mui/icons-material/ArrowForwardOutlined'
import DateRangeOutlinedIcon from '@mui/icons-material/DateRangeOutlined'
import { Box, Stack, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Link as RouterLink } from 'react-router-dom'

import { tokens } from '../../theme/tokens'
import { getProductionDateLabel } from '../../utils/dateUtils'
import { getTranslatedRecord } from '../../utils/translations'
import GenreAndTagChip from '../chips/GenreAndTagChip'
import ImageWithFallback from '../ImageWithFallback'

import type { Production } from '../../types/Productions'

export interface ProductionListCardProps {
  production: Production
  selectedGenreIds?: number[]
}

/**
 * Horizontal card for a {@link Production} or {@link Event}: image, title, artist, optional date and venue,
 * genre filters, and a full-card link to the detail route (genre chips stay separate filters).
 *
 * Text is resolved with the active i18n locale via {@link getTranslatedRecord}. The image uses the
 * first crop of the first gallery image when present; otherwise {@link ImageWithFallback} shows the
 * branded placeholder.
 *
 * @param props.production Full API payload (title, artist, media gallery, genres, events, etc.).
 * @param props.selectedGenreIds Genre ids selected in parent filter state (drives chip style).
 * @returns The list row element.
 */
const ProductionListCard = ({ production, selectedGenreIds }: ProductionListCardProps) => {
  const { i18n } = useTranslation()
  const { language } = i18n

  const imageSrc = production.media_gallery?.media_items[0]?.crops[0]?.image_url
  const title = getTranslatedRecord(production.title, language, production.display_title)
  const artistName = getTranslatedRecord(
    production.artist_name,
    language,
    production.display_artist_name,
  )
  const dateLabel = getProductionDateLabel(
    production.first_event_start,
    production.last_event_end,
    language,
  )
  const genres = production.genres.filter((genre) => genre.display_name)
  const tags = production.tags.filter((tag) => tag.display_name || tag.name || tag.url_title)

  return (
    <Stack
      component={RouterLink}
      to={`/productions/${production.id}`}
      direction="row"
      sx={(theme) => ({
        gap: 3,
        height: 170,
        p: 3,
        borderRadius: tokens.borderRadius.sm,
        overflow: 'hidden',
        backgroundColor: theme.palette.background.paper,
        border: `1px solid ${theme.palette.divider}`,
        textDecoration: 'none',
        transition: 'box-shadow 0.2s ease',
        '&:hover': {
          boxShadow: theme.shadows[3],
        },
      })}
    >
      <ImageWithFallback
        src={imageSrc}
        alt={title}
        height="100%"
        sx={{ aspectRatio: 16 / 9, borderRadius: tokens.borderRadius.sm }}
      />

      <Stack
        sx={{
          flex: 1,
          minWidth: 0,
          height: '100%',
          justifyContent: 'space-between',
          gap: 1,
          overflow: 'hidden',
        }}
      >
        <Stack>
          <Typography
            component="h2"
            variant="h6"
            color="textPrimary"
            noWrap
            sx={{ fontWeight: 'bold' }}
          >
            {title}
          </Typography>

          {artistName ? (
            <Typography component="p" color="textSecondary" noWrap>
              {artistName}
            </Typography>
          ) : null}
        </Stack>

        <Stack spacing={1} sx={{ color: 'text.secondary', minHeight: 48 }}>
          <Stack direction="row" spacing={1} sx={{ alignItems: 'center', minHeight: 20 }}>
            {dateLabel ? (
              <>
                <DateRangeOutlinedIcon fontSize="inherit" />
                <Typography variant="body2" noWrap>
                  {dateLabel}
                </Typography>
              </>
            ) : null}
          </Stack>

          <Stack
            direction="row"
            spacing={0.75}
            sx={{ flexWrap: 'wrap', height: 32, overflow: 'hidden' }}
          >
            {tags.map((tag) => (
              <GenreAndTagChip
                key={`tag-${tag.id}`}
                name={getTranslatedRecord(
                  tag.name || tag.url_title || {},
                  language,
                  tag.display_name ?? tag.type ?? String(tag.id),
                )}
                labels={tag.name || tag.url_title || {}}
                chipType="seriesTag"
                context="static"
                id={tag.id}
              />
            ))}
            {genres.map((genre) => (
              <GenreAndTagChip
                key={genre.id}
                name={getTranslatedRecord(
                  genre.name,
                  language,
                  genre.display_name ?? String(genre.id),
                )}
                labels={genre.name || {}}
                chipType="genre"
                context="static"
                id={genre.id}
                selected={selectedGenreIds?.includes(genre.id) || false}
              />
            ))}
          </Stack>
        </Stack>
      </Stack>

      <Box sx={{ alignSelf: 'center', pr: 2 }}>
        <ArrowForwardOutlinedIcon color="action" />
      </Box>
    </Stack>
  )
}

export default ProductionListCard
