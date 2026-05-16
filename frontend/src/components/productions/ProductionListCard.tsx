import ArrowForwardOutlinedIcon from '@mui/icons-material/ArrowForwardOutlined'
import DateRangeOutlinedIcon from '@mui/icons-material/DateRangeOutlined'
import { Box, Stack, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { useLocation, useNavigate } from 'react-router-dom'

import { tokens } from '../../theme/tokens'
import { getProductionDateLabel } from '../../utils/dateUtils'
import { resolveCurrentLanguage, toLocalizedPath } from '../../utils/localizedRoutes'
import { getTranslatedRecord } from '../../utils/translations'
import GenreAndTagChip from '../chips/GenreAndTagChip'
import ImageWithFallback from '../ImageWithFallback'

import type { Production } from '../../types/Productions'

export interface ProductionListCardProps {
  production: Production
  selectedGenreIds?: number[]
  selectedTagIds?: number[]
}

/**
 * Horizontal card for a {@link Production} or {@link Event}: image, title, artist, optional date and venue,
 * genre filters, and a full-card link to the detail route (genre chips stay separate filters).
 *
 * Text is resolved with the active i18n locale via {@link getTranslatedRecord}. The image uses the
 * first crop of the first gallery image when present; otherwise {@link ImageWithFallback} shows the
 * branded placeholder.
 *
 * Genre chips use `context="static"` (non-interactive) whenever `selectedGenreIds` is defined,
 * so that genre filtering is controlled exclusively by the parent rather than navigating away.
 *
 * @param props.production Full API payload (title, artist, media gallery, genres, events, etc.).
 * @param props.selectedGenreIds Genre ids selected in parent filter state (drives chip style).
 * @returns The list row element.
 */
const ProductionListCard = ({
  production,
  selectedGenreIds,
  selectedTagIds,
}: ProductionListCardProps) => {
  const { i18n, t } = useTranslation()
  const location = useLocation()
  const navigate = useNavigate()
  const { language } = i18n
  const currentLanguage = resolveCurrentLanguage(
    location.pathname,
    i18n.language,
    i18n.resolvedLanguage,
  )
  const detailPath = toLocalizedPath(`/productions/${production.id}`, currentLanguage)

  const imageSrc = production.media_gallery?.media_items[0]?.crops[0]?.image_url
  const title =
    getTranslatedRecord(production.title, language, production.display_title) ||
    t('productions.detail.unknownProduction', 'Unknown production')
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
  const genres = production.genres
    .filter((genre) => genre.display_name)
    .sort((a, b) => {
      const aSelected = selectedGenreIds?.includes(a.id) ? 1 : 0
      const bSelected = selectedGenreIds?.includes(b.id) ? 1 : 0
      return bSelected - aSelected
    })
  const tags = production.tags
    .filter((tag) => tag.display_name || tag.name || tag.url_title)
    .sort((a, b) => {
      const aSelected = selectedTagIds?.includes(a.id) ? 1 : 0
      const bSelected = selectedTagIds?.includes(b.id) ? 1 : 0
      return bSelected - aSelected
    })

  return (
    <Stack
      direction="row"
      role="link"
      tabIndex={0}
      data-to={detailPath}
      onClick={() => {
        navigate(detailPath)
      }}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault()
          navigate(detailPath)
        }
      }}
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
        cursor: 'pointer',
        '&:hover': {
          boxShadow: theme.shadows[3],
        },
      })}
    >
      <ImageWithFallback
        src={imageSrc}
        alt={title}
        sx={{ height: '100%', aspectRatio: 16 / 9, borderRadius: tokens.borderRadius.sm }}
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

          <Box onClick={(e) => e.stopPropagation()}>
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
                  context="series"
                  id={tag.id}
                  selected={selectedTagIds?.includes(tag.id) || false}
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
                  context={selectedGenreIds !== undefined ? 'static' : 'description'}
                  id={genre.id}
                  selected={selectedGenreIds?.includes(genre.id) || false}
                />
              ))}
            </Stack>
          </Box>
        </Stack>
      </Stack>

      <Box sx={{ alignSelf: 'center', pr: 2 }}>
        <ArrowForwardOutlinedIcon color="action" />
      </Box>
    </Stack>
  )
}

export default ProductionListCard
