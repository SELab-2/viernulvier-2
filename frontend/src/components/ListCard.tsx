import DateRangeOutlinedIcon from '@mui/icons-material/DateRangeOutlined'
import RoomOutlinedIcon from '@mui/icons-material/RoomOutlined'
import { Box, Button, Paper, Stack, Typography } from '@mui/material'
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
  eventId?: number | null
  hall?: Hall | null
  starts_at?: string | null
  selectedGenreIds: number[]
  onGenreClick: (genreId: number) => void
}

const ListCard = ({
  production,
  eventId,
  hall,
  starts_at,
  selectedGenreIds,
  onGenreClick,
}: ListCardProps) => {
  const { t, i18n } = useTranslation()
  const language = i18n.language

  // TODO: Add image src
  const imageSrc = null
  const title = getTranslatedRecord(production.title, language, production.display_title)
  const artistName = getTranslatedRecord(
    production.artist_name,
    language,
    production.display_artist_name,
  )

  return (
    <Paper
      elevation={0}
      sx={(theme) => ({
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'stretch',
        height: 175,
        gap: 3,
        p: 3,
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
        }}
      />

      <Box
        sx={{
          flex: 1,
          minWidth: 0,
          alignSelf: 'stretch',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
        }}
      >
        <Stack spacing={0.75} sx={{ minWidth: 0 }}>
          <Typography
            component="h2"
            variant="h5"
            noWrap
            sx={(theme) => ({
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              color: theme.palette.text.primary,
              fontWeight: 'bold',
            })}
          >
            {title}
          </Typography>

          {artistName ? (
            <Typography
              component="p"
              noWrap
              sx={(theme) => ({
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                color: theme.palette.text.secondary,
              })}
            >
              {artistName}
            </Typography>
          ) : null}
        </Stack>

        <Stack spacing={1.25}>
          <Stack
            direction="row"
            spacing={1.5}
            sx={(theme) => ({ color: theme.palette.text.secondary })}
          >
            {starts_at ? (
              <Stack direction="row" spacing={0.75} alignItems="center">
                <DateRangeOutlinedIcon sx={{ fontSize: '1rem' }} />
                <Typography
                  variant="body2"
                  noWrap
                  sx={{ overflow: 'hidden', textOverflow: 'ellipsis' }}
                >
                  {formatDate(starts_at, language)}
                </Typography>
              </Stack>
            ) : null}

            {hall ? (
              <Stack direction="row" spacing={0.75} alignItems="center">
                <RoomOutlinedIcon sx={{ fontSize: '1rem' }} />
                <Typography
                  variant="body2"
                  noWrap
                  sx={{ overflow: 'hidden', textOverflow: 'ellipsis' }}
                >
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
                overflow: 'hidden',
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
      </Box>

      <Button
        component={RouterLink}
        to={eventId ? `/events/${eventId}` : `/productions/${production.id}`}
        variant="outlined"
        sx={(theme) => ({
          alignSelf: 'center',
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
    </Paper>
  )
}

export default ListCard
