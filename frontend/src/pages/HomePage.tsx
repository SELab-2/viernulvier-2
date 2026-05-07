import ArrowForwardOutlinedIcon from '@mui/icons-material/ArrowForwardOutlined'
import SearchOutlinedIcon from '@mui/icons-material/SearchOutlined'
import {
  Box,
  Button,
  Container,
  Divider,
  InputAdornment,
  OutlinedInput,
  Paper,
  Stack,
  Typography,
  useTheme,
} from '@mui/material'
import { keyframes } from '@mui/material/styles'
import { type SyntheticEvent, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link as RouterLink, useLocation, useNavigate } from 'react-router-dom'

import { useCollectionPageNotification } from '../hooks/useCollectionPageNotification'
import { getLandingStats, type LandingStatsResponse } from '../services/productions/Productions'
import { createHomePageStyles } from '../theme/styles'
import { tokens } from '../theme/tokens'
import { resolveCurrentLanguage, toLocalizedPath } from '../utils/localizedRoutes'

// ─── Animations ────────────────────────────────────────────────────────────────

const fadeUp = keyframes`
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
`

const ticker = keyframes`
  from { transform: translate3d(0, 0, 0); }
  to   { transform: translate3d(-50%, 0, 0); }
`

// ─── Static data ────────────────────────────────────────────────────────────────

type LandingCard = {
  eyebrowKey: string
  titleKey: string
  descriptionKey: string
  ctaKey: string
  to: string
  index: number
}

const LANDING_CARDS: LandingCard[] = [
  {
    eyebrowKey: 'landing.cards.archive.eyebrow',
    titleKey: 'landing.cards.archive.title',
    descriptionKey: 'landing.cards.archive.description',
    ctaKey: 'landing.cards.archive.cta',
    to: '/archive',
    index: 0,
  },
  {
    eyebrowKey: 'landing.cards.series.eyebrow',
    titleKey: 'landing.cards.series.title',
    descriptionKey: 'landing.cards.series.description',
    ctaKey: 'landing.cards.series.cta',
    to: '/series',
    index: 1,
  },
  {
    eyebrowKey: 'landing.cards.blogs.eyebrow',
    titleKey: 'landing.cards.blogs.title',
    descriptionKey: 'landing.cards.blogs.description',
    ctaKey: 'landing.cards.blogs.cta',
    to: '/blogs',
    index: 2,
  },
  {
    eyebrowKey: 'landing.cards.prints.eyebrow',
    titleKey: 'landing.cards.prints.title',
    descriptionKey: 'landing.cards.prints.description',
    ctaKey: 'landing.cards.prints.cta',
    to: '/media',
    index: 3,
  },
]

const FALLBACK_ARCHIVE_STATS: LandingStatsResponse = {
  productions: 8500,
  series: 0,
  years: 22,
  blogs: 0,
}

const ARCHIVE_STATS = [
  { labelKey: 'landing.stats.productions', dataKey: 'productions' },
  { labelKey: 'landing.stats.series', dataKey: 'series' },
  { labelKey: 'landing.stats.years', dataKey: 'years' },
  { labelKey: 'landing.stats.blogs', dataKey: 'blogs' },
] as const

const formatArchiveStatValue = (value: number): string => {
  const formatted = new Intl.NumberFormat('nl-BE').format(value)
  return value > 0 ? `${formatted}+` : formatted
}

const LANDING_NOTES = [
  {
    titleKey: 'landing.side.archive.title',
    descriptionKey: 'landing.side.archive.description',
  },
  {
    titleKey: 'landing.side.series.title',
    descriptionKey: 'landing.side.series.description',
  },
  {
    titleKey: 'landing.side.blogs.title',
    descriptionKey: 'landing.side.blogs.description',
  },
  {
    titleKey: 'landing.side.prints.title',
    descriptionKey: 'landing.side.prints.description',
  },
] as const

// ─── Subcomponents ───────────────────────────────────────────────────────────────

