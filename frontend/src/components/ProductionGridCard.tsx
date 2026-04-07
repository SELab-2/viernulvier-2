import DateRangeOutlinedIcon from '@mui/icons-material/DateRangeOutlined'
import { Stack, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Link as RouterLink } from 'react-router-dom'
import type { Production } from '../types/Productions'
import { getProductionDateLabel } from '../utils/dateUtils'
import { getTranslatedRecord } from '../utils/translations'
import GenreChip from './GenreChip'
import ImageWithFallback from './ImageWithFallback'

export interface ProductionGridCardProps {
  production: Production
  selectedGenreIds?: number[]
  onGenreClick?: (genreId: number) => void
}

/**
 * Vertical card for a {@link Production}: full-width image, title, artist, genre chips,
 * and a link to the detail route. Intended for mobile-friendly grid layouts.
 *
 * Text is resolved with the active i18n locale via {@link getTranslatedRecord}. The image uses the
 * first crop of the first gallery image when present; otherwise {@link ImageWithFallback} shows the
 * branded placeholder.
 *
 * @param props.production Full API payload (title, artist, media gallery, genres, events, etc.).
 * @param props.selectedGenreIds Genre ids selected in parent filter state (drives chip style).
 * @param props.onGenreClick Called with a genre id when that chip is pressed.
 * @returns The grid card element.
 */
const ProductionGridCard = ({
  production,
  selectedGenreIds,
  onGenreClick,
}: ProductionGridCardProps) => {
  const { i18n } = useTranslation()
  const language = i18n.language

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

  return (
    <Stack
      component={RouterLink}
      to={`/productions/${production.id}`}
      width={350}
      borderRadius={4}
      overflow="hidden"
      sx={(theme) => ({
        textDecoration: 'none',
        border: `1px solid ${theme.palette.divider}`,
        backgroundColor: theme.palette.background.paper,
        transition: 'box-shadow 0.2s ease',
        '&:hover': {
          boxShadow: theme.shadows[3],
        },
      })}
    >
      <ImageWithFallback src={imageSrc} alt={title} sx={{ aspectRatio: 16 / 9 }} />

      <Stack flex={1} justifyContent="space-between" gap={1} padding={3}>
        <Stack>
          <Typography component="h2" variant="h5" color="textPrimary" fontWeight="bold">
            {title}
          </Typography>

          {artistName ? (
            <Typography component="p" color="textSecondary">
              {artistName}
            </Typography>
          ) : null}
        </Stack>

        <Stack color="text.secondary" spacing={1}>
          {dateLabel ? (
            <Stack direction="row" alignItems="center" spacing={1}>
              <DateRangeOutlinedIcon fontSize="inherit" />
              <Typography variant="body2" noWrap>
                {dateLabel}
              </Typography>
            </Stack>
          ) : null}

          {genres.length > 0 ? (
            <Stack direction="row" flexWrap="wrap" spacing={0.75} height={24} overflow="hidden">
              {genres.map((genre) => (
                <GenreChip
                  key={genre.id}
                  genre={genre}
                  selectedIds={selectedGenreIds}
                  onClick={onGenreClick}
                />
              ))}
            </Stack>
          ) : null}
        </Stack>
      </Stack>
    </Stack>
  )
}

export default ProductionGridCard
