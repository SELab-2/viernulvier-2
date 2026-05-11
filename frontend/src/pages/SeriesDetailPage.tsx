/**
 * Displays detailed information about a specific series (tag),
 * including its metadata, statistics and a chronological list
 * of associated productions grouped by year.
 */

import { Alert, Box, Button, Container, Divider, Stack, Typography } from '@mui/material'
import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Navigate, useLocation, useParams } from 'react-router-dom'

import SeriesDetailPageSkeleton from './SeriesDetailPageSkeleton'
import Breadcrumbs from '../components/production/Breadcrumbs'
import ProductionView from '../components/ProductionView'
import SeriesHeader from '../components/series_details/SeriesHeader'
import SeriesStats from '../components/series_details/SeriesStats'
import { getProductions } from '../services/productions/Productions'
import { getTag } from '../services/tags/Tags'
import { resolveCurrentLanguage, toLocalizedPath } from '../utils/localizedRoutes'
import { getTranslatedRecord } from '../utils/translations'

import type { Production } from '../types/Productions'
import type { Tag } from '../types/Tags'

const PAGE_SIZE = 12

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

type SeriesDetailContentProps = {
  id: string
}

const SeriesDetailContent = ({ id }: SeriesDetailContentProps) => {
  const location = useLocation()
  const { t, i18n } = useTranslation()
  const currentLanguage = resolveCurrentLanguage(
    location.pathname,
    i18n.language,
    i18n.resolvedLanguage,
  )
  const notFoundPath = toLocalizedPath('/not-found', currentLanguage)

  const [seriesTag, setSeriesTag] = useState<Tag | null>(null)
  const [productions, setProductions] = useState<Production[]>([])
  const [totalProductions, setTotalProductions] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [isLoading, setIsLoading] = useState(true)
  const [isLoadingMore, setIsLoadingMore] = useState(false)
  const [error, setError] = useState<SeriesErrorKey>(null)
  const numericId = Number(id)

  useEffect(() => {
    let isActive = true

    const fetchSeries = async () => {
      setIsLoading(true)
      setError(null)
      setProductions([])
      setTotalProductions(0)
      setCurrentPage(1)

      try {
        const [tag, productionsResponse] = await Promise.all([
          getTag(numericId),
          getProductions({ page: 1, pageSize: PAGE_SIZE, filters: { tag: numericId } }),
        ])

        if (!isActive) {
          return
        }

        setSeriesTag(tag)
        setProductions(productionsResponse.results)
        setTotalProductions(productionsResponse.count)
      } catch {
        if (isActive) {
          setError('series.fetchError')
        }
      } finally {
        if (isActive) {
          setIsLoading(false)
        }
      }
    }

    void fetchSeries()

    return () => {
      isActive = false
    }
  }, [numericId])

  const loadMoreProductions = async () => {
    if (isLoadingMore || productions.length >= totalProductions) {
      return
    }

    setIsLoadingMore(true)

    try {
      const nextPage = currentPage + 1
      const productionsResponse = await getProductions({
        page: nextPage,
        pageSize: PAGE_SIZE,
        filters: { tag: numericId },
      })

      setProductions((currentProductions) => [
        ...currentProductions,
        ...productionsResponse.results,
      ])
      setTotalProductions(productionsResponse.count)
      setCurrentPage(nextPage)
    } finally {
      setIsLoadingMore(false)
    }
  }

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

  const startYear = seriesTag?.first_production_start
    ? new Date(seriesTag.first_production_start).getFullYear()
    : null
  const endYear = seriesTag?.last_production_end
    ? new Date(seriesTag.last_production_end).getFullYear()
    : null

  const stats: SeriesStat[] = [
    { value: String(totalProductions), label: t('series.stats.editions') },
    {
      value: startYear && endYear ? `${startYear}–${endYear}` : '—',
      label: t('series.stats.period'),
    },
    { value: seriesTag?.type || '—', label: t('series.stats.type') },
  ]

  if (isLoading) {
    return <SeriesDetailPageSkeleton />
  }
  if (error || !seriesTag) {
    return <Navigate to={notFoundPath} replace />
  }

  const lang = i18n.language.startsWith('en') ? 'en' : 'nl'

  const seriesName =
    getTranslatedRecord(seriesTag.name, lang, seriesTag.display_name) || t('series.untitled')

  const seriesExcerpt =
    getTranslatedRecord(seriesTag.excerpt, lang, seriesTag.display_excerpt) || ''

  const seriesDescription =
    getTranslatedRecord(seriesTag.short_description, lang, seriesTag.display_short_description) ||
    t('series.noDescription')
  const hasMoreProductions = sortedProductions.length < totalProductions

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

        <SeriesHeader name={seriesName} excerpt={seriesExcerpt} description={seriesDescription} />
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

              {hasMoreProductions && (
                <Box sx={{ pl: { xs: 3, md: 12 } }}>
                  <Button variant="outlined" onClick={loadMoreProductions} disabled={isLoadingMore}>
                    {isLoadingMore ? t('common.loading', 'Loading…') : t('series.showMore')}
                  </Button>
                </Box>
              )}
            </Stack>
          </Box>
        )}
      </Stack>
    </Container>
  )
}

const SeriesDetailPage = () => {
  const location = useLocation()
  const { i18n } = useTranslation()
  const { id } = useParams<{ id: string }>()
  const currentLanguage = resolveCurrentLanguage(
    location.pathname,
    i18n.language,
    i18n.resolvedLanguage,
  )
  const notFoundPath = toLocalizedPath('/not-found', currentLanguage)

  if (!id || Number.isNaN(Number(id))) {
    return <Navigate to={notFoundPath} replace />
  }

  return <SeriesDetailContent key={id} id={id} />
}

export default SeriesDetailPage
