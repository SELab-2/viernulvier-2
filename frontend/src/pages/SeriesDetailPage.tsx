/**
 * Displays detailed information about a specific series (tag),
 * including its metadata, statistics and a chronological list
 * of associated productions.
 */

import { useEffect, useMemo, useState } from 'react'
import { Alert, Box, Button, Container, Divider, Stack, Typography } from '@mui/material'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import { Navigate, useNavigate, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import SeriesHeader from '../components/series_details/SeriesHeader'
import SeriesStats from '../components/series_details/SeriesStats'
import ProductionCard from '../components/series_details/ProductionCard'
import TimelineItem from '../components/series_details/TimelineItem'
import SeriesDetailBreadcrumbs from '../components/series_details/Breadcrumbs'

import { getTag } from '../services/tags/Tags'
import { getProductions } from '../services/productions/Productions'
import type { Tag } from '../types/Tags'
import type { Production } from '../types/Productions'
import LoadingSpinner from '../components/LoadingSpinner'

type SeriesStat = {
  value: string
  label: string
}

function getLocalizedRecordValue(
  value: Record<string, string> | null | undefined,
  language: string,
  fallback = '',
): string {
  if (!value) return fallback

  const normalizedLanguage = language.startsWith('en') ? 'en' : 'nl'

  return value[normalizedLanguage] ?? value.en ?? value.nl ?? Object.values(value)[0] ?? fallback
}

function extractYearFromProduction(production: Production): string {
  if (production.first_event_start) {
    return new Date(production.first_event_start).getFullYear().toString()
  }
  if (production.last_event_end) {
    return new Date(production.last_event_end).getFullYear().toString()
  }
  const candidates = [production.display_title, ...Object.values(production.title ?? {})].filter(
    Boolean,
  ) as string[]

  for (const candidate of candidates) {
    const match = candidate.match(/\b(19|20)\d{2}\b/)
    if (match) return match[0]
  }

  return '—'
}

function buildProductionMeta(production: Production, language: string): string {
  const parts = [
    getLocalizedRecordValue(production.artist_name, language),
    production.uit_database_type?.name ?? '',
    production.uit_database_theme?.name ?? '',
  ].filter(Boolean)

  return parts.join(' · ')
}

function buildProductionDescription(production: Production, language: string): string {
  return (
    getLocalizedRecordValue(production.teaser, language) ||
    getLocalizedRecordValue(production.description, language) ||
    ''
  )
}

// TODO: use production images in production cards. This is just a placeholder for the moment.
//function buildProductionImage(_production: Production): string {
//  return ''
//}

const SeriesDetailPage = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { t, i18n } = useTranslation()

  const [seriesTag, setSeriesTag] = useState<Tag | null>(null)
  const [productions, setProductions] = useState<Production[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const numericId = Number(id)

    if (!numericId || Number.isNaN(numericId)) {
      setError(t('series.invalidId'))
      setIsLoading(false)
      return
    }

    const fetchSeries = async () => {
      try {
        setIsLoading(true)
        setError(null)

        const [tag, productionsResponse] = await Promise.all([
          getTag(numericId),
          getProductions({
            pageSize: 100,
            filters: {
              tag: numericId,
            },
          }),
        ])

        setSeriesTag(tag)
        setProductions(productionsResponse.results)
      } catch {
        setError(t('series.fetchError'))
      } finally {
        setIsLoading(false)
      }
    }

    void fetchSeries()
  }, [id, t])

  const sortedProductions = useMemo(() => {
    return [...productions].sort((a, b) => {
      const yearA = Number(extractYearFromProduction(a))
      const yearB = Number(extractYearFromProduction(b))

      if (Number.isNaN(yearA) && Number.isNaN(yearB)) return b.id - a.id
      if (Number.isNaN(yearA)) return 1
      if (Number.isNaN(yearB)) return -1

      return yearB - yearA
    })
  }, [productions])

  const stats = useMemo<SeriesStat[]>(() => {
    const years = sortedProductions
      .map((production) => extractYearFromProduction(production))
      .filter((year) => /^\d{4}$/.test(year))
      .map(Number)

    const minYear = years.length ? Math.min(...years) : null
    const maxYear = years.length ? Math.max(...years) : null

    return [
      {
        value: String(sortedProductions.length),
        label: t('series.stats.editions'),
      },
      {
        value: minYear && maxYear ? `${minYear}–${maxYear}` : '—',
        label: t('series.stats.period'),
      },
      {
        value: seriesTag?.type || '—',
        label: t('series.stats.type'),
      },
    ]
  }, [seriesTag?.type, sortedProductions, t])

  if (isLoading) {
    return <LoadingSpinner label={t('series.loading')} fullScreen />
  }

  if (error || !seriesTag) {
    return <Navigate to="/404" replace />
  }

  const seriesName =
    getLocalizedRecordValue(seriesTag.name, i18n.language) ||
    seriesTag.display_name ||
    t('series.untitled')

  const seriesDescription =
    getLocalizedRecordValue(seriesTag.short_description, i18n.language) ||
    seriesTag.display_short_description ||
    t('series.noDescription')

  return (
    <Container
      maxWidth="lg"
      sx={{
        py: { xs: 3, md: 5 },
        px: { xs: 2, sm: 3 },
        overflowX: 'hidden',
      }}
    >
      <Stack spacing={4}>
        <Stack spacing={2}>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/series')}
            sx={{ alignSelf: 'flex-start' }}
          >
            {t('series.backToSeries')}
          </Button>

          <SeriesDetailBreadcrumbs
            items={[
              { label: t('nav.home'), to: '/' },
              { label: t('footer.nav.series'), to: '/series' },
              { label: seriesName },
            ]}
          />
        </Stack>

        <SeriesHeader name={seriesName} description={seriesDescription} />

        <SeriesStats stats={stats} />

        <Divider />

        <Stack spacing={1}>
          <Typography variant="h4" component="h2" sx={{ fontWeight: 700 }}>
            {t('series.allEditions')}
          </Typography>

          <Typography variant="body2" color="text.secondary">
            {t('series.allEditionsSubtitle')}
          </Typography>
        </Stack>

        {sortedProductions.length === 0 ? (
          <Alert severity="info" variant="outlined">
            {t('series.noProductions')}
          </Alert>
        ) : (
          <Stack spacing={4} sx={{ position: 'relative', pl: { xs: 0, md: 3 } }}>
            <Box
              sx={{
                position: 'absolute',
                left: 11,
                top: 10,
                bottom: 10,
                width: '1px',
                bgcolor: 'divider',
                display: { xs: 'none', md: 'block' },
              }}
            />

            {sortedProductions.map((production) => (
              <TimelineItem key={production.id} year={extractYearFromProduction(production)}>
                <ProductionCard
                  title={
                    production.display_title ||
                    getLocalizedRecordValue(production.title, i18n.language) ||
                    t('series.untitledProduction')
                  }
                  meta={buildProductionMeta(production, i18n.language)}
                  description={buildProductionDescription(production, i18n.language)}
                  tags={production.tags.map(
                    (tag) => tag.display_name || getLocalizedRecordValue(tag.name, i18n.language),
                  )}
                  //image={buildProductionImage(production)}
                />
              </TimelineItem>
            ))}
          </Stack>
        )}
      </Stack>
    </Container>
  )
}

export default SeriesDetailPage
