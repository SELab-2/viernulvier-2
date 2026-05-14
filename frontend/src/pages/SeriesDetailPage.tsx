/**
 * Displays detailed information about a specific series (tag),
 * including its metadata, statistics and a chronological list
 * of associated productions grouped by year.
 */

import { Alert, Box, Button, Container, Divider, Stack, Typography } from '@mui/material'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Navigate, useLocation, useNavigate, useParams } from 'react-router-dom'

import SeriesDetailPageSkeleton from './SeriesDetailPageSkeleton'
import Breadcrumbs from '../components/production/Breadcrumbs'
import ProductionView from '../components/ProductionView'
import SeriesHeader from '../components/series_details/SeriesHeader'
import SeriesStats from '../components/series_details/SeriesStats'
import { ApiError } from '../services/ApiTypes'
import { getProductions } from '../services/productions/Productions'
import { getTag } from '../services/tags/Tags'
import { ALERT_SEVERITIES } from '../types/FloatingAlertConfig'
import { resolveCurrentLanguage, toLocalizedPath } from '../utils/localizedRoutes'
import { createFloatingAlertState } from '../utils/navigation'
import { getTranslatedRecord } from '../utils/translations'

import type { Production } from '../types/Productions'
import type { Tag } from '../types/Tags'

const PAGE_SIZE = 12
const SERIES_PRODUCTIONS_ORDERING = '-first_event_start'

type SeriesStat = {
  value: string
  label: string
}

type SeriesErrorKey = 'series.invalidId' | 'series.fetchError' | null

type ProductionYearGroup = {
  year: number
  productions: Production[]
}

type SeriesDetailContentProps = {
  id: string
}

const getProductionDateTimestamp = (production: Production): number => {
  const date = production.first_event_start ?? production.last_event_end
  return date ? new Date(date).getTime() : Number.NEGATIVE_INFINITY
}

const sortProductionsByDateDesc = (productions: Production[]): Production[] =>
  [...productions].sort((a, b) => {
    const dateDifference = getProductionDateTimestamp(b) - getProductionDateTimestamp(a)

    if (dateDifference !== 0) {
      return dateDifference
    }

    return b.id - a.id
  })

const getProductionYear = (production: Production): number | null => {
  const date = production.first_event_start ?? production.last_event_end

  if (!date) {
    return null
  }

  const year = new Date(date).getFullYear()
  return Number.isNaN(year) ? null : year
}

const groupProductionsByYear = (productions: Production[]): ProductionYearGroup[] => {
  const groupedProductions = new Map<number, Production[]>()

  sortProductionsByDateDesc(productions).forEach((production) => {
    const year = getProductionYear(production)

    if (year === null) {
      return
    }

    groupedProductions.set(year, [...(groupedProductions.get(year) ?? []), production])
  })

  return Array.from(groupedProductions.entries())
    .sort(([yearA], [yearB]) => yearB - yearA)
    .map(([year, yearProductions]) => ({ year, productions: yearProductions }))
}

