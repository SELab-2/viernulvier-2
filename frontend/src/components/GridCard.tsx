import DateRangeOutlinedIcon from '@mui/icons-material/DateRangeOutlined'
import RoomOutlinedIcon from '@mui/icons-material/RoomOutlined'
import { Paper, Stack, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Link as RouterLink } from 'react-router-dom'
import type { Production } from '../types/Productions'
import { getEventDateRangeLabel, getSharedLocationName } from '../utils/productionEvents'
import { getTranslatedRecord } from '../utils/translations'
import GenreChip from './GenreChip'
import ImageWithFallback from './ImageWithFallback'

export interface GridCardProps {
  production: Production
  selectedGenreIds: number[]
  onGenreClick: (genreId: number) => void
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
const GridCard = ({ production, selectedGenreIds, onGenreClick }: GridCardProps) => {
  const { t, i18n } = useTranslation()
  const language = i18n.language

  const imageSrc = production.media_gallery?.media_items[0]?.crops[0]?.image_url
  const title = getTranslatedRecord(production.title, language, production.display_title)
  const artistName = getTranslatedRecord(
    production.artist_name,
    language,
    production.display_artist_name,
  )
  const dateRangeLabel = getEventDateRangeLabel(production.events, language)
  const locationName = getSharedLocationName(production.events, language)
  const genres = production.genres.filter((genre) => genre.display_name)

  return (
    <Stack
      component={Paper}
      elevation={0}
      direction="column"
      sx={(theme) => ({
        width: '350px',
        overflow: 'hidden',
        border: `1px solid ${theme.palette.divider}`,
        borderRadius: '16px',
        backgroundColor: theme.palette.background.paper,
        textDecoration: 'none',
        color: 'inherit',
        cursor: 'pointer',
        transition: 'box-shadow 0.2s ease',
        '&:hover': {
          boxShadow: theme.shadows[3],
        },
      })}
    >
      <RouterLink
        to={`/productions/${production.id}`}
        style={{ display: 'contents', textDecoration: 'none', color: 'inherit' }}
        aria-label={t('listCard.imageAlt', { title })}
      >
        <ImageWithFallback
          src={imageSrc}
          alt={t('listCard.imageAlt', { title })}
          sx={{
            aspectRatio: '16 / 9',
            objectFit: 'cover',
          }}
        />
      </RouterLink>

      <Stack
        component={RouterLink}
        to={`/productions/${production.id}`}
        direction="column"
        justifyContent="space-between"
        sx={{
          p: 3,
          gap: 1,
          textDecoration: 'none',
          color: 'inherit',
          flex: 1,
        }}
      >
        <Stack spacing={0.75}>
          <Typography component="h2" variant="h5" color="textPrimary" fontWeight="bold">
            {title}
          </Typography>

          {artistName ? (
            <Typography component="p" color="textSecondary">
              {artistName}
            </Typography>
          ) : null}
        </Stack>

        <Stack spacing={1.25}>
          {dateRangeLabel || locationName ? (
            <Stack sx={{ color: 'text.secondary', alignItems: 'flex-start' }}>
              {dateRangeLabel ? (
                <Stack
                  direction="row"
                  spacing={0.75}
                  alignItems="center"
                  sx={{ minWidth: 0, flex: '0 1 auto' }}
                >
                  <DateRangeOutlinedIcon sx={{ fontSize: '1rem', flexShrink: 0 }} />
                  <Typography variant="body2" noWrap sx={{ minWidth: 0 }}>
                    {dateRangeLabel}
                  </Typography>
                </Stack>
              ) : null}

              {locationName ? (
                <Stack
                  direction="row"
                  spacing={0.75}
                  alignItems="center"
                  sx={{ minWidth: 0, flex: '0 1 auto' }}
                >
                  <RoomOutlinedIcon sx={{ fontSize: '1rem', flexShrink: 0 }} />
                  <Typography variant="body2" noWrap sx={{ minWidth: 0 }}>
                    {locationName}
                  </Typography>
                </Stack>
              ) : null}
            </Stack>
          ) : null}

          {genres.length > 0 ? (
            <Stack
              direction="row"
              spacing={0.75}
              sx={{
                borderRadius: '4px',
                flexWrap: 'nowrap',
                minWidth: 0,
                maxWidth: '100%',
                overflowX: 'auto',
                overflowY: 'hidden',
                WebkitOverflowScrolling: 'touch',
                scrollbarWidth: 'none',
                msOverflowStyle: 'none',
                '&::-webkit-scrollbar': { display: 'none' },
              }}
            >
              {production.genres.map((genre) => (
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

export default GridCard
