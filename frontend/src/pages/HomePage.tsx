import { Box, Container, Paper, Stack, Typography } from '@mui/material'
import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useTheme, useMediaQuery } from '@mui/material'
import GenreAndTagChip from '../components/GenreAndTagChip'
import SearchControlsBar from '../components/searchbar/SearchControlsBar'
import { useSearchBarUrlState } from '../components/searchbar/useSearchBarUrlState'
import type { Genre } from '../types/Genres'
import { getTranslatedRecord } from '../utils/translations'

// TODO: use the floatingAlerts when needed

const MOCK_SERIES_TAGS = [
  { id: 1, name: 'Familie', labels: {} },
  { id: 2, name: 'Jong publiek', labels: {} },
  { id: 3, name: 'Premiere', labels: {} },
]

/**
 * Homepage doubles as an interaction playground for all chip contexts.
 */
const HomePage = () => {
  const { t, i18n } = useTranslation()
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const [genres, setGenres] = useState<Genre[]>([])
  const {
    searchValue,
    sortTarget,
    sortDirection,
    viewMode,
    selectedGenreIds,
    selectedSeriesTagIds,
    setSearchValue,
    setSortTarget,
    setSortDirection,
    setViewMode,
    toggleGenreId,
    toggleSeriesTagId,
  } = useSearchBarUrlState({ isMobile })

  useEffect(() => {
    const loadGenres = async () => {
      try {
        const { getGenres } = await import('../services/genres/Genres')
        const response = await getGenres({ pageSize: 20 })
        setGenres(response.results)
      } catch {
        setGenres([])
      }
    }

    loadGenres()
  }, [])

  const genreChips = useMemo(
    () =>
      genres
        .map((genre) => ({
          id: genre.id,
          name: getTranslatedRecord(genre.name, i18n.language, genre.display_name),
          labels: genre.name ?? {},
        }))
        .filter((genre) => Boolean(genre.name)),
    [genres, i18n.language],
  )

  const previewGenreChips = genreChips.slice(0, 4)

  return (
    <Box>
      <Container maxWidth="md" sx={{ py: 6 }}>
        <Paper elevation={3} sx={{ p: 4 }}>
          <Stack spacing={3}>
            <Typography variant="h3" component="h1">
              {t('title')}
            </Typography>
            <Typography variant="subtitle1">{t('subtitle')}</Typography>
          </Stack>
        </Paper>
      </Container>
      <Box
        sx={{
          backgroundColor: theme.palette.mode === 'light' ? '#f8f8f8' : '#1e1e1e',
          pt: 4,
          pb: 6,
          borderBottom: `1px solid ${theme.palette.divider}`,
        }}
      >
        <Box sx={{ width: '75%', mx: 'auto' }}>
          <SearchControlsBar
            placeholder={
              isMobile ? t('searchbar.searchPlaceholderMobile') : t('searchbar.searchPlaceholder')
            }
            searchValue={searchValue}
            onSearchChange={setSearchValue}
            onSearchSubmit={setSearchValue}
            sortTarget={sortTarget}
            onSortTargetChange={setSortTarget}
            sortDirection={sortDirection}
            onSortDirectionChange={setSortDirection}
            viewMode={viewMode}
            onViewModeChange={setViewMode}
            showViewModeToggle={!isMobile}
            genreChips={genreChips}
            seriesTagChips={MOCK_SERIES_TAGS}
            selectedGenreIds={selectedGenreIds}
            selectedSeriesTagIds={selectedSeriesTagIds}
            onGenreChipToggle={toggleGenreId}
            onSeriesTagChipToggle={toggleSeriesTagId}
          />

          <Stack spacing={2} mt={3}>
            <Typography variant="subtitle2" color="text.secondary">
              Chip preview: static, description and series contexts
            </Typography>

            <Stack direction="row" gap={1} flexWrap="wrap">
              {previewGenreChips.map((genreChip) => (
                <GenreAndTagChip
                  key={`static-${genreChip.id}`}
                  name={genreChip.name}
                  labels={genreChip.labels}
                  chipType="genre"
                  context="static"
                  id={genreChip.id}
                  selected={selectedGenreIds.includes(genreChip.id)}
                />
              ))}
              {MOCK_SERIES_TAGS.map((seriesTag) => (
                <GenreAndTagChip
                  key={`static-tag-${seriesTag.id}`}
                  name={seriesTag.name}
                  labels={seriesTag.labels}
                  chipType="seriesTag"
                  context="static"
                  id={seriesTag.id}
                  selected={selectedSeriesTagIds.includes(seriesTag.id)}
                />
              ))}
            </Stack>

            <Stack direction="row" gap={1} flexWrap="wrap">
              <GenreAndTagChip
                name={previewGenreChips[0]?.name ?? 'Genre'}
                labels={previewGenreChips[0]?.labels ?? {}}
                chipType="genre"
                context="description"
                id={previewGenreChips[0]?.id ?? 1}
              />
              <GenreAndTagChip
                name={MOCK_SERIES_TAGS[0].name}
                labels={MOCK_SERIES_TAGS[0].labels}
                chipType="seriesTag"
                context="description"
                id={MOCK_SERIES_TAGS[0].id}
              />
            </Stack>

            <Stack direction="row" gap={1} flexWrap="wrap">
              <GenreAndTagChip
                name="1"
                labels={{ nl: 'Reeks 1', en: 'Series 1' }}
                chipType="seriesTag"
                context="series"
                id="1"
              />
            </Stack>
          </Stack>
        </Box>
      </Box>
    </Box>
  )
}

export default HomePage