const SeriesDetailContent = ({ id }: SeriesDetailContentProps) => {
  const location = useLocation()
  const navigate = useNavigate()
  const { t, i18n } = useTranslation()
  const currentLanguage = resolveCurrentLanguage(
    location.pathname,
    i18n.language,
    i18n.resolvedLanguage,
  )
  const seriesPath = toLocalizedPath('/series', currentLanguage)
  const notFoundPath = toLocalizedPath('/not-found', currentLanguage)
  const currentPath = location.pathname

  const [seriesTag, setSeriesTag] = useState<Tag | null>(null)
  const [seriesProductions, setSeriesProductions] = useState<Production[]>([])
  const [totalProductions, setTotalProductions] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [isLoading, setIsLoading] = useState(true)
  const [isLoadingMore, setIsLoadingMore] = useState(false)
  const [error, setError] = useState<SeriesErrorKey>(null)
  const numericId = Number(id)

  const showRateLimitAlert = useCallback(
    (rateLimitError: ApiError, fallbackPath = seriesPath) => {
      const alertMessage =
        Number(rateLimitError.message) === 429
          ? String(rateLimitError.status)
          : rateLimitError.message
      navigate(fallbackPath, {
        replace: true,
        state: createFloatingAlertState({
          message: alertMessage,
          severity: ALERT_SEVERITIES.warning,
        }),
      })
    },
    [navigate, seriesPath],
  )

  useEffect(() => {
    let isActive = true

    const fetchSeries = async () => {
      setIsLoading(true)
      setError(null)
      setSeriesProductions([])
      setTotalProductions(0)
      setCurrentPage(1)

      try {
        const [tag, productionsResponse] = await Promise.all([
          getTag(numericId),
          getProductions({
            page: 1,
            pageSize: PAGE_SIZE,
            filters: {
              tag: numericId,
              ordering: SERIES_PRODUCTIONS_ORDERING,
            },
          }),
        ])

        if (!isActive) {
          return
        }

        setSeriesTag(tag)
        setSeriesProductions(sortProductionsByDateDesc(productionsResponse.results ?? []))
        setTotalProductions(productionsResponse.count ?? productionsResponse.results?.length ?? 0)
        setCurrentPage(1)
      } catch (error: unknown) {
        if (!isActive) {
          return
        }

        if (error instanceof ApiError && (error.status === 429 || Number(error.message) === 429)) {
          isActive = false
          showRateLimitAlert(error)
          return
        }

        setError('series.fetchError')
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
  }, [numericId, showRateLimitAlert])

  const loadMoreProductions = async () => {
    if (isLoadingMore || seriesProductions.length >= totalProductions) {
      return
    }

    setIsLoadingMore(true)

    try {
      const nextPage = currentPage + 1
      const response = await getProductions({
        page: nextPage,
        pageSize: PAGE_SIZE,
        filters: {
          tag: numericId,
          ordering: SERIES_PRODUCTIONS_ORDERING,
        },
      })

      setSeriesProductions((currentProductions) =>
        sortProductionsByDateDesc([...currentProductions, ...(response.results ?? [])]),
      )
      setTotalProductions(response.count ?? totalProductions)
      setCurrentPage(nextPage)
    } catch (error: unknown) {
      if (error instanceof ApiError && (error.status === 429 || Number(error.message) === 429)) {
        showRateLimitAlert(error, currentPath)
      }
    } finally {
      setIsLoadingMore(false)
    }
  }

  const productionsByYear = useMemo(
    () => groupProductionsByYear(seriesProductions),
    [seriesProductions],
  )

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
    return (
      <Navigate
        to={notFoundPath}
        replace
        state={createFloatingAlertState({
          message: t(error ?? 'series.fetchError'),
          severity: ALERT_SEVERITIES.error,
        })}
      />
    )
  }

  const lang = i18n.language.startsWith('en') ? 'en' : 'nl'

  const seriesName =
    getTranslatedRecord(seriesTag.name, lang, seriesTag.display_name) || t('series.untitled')

  const seriesExcerpt =
    getTranslatedRecord(seriesTag.excerpt, lang, seriesTag.display_excerpt) || ''

  const seriesDescription =
    getTranslatedRecord(seriesTag.short_description, lang, seriesTag.display_short_description) ||
    t('series.noDescription')

  const selectedTagIds = seriesTag ? [seriesTag.id] : undefined
  const hasMoreProductions = seriesProductions.length < totalProductions

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

        {productionsByYear.length === 0 ? (
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
              {productionsByYear.map(({ year, productions }) => (
                <Stack
                  key={year}
                  direction={{ xs: 'column', md: 'row' }}
                  spacing={2}
                  sx={{ alignItems: { md: 'flex-start' } }}
                >
                  {/* Year marker — dot on timeline + bold year label */}
                  <Stack
                    direction="row"
                    spacing={1.5}
                    sx={{
                      alignItems: 'center',
                      flexShrink: 0,
                      width: { md: 88 },
                    }}
                  >
                    <Box
                      sx={{
                        width: 12,
                        height: 12,
                        borderRadius: '50%',
                        bgcolor: 'text.primary',
                        flexShrink: 0,
                        position: 'relative',
                        zIndex: 1,
                      }}
                    />
                    <Typography
                      variant="h6"
                      component="span"
                      sx={{ fontWeight: 800, lineHeight: 1 }}
                    >
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
                    <ProductionView
                      productions={productions}
                      layout="list"
                      selectedTagIds={selectedTagIds}
                    />
                  </Box>
                </Stack>
              ))}
            </Stack>

            {hasMoreProductions && (
              <Box sx={{ mt: 4, pl: { xs: 3, md: 13 } }}>
                <Button
                  variant="outlined"
                  onClick={() => void loadMoreProductions()}
                  disabled={isLoadingMore}
                >
                  {isLoadingMore
                    ? t('common.loading', 'Loading…')
                    : t('series.showMore', 'Show More')}
                </Button>
              </Box>
            )}
          </Box>
        )}
      </Stack>
    </Container>
  )
}

const SeriesDetailPage = () => {
  const location = useLocation()
  const { i18n, t } = useTranslation()
  const { id } = useParams<{ id: string }>()
  const currentLanguage = resolveCurrentLanguage(
    location.pathname,
    i18n.language,
    i18n.resolvedLanguage,
  )
  const seriesPath = toLocalizedPath('/series', currentLanguage)

  if (!id || Number.isNaN(Number(id))) {
    return (
      <Navigate
        to={seriesPath}
        replace
        state={createFloatingAlertState({
          message: t('series.invalidId'),
          severity: ALERT_SEVERITIES.error,
        })}
      />
    )
  }

  return <SeriesDetailContent key={id} id={id} />
}

export default SeriesDetailPage
