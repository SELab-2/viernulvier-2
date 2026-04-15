/**
 * Displays detailed information about a specific series (tag),
 * including its metadata, statistics and a chronological list
 * of associated productions.
 */

import {
  Alert,
  Box,
  Container,
  Divider,
  Stack,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material'
import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Navigate, useParams } from 'react-router-dom'

import SeriesDetailPageSkeleton from './SeriesDetailPageSkeleton'
import Breadcrumbs from '../components/production/Breadcrumbs'
import ProductionGridCard from '../components/productions/ProductionGridCard'
import ProductionListCard from '../components/productions/ProductionListCard'
import SeriesHeader from '../components/series_details/SeriesHeader'
import SeriesStats from '../components/series_details/SeriesStats'
import TimelineItem, { DOT_CENTER_X } from '../components/series_details/TimelineItem'
import { getProductions } from '../services/productions/Productions'
import { getTag } from '../services/tags/Tags'

import type { Production } from '../types/Productions'
import type { Tag } from '../types/Tags'

type SeriesStat = {
  value: string
  label: string
}

type SeriesErrorKey = 'series.invalidId' | 'series.fetchError' | null

function getLocalizedRecordValue(
  value: Record<string, string> | null | undefined,
  language: string,
  fallback = '',
): string {
  if (!value) {
    return fallback
  }

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
    if (match) {
      return match[0]
    }
  }

  return '—'
}

const SeriesDetailPage = () => {
  const { id } = useParams<{ id: string }>()
  const { t, i18n } = useTranslation()
  const theme = useTheme()
  const isSmallViewport = useMediaQuery(theme.breakpoints.down('md'))

  const [seriesTag, setSeriesTag] = useState<Tag | null>(null)
  const [productions, setProductions] = useState<Production[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<SeriesErrorKey>(null)

  useEffect(() => {
    const numericId = Number(id)

    if (!numericId || Number.isNaN(numericId)) {
      setError('series.invalidId')
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
        setError('series.fetchError')
      } finally {
        setIsLoading(false)
      }
    }

    void fetchSeries()
  }, [id])

  const sortedProductions = useMemo(() => {
    return [...productions].sort((a, b) => {
      const yearA = Number(extractYearFromProduction(a))
      const yearB = Number(extractYearFromProduction(b))

      if (Number.isNaN(yearA) && Number.isNaN(yearB)) {
        return b.id - a.id
      }
      if (Number.isNaN(yearA)) {
        return 1
      }
      if (Number.isNaN(yearB)) {
        return -1
      }

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
    return <SeriesDetailPageSkeleton />
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
          <Breadcrumbs
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

        <Stack spacing={1} sx={{ textAlign: { xs: 'center', md: 'left' } }}>
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
          <Box sx={{ position: 'relative' }}>
            <Box
              sx={{
                position: 'absolute',
                left: { md: DOT_CENTER_X },
                top: { md: DOT_CENTER_X },
                bottom: 0,
                width: '1px',
                bgcolor: 'divider',
                display: { xs: 'none', md: 'block' },
              }}
            />

            <Stack spacing={2}>
              {sortedProductions.map((production, index) => {
                const year = extractYearFromProduction(production)
                const prevYear =
                  index > 0 ? extractYearFromProduction(sortedProductions[index - 1]!) : null
                const showYearLabel = year !== prevYear

                return (
                  <TimelineItem key={production.id} year={year} showYearLabel={showYearLabel}>
                    {isSmallViewport ? (
                      <Box
                        sx={{
                          display: 'flex',
                          justifyContent: 'center',
                          width: '100%',
                          '& > a': {
                            width: '100%',
                            maxWidth: 350,
                          },
                        }}
                      >
                        <ProductionGridCard production={production} />
                      </Box>
                    ) : (
                      <ProductionListCard production={production} />
                    )}
                  </TimelineItem>
                )
              })}
            </Stack>
          </Box>
        )}
      </Stack>
    </Container>
  )
}

export default SeriesDetailPage