/** Thin horizontal rule with optional label */
const RuleLabel = ({ label }: { label: string }) => {
  const theme = useTheme()
  return (
    <Stack direction="row" spacing={2} sx={{ alignItems: 'center' }}>
      <Box sx={{ flex: 1, height: '1px', bgcolor: theme.palette.divider }} />
      <Typography
        variant="overline"
        sx={{
          fontSize: '0.72rem',
          letterSpacing: '0.18em',
          color: 'text.disabled',
          whiteSpace: 'nowrap',
        }}
      >
        {label}
      </Typography>
      <Box sx={{ flex: 1, height: '1px', bgcolor: theme.palette.divider }} />
    </Stack>
  )
}

const TickerStrip = ({ items }: { items: string[] }) => {
  const theme = useTheme()
  const homepageStyles = createHomePageStyles(theme)
  const tickerLane = [...items, ...items, ...items]
  const tickerLanes = [tickerLane, tickerLane]

  return (
    <Box
      sx={{
        overflow: 'hidden',
        bgcolor: homepageStyles.tickerBackground,
        borderTop: `1px solid ${theme.palette.divider}`,
        borderBottom: `1px solid ${theme.palette.divider}`,
        py: '8px',
        userSelect: 'none',
      }}
    >
      <Box
        sx={{
          display: 'flex',
          width: 'max-content',
          animation: `${ticker} 60s linear infinite`,
          willChange: 'transform',
          '&:hover': { animationPlayState: 'paused' },
          '@media (prefers-reduced-motion: reduce)': { animation: 'none' },
        }}
      >
        {tickerLanes.map((lane, laneIndex) => (
          <Box
            key={`lane-${laneIndex}`}
            sx={{
              display: 'inline-flex',
              alignItems: 'center',
              flexShrink: 0,
              gap: 3,
              pr: 3,
            }}
          >
            {lane.map((item, index) => (
              <Typography
                key={`${laneIndex}-${item}-${index}`}
                component="span"
                sx={{
                  fontFamily: '"Space Mono", monospace',
                  fontSize: '0.64rem',
                  letterSpacing: '0.22em',
                  color: homepageStyles.tickerText,
                  whiteSpace: 'nowrap',
                  fontWeight: item === '·' ? 400 : 700,
                }}
              >
                {item}
              </Typography>
            ))}
          </Box>
        ))}
      </Box>
    </Box>
  )
}

// ─── Page ───────────────────────────────────────────────────────────────────────

