/**
 * Displays detailed information about a specific series (tag),
 * including its metadata, statistics and a chronological list
 * of associated productions grouped by year.
 *
 * This page handles:
 * - Fetching series metadata (Tag)
 * - Fetching paginated productions for the series
 * - Grouping productions by year
 * - Infinite "Load more" pagination
 * - Rate-limit handling (429 redirects with floating alert state)
 * - Localized routing and translations
 */

import { Alert, Box, Button, Container, Divider, Stack, Typography } from '@mui/material'
import { useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Navigate, useLocation, useNavigate, useParams } from 'react-router-dom'

import SeriesDetailPageSkeleton from './SeriesDetailPageSkeleton'
import { ApiError } from '../../../services/ApiTypes'
import { getProductions } from '../../../services/productions/Productions'
import { getTag } from '../../../services/tags/Tags'
import CollectionView from '../../../shared/components/CollectionView'
import { ALERT_SEVERITIES } from '../../../types/FloatingAlertConfig'
import { resolveCurrentLanguage, toLocalizedPath } from '../../../utils/localizedRoutes'
import { createFloatingAlertState } from '../../../utils/navigation'
import { getTranslatedRecord } from '../../../utils/translations'
import ProductionGridCard from '../../productions/components/cards/ProductionGridCard'
import ProductionListCard from '../../productions/components/cards/ProductionListCard'
import Breadcrumbs from '../../productions/components/detail/Breadcrumbs'
import SeriesHeader from '../components/SeriesHeader'
import SeriesStats from '../components/SeriesStats'

import type { Production } from '../../../types/Productions'
import type { Tag } from '../../../types/Tags'

const PAGE_SIZE = 12
const SERIES_PRODUCTIONS_ORDERING = '-first_event_start'

/**
 * UI representation of a single stat block in the series header.
 */
type SeriesStat = {
  value: string
  label: string
}

/**
 * Error keys used for translation-based error handling.
 */
type SeriesErrorKey = 'series.invalidId' | 'series.fetchError' | null

/**
 * Groups productions by year for timeline-style rendering.
 */
type ProductionYearGroup = {
  year: number
  productions: Production[]
}

type SeriesDetailContentProps = {
  id: string
}

/**
 * Extracts a sortable timestamp from a production.
 * Prefers first_event_start, falls back to last_event_end.
 */
const getProductionDateTimestamp = (production: Production): number => {
  const date = production.first_event_start ?? production.last_event_end
  return date ? new Date(date).getTime() : Number.NEGATIVE_INFINITY
}

/**
 * Sort productions by date descending (newest first),
 * then by ID as a stable fallback.
 */
const sortProductionsByDateDesc = (productions: Production[]): Production[] =>
  [...productions].sort((a, b) => {
    const dateDifference = getProductionDateTimestamp(b) - getProductionDateTimestamp(a)

    if (dateDifference !== 0) {
      return dateDifference
    }

    return b.id - a.id
  })

/**
 * Extract year from production date fields.
 * Returns null if no valid date exists.
 */
const getProductionYear = (production: Production): number | null => {
  const date = production.first_event_start ?? production.last_event_end

  if (!date) {
    return null
  }

  const year = new Date(date).getFullYear()
  return Number.isNaN(year) ? null : year
}

/**
 * Groups productions by year and sorts them in reverse chronological order.
 */
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

/**
 * Main content component for a series detail page.
 * Handles data fetching, pagination, grouping, and rendering.
 */
const SeriesDetailContent = ({ id }: SeriesDetailContentProps) => {
  const location = useLocation()
  const navigate = useNavigate()
  const { t, i18n } = useTranslation()
  const currentLanguage = resolveCurrentLanguage(
    location.pathname,
    i18n.language,
    i18n.resolvedLanguage,
  )
  const notFoundPath = toLocalizedPath('/not-found', currentLanguage)

  const [seriesTag, setSeriesTag] = useState<Tag | null>(null)
  const [seriesProductions, setSeriesProductions] = useState<Production[]>([])
  const [totalProductions, setTotalProductions] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [isLoading, setIsLoading] = useState(true)
  const [isLoadingMore, setIsLoadingMore] = useState(false)
  const [error, setError] = useState<SeriesErrorKey>(null)
  const numericId = Number(id)

  // Keep the latest navigation and localization values in refs so the fetch
  // effect can stay tied to the route id only.
  const navigateRef = useRef(navigate)
  const currentLanguageRef = useRef(currentLanguage)
  const currentPathRef = useRef(location.pathname)
  const tRef = useRef(t)

  useEffect(() => {
    navigateRef.current = navigate
  }, [navigate])

  useEffect(() => {
    currentLanguageRef.current = currentLanguage
  }, [currentLanguage])

  useEffect(() => {
    currentPathRef.current = location.pathname
  }, [location.pathname])

  useEffect(() => {
    tRef.current = t
  }, [t])

  /**
   * Initial fetch: loads tag + first page of productions.
   */
  useEffect(() => {
    let isActive = true

    const fetchSeries = async () => {
      setError(null)

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
          const alertMessage = Number(error.message) === 429 ? String(error.status) : error.message
          navigateRef.current(toLocalizedPath('/series', currentLanguageRef.current), {
            replace: true,
            state: createFloatingAlertState({
              message: alertMessage,
              severity: ALERT_SEVERITIES.warning,
            }),
          })
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
  }, [numericId])

  /**
   * Loads the next page of productions.
   *
   * Uses the latest route values from refs so error redirects still stay
   * localized without broadening the fetch dependencies.
   */
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

      const nextResults = response?.results ?? []

      setSeriesProductions((currentProductions) =>
        sortProductionsByDateDesc([...currentProductions, ...nextResults]),
      )
      setTotalProductions(response?.count ?? totalProductions)
      setCurrentPage(nextPage)
    } catch (error: unknown) {
      if (error instanceof ApiError && (error.status === 429 || Number(error.message) === 429)) {
        const alertMessage = Number(error.message) === 429 ? String(error.status) : error.message
        navigateRef.current(currentPathRef.current, {
          replace: true,
          state: createFloatingAlertState({
            message: alertMessage,
            severity: ALERT_SEVERITIES.warning,
          }),
        })
      }
    } finally {
      setIsLoadingMore(false)
    }
  }

  /**
   * Memoized grouping of productions by year.
   */
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

  /**
   * Stats displayed in header section.
   */
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
    getTranslatedRecord(seriesTag.excerpt, lang, seriesTag.display_excerpt) ||
    t('blogs.home.noExcerpt', 'No excerpt available')

  const seriesDescription =
    getTranslatedRecord(seriesTag.short_description, lang, seriesTag.display_short_description) ||
    t('series.noDescription')

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
                    <CollectionView
                      items={productions}
                      layout="list"
                      getKey={(production) => production.id}
                      renderListItem={(production) => (
                        <ProductionListCard production={production} />
                      )}
                      renderGridItem={(production) => (
                        <ProductionGridCard production={production} />
                      )}
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

/**
 * Route wrapper that validates the URL param and handles invalid IDs.
 */
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
