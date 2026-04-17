/**
 * Displays detailed information about a specific series (tag),
 * including its metadata, statistics and a chronological list
 * of associated productions grouped by year.
 */

import { Alert, Box, Container, Divider, Stack, Typography } from '@mui/material'
import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Navigate, useParams } from 'react-router-dom'

import Breadcrumbs from '../components/production/Breadcrumbs'
import ProductionView from '../components/ProductionView'
import SeriesHeader from '../components/series_details/SeriesHeader'
import SeriesStats from '../components/series_details/SeriesStats'
import { getProductions } from '../services/productions/Productions'
import { getTag } from '../services/tags/Tags'
import { getTranslatedRecord } from '../utils/translations'
import SeriesDetailPageSkeleton from './SeriesDetailPageSkeleton'

import type { Production } from '../types/Productions'
import type { Tag } from '../types/Tags'

type SeriesStat = {
  value: string
  label: string
}

type SeriesErrorKey = 'series.invalidId' | 'series.fetchError' | null

/** Extracts the display year from a production based on its event dates. */
function getProductionYear(production: Production): string {
  if (production.first_event_start) {
    return new Date(production.first_event_start).getFullYear().toString()
  }
  if (production.last_event_end) {
    return new Date(production.last_event_end).getFullYear().toString()
  }
  return '—'
}

function buildProductionMeta(production: Production, language: string): string {
  const primaryGenre = production.genres?.[0]?.display_name ?? ''
  const parts = [
    getLocalizedRecordValue(production.artist_name, language),
    production.uit_database_type?.name ?? '',
    primaryGenre,
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

const SeriesDetailPage = () => {
  const { id } = useParams<{ id: string }>()
  const { t, i18n } = useTranslation()

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
          getProductions({ pageSize: 100, filters: { tag: numericId } }),
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

  /** Sorted most-recent first by start date; productions without a date fall to the end. */
  const sortedProductions = useMemo(
    () =>
      [...productions].sort((a, b) => {
        if (a.first_event_start && b.first_event_start) {
          return new Date(b.first_event_start).getTime() - new Date(a.first_event_start).getTime()
        }
        if (a.first_event_start) {
          return -1
        }
        if (b.first_event_start) {
          return 1
        }
        return b.id - a.id
      }),
    [productions],
  )

  /** Productions grouped by year in display order, preserving sort within each group. */
  const productionsByYear = useMemo(() => {
    const groups = new Map<string, Production[]>()
    for (const production of sortedProductions) {
      const year = getProductionYear(production)
      const existing = groups.get(year)
      if (existing) {
        existing.push(production)
      } else {
        groups.set(year, [production])
      }
    }
    return Array.from(groups.entries())
  }, [sortedProductions])

  const stats = useMemo<SeriesStat[]>(() => {
    const years = sortedProductions
      .map(getProductionYear)
      .filter((year) => /^\d{4}$/.test(year))
      .map(Number)

    const minYear = years.length ? Math.min(...years) : null
    const maxYear = years.length ? Math.max(...years) : null

    return [
      { value: String(sortedProductions.length), label: t('series.stats.editions') },
      {
        value: minYear && maxYear ? `${minYear}–${maxYear}` : '—',
        label: t('series.stats.period'),
      },
      { value: seriesTag?.type || '—', label: t('series.stats.type') },
    ]
  }, [seriesTag?.type, sortedProductions, t])

  if (isLoading) {
    return <SeriesDetailPageSkeleton />
  }
  if (error || !seriesTag) {
    return <Navigate to="/404" replace />
  }

  const lang = i18n.language.startsWith('en') ? 'en' : 'nl'

  const seriesName =
    getTranslatedRecord(seriesTag.name, lang, seriesTag.display_name) || t('series.untitled')

  const seriesDescription =
    getTranslatedRecord(seriesTag.short_description, lang, seriesTag.display_short_description) ||
    t('series.noDescription')

  return (
    <Container maxWidth="lg" sx={{ py: 5 }}>
      <Stack spacing={4}>
        <Breadcrumbs
          items={[
            { label: t('nav.home'), to: '/' },
            { label: t('footer.nav.series'), to: '/series' },
            { label: seriesName },
          ]}
        />

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
          <Box sx={{ position: 'relative' }}>
            <Box
              sx={{
                position: 'absolute',
                left: '5px',
                top: 0,
                bottom: 0,
                width: '1px',
                bgcolor: 'divider',
              }}
            />

            <Stack spacing={4}>
              {productionsByYear.map(([year, yearProductions]) => (
                <Stack
                  key={year}
                  direction={{ xs: 'column', md: 'row' }}
                  spacing={2}
                  sx={{ alignItems: { md: 'flex-start' } }}
                >
                  {/* Year marker — dot sits on top of the timeline line */}
                  <Stack
                    direction="row"
                    spacing={1}
                    sx={{ alignItems: 'center', flexShrink: 0, width: { md: 80 } }}
                  >
                    <Box
                      sx={{
                        width: 10,
                        height: 10,
                        borderRadius: '50%',
                        bgcolor: 'text.primary',
                        flexShrink: 0,
                        position: 'relative',
                        zIndex: 1,
                      }}
                    />
                    <Typography variant="body2" color="text.secondary">
                      {year}
                    </Typography>
                  </Stack>

                  <Box
                    sx={{
                      flex: 1,
                      minWidth: 0,
                      maxWidth: { xs: 400, md: 'none' },
                      pl: { xs: 3, md: 0 },
                    }}
                  >
                    <ProductionView productions={yearProductions} layout="list" />
                  </Box>
                </Stack>
              ))}
            </Stack>
          </Box>
        )}
      </Stack>
    </Container>
  )
}

export default SeriesDetailPage
