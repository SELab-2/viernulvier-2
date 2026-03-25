import DateRangeOutlinedIcon from '@mui/icons-material/DateRangeOutlined'
import RoomOutlinedIcon from '@mui/icons-material/RoomOutlined'
import { Button, Paper, Stack, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Link as RouterLink } from 'react-router-dom'
import type { Hall } from '../types/Halls'
import type { Production } from '../types/Productions'
import { formatDate } from '../utils/formatDate'
import getLocationName from '../utils/locations'
import { getTranslatedRecord } from '../utils/translations'
import GenreChip from './GenreChip'
import ImageWithFallback from './ImageWithFallback'

export interface ListCardProps {
  production: Production
  pathname: string
  hall?: Hall | null
  startsAt?: string | null
  selectedGenreIds: number[]
  onGenreClick: (genreId: number) => void
}

/**
 * Horizontal card for a {@link Production} or {@link Event}: image, title, artist, optional date and venue,
 * genre filters, and a link to the detail route.
 *
 * Text is resolved with the active i18n locale via {@link getTranslatedRecord}. The image uses the
 * first crop of the first gallery image when present; otherwise {@link ImageWithFallback} shows the
 * branded placeholder.
 *
 * @param props.production Full API payload (title, artist, media gallery, genres, etc.).
 * @param props.pathname Client route for the view button (e.g. production or event detail path).
 * @param props.hall Optional {@link Hall}; when set, shows a venue line via {@link getLocationName}.
 * @param props.startsAt Optional ISO start time for the listing; falsy values hide the date row.
 * @param props.selectedGenreIds Genre ids selected in parent filter state (drives chip style).
 * @param props.onGenreClick Called with a genre id when that chip is pressed.
 * @returns The list row element.
 */
const ListCard = ({
  production,
  pathname,
  hall,
  startsAt,
  selectedGenreIds,
  onGenreClick,
}: ListCardProps) => {
  const { t, i18n } = useTranslation()
  const language = i18n.language

  const imageSrc = production.media_gallery?.media_items[0]?.crops[0]?.image_url
  const title = getTranslatedRecord(production.title, language, production.display_title)
  const artistName = getTranslatedRecord(
    production.artist_name,
    language,
    production.display_artist_name,
  )

  return (
    <Stack
      component={Paper}
      elevation={0}
      direction="row"
      alignItems="stretch"
      sx={(theme) => ({
        height: 175,
        gap: 3,
        p: 3,
        minWidth: 0,
        overflow: 'hidden',
        border: `1px solid ${theme.palette.divider}`,
        borderRadius: '4px',
        backgroundColor: theme.palette.background.paper,
      })}
    >
      <ImageWithFallback
        src={imageSrc}
        alt={t('listCard.imageAlt', { title })}
        sx={{
          aspectRatio: 5 / 3,
          borderRadius: '4px',
          flexShrink: 0,
          alignSelf: 'stretch',
          height: '100%',
          objectFit: 'cover',
        }}
      />

      <Stack
        direction="column"
        justifyContent="space-between"
        sx={{ flex: 1, minWidth: 0, overflow: 'hidden', alignSelf: 'stretch' }}
      >
        <Stack spacing={0.75}>
          <Typography component="h2" variant="h5" color="textPrimary" fontWeight="bold" noWrap>
            {title}
          </Typography>

          {artistName ? (
            <Typography component="p" color="textSecondary" noWrap>
              {artistName}
            </Typography>
          ) : null}
        </Stack>

        <Stack spacing={1.25}>
          <Stack
            direction="row"
            spacing={1.5}
            sx={{ color: 'text.secondary', justifyContent: 'flex-start', alignItems: 'center' }}
          >
            {startsAt ? (
              <Stack
                direction="row"
                spacing={0.75}
                alignItems="center"
                sx={{ minWidth: 0, flex: '0 1 auto' }}
              >
                <DateRangeOutlinedIcon sx={{ fontSize: '1rem', flexShrink: 0 }} />
                <Typography variant="body2" noWrap sx={{ minWidth: 0 }}>
                  {formatDate(startsAt, language)}
                </Typography>
              </Stack>
            ) : null}

            {hall ? (
              <Stack
                direction="row"
                spacing={0.75}
                alignItems="center"
                sx={{ minWidth: 0, flex: '0 1 auto' }}
              >
                <RoomOutlinedIcon sx={{ fontSize: '1rem', flexShrink: 0 }} />
                <Typography variant="body2" noWrap sx={{ minWidth: 0 }}>
                  {getLocationName(hall, language)}
                </Typography>
              </Stack>
            ) : null}
          </Stack>

          {production.genres.length > 0 ? (
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

      <Button
        component={RouterLink}
        to={pathname}
        variant="outlined"
        sx={(theme) => ({
          alignSelf: 'center',
          flexShrink: 0,
          px: 3,
          borderColor: theme.palette.divider,
          borderRadius: '4px',
          color: theme.palette.text.primary,
          backgroundColor: theme.palette.background.paper,
          textTransform: 'none',
        })}
      >
        {t('listCard.view')} →
      </Button>
    </Stack>
  )
}

export default ListCard