const HomePage = () => {
  const { t, i18n } = useTranslation()
  const theme = useTheme()
  const homepageStyles = createHomePageStyles(theme)
  const navigate = useNavigate()
  const location = useLocation()
  const [searchQuery, setSearchQuery] = useState('')
  const [archiveStats, setArchiveStats] = useState<LandingStatsResponse>(FALLBACK_ARCHIVE_STATS)
  const currentLanguage = resolveCurrentLanguage(
    location.pathname,
    i18n.language,
    i18n.resolvedLanguage,
  )
  const localizedPath = (path: string) => toLocalizedPath(path, currentLanguage)
  const { showFloatingAlert, clearFloatingAlert } =
    useCollectionPageNotification('home.error.notification')

  useEffect(() => {
    let isActive = true

    const fetchStats = async () => {
      // Clear any existing floating alerts for predictable UX
      clearFloatingAlert()

      try {
        const response = await getLandingStats()
        if (!isActive) {
          return
        }

        setArchiveStats(response)
      } catch (error: unknown) {
        if (!isActive) {
          return
        }

        // Show a floating alert for API failures (rate-limits will be shown as warnings)
        showFloatingAlert(error)

        // Keep predictable values when the stats endpoint is temporarily unavailable.
        setArchiveStats(FALLBACK_ARCHIVE_STATS)
      }
    }

    void fetchStats()

    return () => {
      isActive = false
    }
  }, [])

  const handleSearch = (e: SyntheticEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      navigate(`${localizedPath('/archive')}?q=${encodeURIComponent(searchQuery.trim())}`)
    } else {
      navigate(localizedPath('/archive'))
    }
  }

  const tickerItems = [
    t('landing.ticker.brand'),
    '·',
    t('landing.ticker.city'),
    '·',
    t('landing.ticker.archive'),
    '·',
    t('landing.ticker.collection'),
    '·',
    t('landing.ticker.years', { value: formatArchiveStatValue(archiveStats.years) }),
    '·',
    t('landing.ticker.productions', { value: formatArchiveStatValue(archiveStats.productions) }),
    '·',
    t('landing.ticker.performances'),
    '·',
    t('landing.ticker.center'),
    '·',
    t('landing.ticker.theatre'),
    '·',
    t('landing.ticker.concert'),
    '·',
    t('landing.ticker.dance'),
    '·',
  ]

  return (
    <Box sx={{ py: { xs: 3, md: 5 } }}>
      <Container maxWidth="xl">
        <Stack spacing={{ xs: 6, md: 8 }}>
          {/* ── 2. HERO ──────────────────────────────────────────────────────── */}
          <Paper
            elevation={0}
            sx={{
              position: 'relative',
              overflow: 'hidden',
              borderRadius: tokens.card.borderRadiusPx,
              border: `1px solid ${theme.palette.divider}`,
              background: homepageStyles.heroBackground,
              animation: `${fadeUp} 700ms 80ms ease both`,
              '@media (prefers-reduced-motion: reduce)': { animation: 'none' },
            }}
          >
            {/* Top accent line */}
            <Box
              sx={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                height: '2px',
                background: homepageStyles.heroAccentLine,
              }}
            />

            <Box
              sx={{
                position: 'relative',
                display: 'grid',
                gridTemplateColumns: { xs: '1fr', lg: '1fr 420px' },
                gap: { xs: 4, lg: 6 },
                p: { xs: 3, sm: 4, md: 6 },
              }}
            >
              {/* Left: headline + search */}
              <Stack spacing={4} sx={{ justifyContent: 'center', minWidth: 0 }}>
                <Stack spacing={2.5}>
                  <Typography
                    variant="overline"
                    sx={{
                      letterSpacing: '0.2em',
                      color: 'text.secondary',
                      fontSize: '0.8rem',
                    }}
                  >
                    {t('landing.hero.eyebrow')}
                  </Typography>

                  <Typography
                    component="h1"
                    sx={{
                      fontWeight: 800,
                      lineHeight: 1.0,
                      fontSize: { xs: '2.6rem', sm: '3.4rem', md: '4.2rem', lg: '4.8rem' },
                      color: 'text.primary',
                      letterSpacing: '-0.02em',
                      maxWidth: 820,
                    }}
                  >
                    {t('landing.hero.title')}
                  </Typography>

                  <Typography
                    variant="body1"
                    sx={{
                      maxWidth: 660,
                      fontSize: { xs: '1rem', md: '1.1rem' },
                      lineHeight: 1.75,
                      color: 'text.secondary',
                    }}
                  >
                    {t('landing.hero.description')}
                  </Typography>
                </Stack>

                {/* Search bar */}
                <Box component="form" onSubmit={handleSearch} sx={{ maxWidth: 560 }}>
                  <OutlinedInput
                    fullWidth
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder={t('searchbar.searchPlaceholder')}
                    startAdornment={
                      <InputAdornment position="start">
                        <SearchOutlinedIcon sx={{ color: 'text.disabled', fontSize: 20 }} />
                      </InputAdornment>
                    }
                    endAdornment={
                      <InputAdornment position="end">
                        <Button
                          type="submit"
                          variant="contained"
                          size="small"
                          sx={{ borderRadius: '6px', px: 2, py: 0.75, fontSize: '0.82rem' }}
                        >
                          {t('searchbar.search')}
                        </Button>
                      </InputAdornment>
                    }
                    sx={{
                      bgcolor: homepageStyles.inputBackground,
                      fontSize: '0.95rem',
                      '& .MuiOutlinedInput-notchedOutline': {
                        borderColor: homepageStyles.accentBorder,
                      },
                    }}
                  />
                </Box>

                {/* CTA buttons */}
                <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
                  <Button
                    component={RouterLink}
                    to={localizedPath('/archive')}
                    variant="contained"
                    size="large"
                    sx={{ fontWeight: 700 }}
                  >
                    {t('landing.hero.primaryCta')}
                  </Button>
                  <Button
                    component={RouterLink}
                    to={localizedPath('/series')}
                    variant="outlined"
                    size="large"
                  >
                    {t('landing.hero.seriesCta')}
                  </Button>
                  <Button
                    component={RouterLink}
                    to={localizedPath('/blogs')}
                    variant="outlined"
                    size="large"
                  >
                    {t('landing.hero.secondaryCta')}
                  </Button>
                  <Button
                    component="a"
                    href="https://www.viernulvier.gent/"
                    target="_blank"
                    rel="noopener noreferrer"
                    variant="text"
                    size="large"
                  >
                    {t('landing.hero.websiteCta')}
                  </Button>
                </Stack>
              </Stack>

              {/* Right: info panel */}
              <Paper
                elevation={0}
                sx={{
                  p: { xs: 2.5, sm: 3 },
                  borderRadius: tokens.card.borderRadiusPx,
                  border: `1px solid ${theme.palette.divider}`,
                  bgcolor: homepageStyles.heroPanelBackground,
                  backdropFilter: 'blur(12px)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 2.5,
                }}
              >
                <Stack spacing={0.5}>
                  <Typography
                    variant="overline"
                    sx={{ fontSize: '0.74rem', letterSpacing: '0.16em', color: 'text.disabled' }}
                  >
                    {t('landing.side.eyebrow')}
                  </Typography>
                  <Typography variant="h6" sx={{ fontWeight: 700, lineHeight: 1.25 }}>
                    {t('landing.side.title')}
                  </Typography>
                </Stack>

                <Stack divider={<Divider flexItem />} spacing={0}>
                  {LANDING_NOTES.map((note) => (
                    <Stack key={note.titleKey} spacing={0.5} sx={{ py: 1.5 }}>
                      <Typography
                        variant="subtitle2"
                        sx={{ fontWeight: 700, fontSize: '0.9rem', lineHeight: 1.3 }}
                      >
                        {t(note.titleKey)}
                      </Typography>
                      <Typography
                        variant="body2"
                        sx={{ fontSize: '0.85rem', color: 'text.secondary', lineHeight: 1.55 }}
                      >
                        {t(note.descriptionKey)}
                      </Typography>
                    </Stack>
                  ))}
                </Stack>
              </Paper>
            </Box>

            <TickerStrip items={tickerItems} />
          </Paper>

          {/* ── 3. STATS BAR ─────────────────────────────────────────────────── */}
          <Box
            sx={{
              animation: `${fadeUp} 700ms 200ms ease both`,
              '@media (prefers-reduced-motion: reduce)': { animation: 'none' },
            }}
          >
            <Stack spacing={2}>
              <RuleLabel label={t('landing.statsSection.eyebrow')} />
              <Stack spacing={0.75} sx={{ maxWidth: 720 }}>
                <Typography
                  variant="h5"
                  component="h2"
                  sx={{ fontWeight: 800, letterSpacing: '-0.02em', color: 'text.primary' }}
                >
                  {t('landing.statsSection.title')}
                </Typography>
                <Typography variant="body2" sx={{ color: 'text.secondary', lineHeight: 1.6 }}>
                  {t('landing.statsSection.description')}
                </Typography>
              </Stack>

              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: {
                    xs: 'repeat(2, minmax(0, 1fr))',
                    md: 'repeat(4, minmax(0, 1fr))',
                  },
                  gap: 1,
                  border: `1px solid ${theme.palette.divider}`,
                  borderRadius: tokens.card.borderRadiusPx,
                  overflow: 'hidden',
                  bgcolor: theme.palette.background.paper,
                }}
              >
                {ARCHIVE_STATS.map((stat, i) => (
                  <Box
                    key={stat.labelKey}
                    sx={{
                      p: { xs: 1.75, md: 2.25 },
                      borderRight: {
                        xs: 'none',
                        md:
                          i < ARCHIVE_STATS.length - 1
                            ? `1px solid ${theme.palette.divider}`
                            : 'none',
                      },
                      borderBottom: {
                        xs: i < 2 ? `1px solid ${theme.palette.divider}` : 'none',
                        md: 'none',
                      },
                      bgcolor: homepageStyles.subtleSurface,
                      textAlign: 'center',
                      minWidth: 0,
                    }}
                  >
                    <Typography
                      sx={{
                        fontSize: { xs: '1.45rem', md: '1.8rem' },
                        fontWeight: 800,
                        letterSpacing: '-0.03em',
                        lineHeight: 1,
                        color: 'text.primary',
                      }}
                    >
                      {formatArchiveStatValue(archiveStats[stat.dataKey])}
                    </Typography>
                    <Typography
                      variant="caption"
                      sx={{
                        mt: 0.5,
                        display: 'block',
                        fontSize: '0.72rem',
                        letterSpacing: '0.08em',
                        textTransform: 'uppercase',
                        color: 'text.disabled',
                      }}
                    >
                      {t(stat.labelKey)}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </Stack>
          </Box>

          {/* ── 4. ENTRY CARDS SECTION ───────────────────────────────────────── */}
          <Stack spacing={3}>
            <RuleLabel label={t('landing.cardsSection.eyebrow')} />

            <Stack spacing={1}>
              <Typography
                variant="h4"
                component="h2"
                sx={{ fontWeight: 800, letterSpacing: '-0.02em', color: 'text.primary' }}
              >
                {t('landing.cardsSection.title')}
              </Typography>
              <Typography
                variant="body1"
                sx={{ maxWidth: 640, color: 'text.secondary', lineHeight: 1.7 }}
              >
                {t('landing.cardsSection.description')}
              </Typography>
            </Stack>

            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: {
                  xs: '1fr',
                  sm: 'repeat(2, minmax(0,1fr))',
                  xl: 'repeat(4, minmax(0,1fr))',
                },
                gap: 2,
              }}
            >
              {LANDING_CARDS.map((card) => (
                <Paper
                  key={card.to}
                  component={RouterLink}
                  to={localizedPath(card.to)}
                  elevation={0}
                  sx={{
                    minHeight: 200,
                    p: 3,
                    borderRadius: tokens.card.borderRadiusPx,
                    border: `1px solid ${theme.palette.divider}`,
                    textDecoration: 'none',
                    color: 'inherit',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    bgcolor: theme.palette.background.paper,
                    transition: tokens.transitions.base,
                    animation: `${fadeUp} 700ms ${160 + card.index * 80}ms ease both`,
                    '@media (prefers-reduced-motion: reduce)': { animation: 'none' },
                    '&:hover': {
                      bgcolor: homepageStyles.cardHoverBackground,
                      borderColor: homepageStyles.cardHoverBorder,
                      transform: 'translateY(-3px)',
                      boxShadow: tokens.shadows.md,
                    },
                  }}
                >
                  <Stack spacing={1.5}>
                    <Typography
                      variant="overline"
                      sx={{
                        fontSize: '0.72rem',
                        letterSpacing: '0.16em',
                        color: 'text.disabled',
                      }}
                    >
                      {t(card.eyebrowKey)}
                    </Typography>
                    <Typography
                      variant="h5"
                      component="h3"
                      sx={{
                        fontWeight: 800,
                        letterSpacing: '-0.02em',
                        lineHeight: 1.1,
                        color: 'text.primary',
                      }}
                    >
                      {t(card.titleKey)}
                    </Typography>
                    <Typography
                      variant="body2"
                      sx={{
                        fontSize: '0.9rem',
                        lineHeight: 1.65,
                        color: 'text.secondary',
                      }}
                    >
                      {t(card.descriptionKey)}
                    </Typography>
                  </Stack>

                  <Stack
                    direction="row"
                    spacing={1}
                    sx={{
                      alignItems: 'center',
                      mt: 3,
                      pt: 2,
                      borderTop: `1px solid ${theme.palette.divider}`,
                    }}
                  >
                    <Typography
                      variant="button"
                      sx={{
                        fontSize: '0.82rem',
                        letterSpacing: '0.04em',
                        fontWeight: 700,
                        color: 'text.primary',
                      }}
                    >
                      {t(card.ctaKey)}
                    </Typography>
                    <ArrowForwardOutlinedIcon sx={{ fontSize: 16 }} />
                  </Stack>
                </Paper>
              ))}
            </Box>
          </Stack>
        </Stack>
      </Container>
    </Box>
  )
}

export default HomePage
