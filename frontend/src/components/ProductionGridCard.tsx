import DateRangeOutlinedIcon from '@mui/icons-material/DateRangeOutlined'
import { Stack, Typography, useTheme } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Link as RouterLink } from 'react-router-dom'
import { createCommonStyles } from '../theme/styles'
import { tokens } from '../theme/tokens'
import type { Production } from '../types/Productions'
import { getProductionDateLabel } from '../utils/dateUtils'
import { getTranslatedRecord } from '../utils/translations'
import GenreAndTagChip from './chips/GenreAndTagChip'
import ImageWithFallback from './ImageWithFallback'

export interface ProductionGridCardProps {
  production: Production
  selectedGenreIds?: number[]
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
 * @returns The grid card element.
 */
const ProductionGridCard = ({ production, selectedGenreIds }: ProductionGridCardProps) => {
  const theme = useTheme()
  const commonStyles = createCommonStyles(theme)
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
      sx={{
        ...commonStyles.cardBase,
        width: 350,
        height: '100%',
        borderRadius: tokens.card.borderRadius,
        overflow: 'hidden',
      }}
    >
      <ImageWithFallback src={imageSrc} alt={title} sx={{ aspectRatio: 16 / 9 }} />

      <Stack
        sx={{
          flex: 1,
          justifyContent: 'space-between',
          gap: tokens.spacing.numericSm,
          p: tokens.spacing.numericLg,
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

        <Stack spacing={1} sx={{ color: 'text.secondary', minHeight: 56 }}>
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
            {genres.map((genre) => (
              <GenreAndTagChip
                key={genre.id}
                name={genre.display_name || ''} // TODO: resolve so there is always a fallback
                labels={{}}
                chipType="genre"
                context="static"
                id={genre.id}
                selected={selectedGenreIds?.includes(genre.id)} // TODO: resolve so this is never undefined
              />
            ))}
          </Stack>
        </Stack>
      </Stack>
    </Stack>
  )
}

export default ProductionGridCard
