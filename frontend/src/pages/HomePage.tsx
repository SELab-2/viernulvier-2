import SearchOutlinedIcon from '@mui/icons-material/SearchOutlined'
import {
  Box,
  Button,
  Container,
  InputAdornment,
  OutlinedInput,
  Stack,
  Typography,
  useTheme,
} from '@mui/material'
import { keyframes } from '@mui/material/styles'
import { type SyntheticEvent, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link as RouterLink, useLocation, useNavigate } from 'react-router-dom'

import { getLandingStats, type LandingStatsResponse } from '../services/productions/Productions'
import { useCollectionPageNotification } from '../shared/hooks/useCollectionPageNotification'
import { createHomePageStyles } from '../theme/styles'
import { resolveCurrentLanguage, toLocalizedPath } from '../utils/localizedRoutes'

// Animations

const fadeUp = keyframes`
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
`

// Static data

type LandingCard = {
  eyebrowKey: string
  titleKey: string
  ctaKey: string
  to: string
  image: string
  index: number
}

const LANDING_CARDS: LandingCard[] = [
  {
    eyebrowKey: 'landing.cards.archive.eyebrow',
    titleKey: 'landing.cards.archive.title',
    ctaKey: 'landing.cards.archive.cta',
    to: '/archive',
    image: '/homepage_archive.webp',
    index: 0,
  },
  {
    eyebrowKey: 'landing.cards.series.eyebrow',
    titleKey: 'landing.cards.series.title',
    ctaKey: 'landing.cards.series.cta',
    to: '/series',
    image: '/homepage_series.webp',
    index: 1,
  },
  {
    eyebrowKey: 'landing.cards.blogs.eyebrow',
    titleKey: 'landing.cards.blogs.title',
    ctaKey: 'landing.cards.blogs.cta',
    to: '/blogs',
    image: '/homepage_blogs.webp',
    index: 2,
  },
  {
    eyebrowKey: 'landing.cards.media.eyebrow',
    titleKey: 'landing.cards.media.title',
    ctaKey: 'landing.cards.media.cta',
    to: '/media',
    image: '/homepage_media.webp',
    index: 3,
  },
]

const ARCHIVE_STATS = [
  { labelKey: 'landing.stats.productions', dataKey: 'productions' },
  { labelKey: 'landing.stats.series', dataKey: 'series' },
  { labelKey: 'landing.stats.years', dataKey: 'years' },
  { labelKey: 'landing.stats.blogs', dataKey: 'blogs' },
] as const

const formatArchiveStatValue = (value: number | undefined | null): string => {
  if (value === undefined || value === null) {
    return '-'
  }
  if (value <= 0) {
    return '-'
  }
  const formatted = new Intl.NumberFormat('nl-BE').format(value)
  return `${formatted}+`
}

// ─── Page ─────────────────────────────────────────────────────────────────────

const HomePage = () => {
  const { t, i18n } = useTranslation()
  const theme = useTheme()
  const s = createHomePageStyles(theme)
  const navigate = useNavigate()
  const location = useLocation()
  const [searchQuery, setSearchQuery] = useState('')
  const [archiveStats, setArchiveStats] = useState<Partial<LandingStatsResponse>>({})

  const currentLanguage = resolveCurrentLanguage(
    location.pathname,
    i18n.language,
    i18n.resolvedLanguage,
  )
  const localizedPath = (path: string) => toLocalizedPath(path, currentLanguage)
  const { showFloatingAlert, clearFloatingAlert } = useCollectionPageNotification(
    'archive.home.error.notification',
  )

  useEffect(() => {
    let isActive = true
    const fetchStats = async () => {
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
        showFloatingAlert(error)
        setArchiveStats({})
      }
    }
    void fetchStats()
    return () => {
      isActive = false
    }
  }, [clearFloatingAlert, showFloatingAlert])

  const handleSearch = (e: SyntheticEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      navigate(`${localizedPath('/archive')}?q=${encodeURIComponent(searchQuery.trim())}`)
    } else {
      navigate(localizedPath('/archive'))
    }
  }

  return (
    <Box>
      {/* HERO */}
      <Box
        sx={{
          position: 'relative',
          height: { xs: '72vh', md: '78vh' },
          minHeight: { xs: 560, md: 580 },
          overflow: 'hidden',
          background: s.heroFallbackGradient,
        }}
      >
        {/* Background image */}
        <Box
          component="img"
          src="/homepage_hero.webp"
          alt=""
          aria-hidden
          onError={(e) => {
            ;(e.currentTarget as HTMLImageElement).style.display = 'none'
          }}
          sx={{
            position: 'absolute',
            inset: 0,
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            objectPosition: 'center',
          }}
        />

        {/* Gradient overlay - two-layer for richer depth */}
        <Box sx={{ position: 'absolute', inset: 0, background: s.heroOverlay }} />
        <Box sx={{ position: 'absolute', inset: 0, background: s.heroOverlayVignette }} />

        {/* Hero content */}
        <Container
          maxWidth="xl"
          sx={{
            position: 'relative',
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'flex-end',
            pb: { xs: 6, md: 8 },
            pt: { xs: '72px', md: '88px' },
          }}
        >
          <Stack spacing={3.5} sx={{ maxWidth: 660, animation: `${fadeUp} 600ms ease both` }}>
            {/* Eyebrow label */}
            <Typography
              sx={{
                fontSize: '0.72rem',
                fontWeight: 600,
                letterSpacing: '0.16em',
                textTransform: 'uppercase',
                color: s.heroEyebrowColor,
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                '&::before': {
                  content: '""',
                  display: 'block',
                  width: 24,
                  height: 2,
                  bgcolor: s.heroEyebrowColor,
                  borderRadius: 1,
                  flexShrink: 0,
                },
              }}
            >
              {t('landing.hero.eyebrow')}
            </Typography>

            <Typography
              component="h1"
              sx={{
                fontWeight: 800,
                lineHeight: 1.0,
                fontSize: { xs: '2.6rem', sm: '3.4rem', md: '4.4rem' },
                color: s.heroTitleColor,
                letterSpacing: '-0.02em',
              }}
            >
              {t('landing.hero.title')}
            </Typography>

            <Typography
              sx={{
                fontSize: { xs: '0.95rem', md: '1.05rem' },
                lineHeight: 1.75,
                color: s.heroDescriptionColor,
                maxWidth: 500,
              }}
            >
              {t('landing.hero.description')}
            </Typography>

            {/* Search bar */}
            <Box component="form" onSubmit={handleSearch} sx={{ maxWidth: 480 }}>
              <OutlinedInput
                fullWidth
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={t('searchbar.searchPlaceholder')}
                inputProps={{
                  style: {
                    textOverflow: 'ellipsis',
                  },
                }}
                startAdornment={
                  <InputAdornment position="start">
                    <SearchOutlinedIcon sx={{ color: s.searchIconColor, fontSize: 19 }} />
                  </InputAdornment>
                }
                endAdornment={
                  <InputAdornment position="end">
                    <Button
                      type="submit"
                      variant="contained"
                      size="small"
                      disableElevation
                      sx={{
                        borderRadius: '6px',
                        px: 2,
                        py: 0.75,
                        fontSize: '0.8rem',
                        fontWeight: 600,
                        bgcolor: s.searchButtonBg,
                        color: s.searchButtonText,
                        '&:hover': { bgcolor: s.searchButtonBgHover },
                      }}
                    >
                      {t('searchbar.search')}
                    </Button>
                  </InputAdornment>
                }
                sx={{
                  bgcolor: s.searchInputBg,
                  backdropFilter: 'blur(10px)',
                  borderRadius: '8px',
                  '& input': {
                    color: s.searchInputText,
                    fontSize: '0.92rem',
                    '&::placeholder': { color: s.searchInputPlaceholder, opacity: 1 },
                  },
                  '& .MuiOutlinedInput-notchedOutline': {
                    borderColor: s.searchInputBorder,
                  },
                  '&:hover .MuiOutlinedInput-notchedOutline': {
                    borderColor: s.searchInputBorderHover,
                  },
                  '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                    borderColor: s.searchInputBorderFocus,
                    borderWidth: 1.5,
                  },
                }}
              />
            </Box>

            {/* CTA buttons */}
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} sx={{ flexWrap: 'wrap' }}>
              <Button
                component={RouterLink}
                to={localizedPath('/archive')}
                variant="contained"
                size="large"
                disableElevation
                sx={{
                  fontWeight: 700,
                  fontSize: '0.9rem',
                  bgcolor: s.primaryButtonBg,
                  color: s.primaryButtonText,
                  '&:hover': { bgcolor: s.primaryButtonBgHover },
                }}
              >
                {t('landing.hero.primaryCta')}
              </Button>
              <Button
                component={RouterLink}
                to={localizedPath('/series')}
                variant="outlined"
                size="large"
                sx={{
                  fontWeight: 600,
                  fontSize: '0.9rem',
                  borderColor: s.secondaryButtonBorder,
                  color: s.secondaryButtonText,
                  '&:hover': {
                    borderColor: s.secondaryButtonBorderHover,
                    bgcolor: s.secondaryButtonBgHover,
                  },
                }}
              >
                {t('landing.hero.seriesCta')}
              </Button>
              <Button
                component="a"
                href="https://www.viernulvier.gent/"
                target="_blank"
                rel="noopener noreferrer"
                variant="text"
                size="large"
                sx={{
                  fontSize: '0.9rem',
                  color: s.tertiaryButtonText,
                  '&:hover': { color: s.tertiaryButtonTextHover, bgcolor: 'transparent' },
                }}
              >
                {t('landing.hero.websiteCta')} →
              </Button>
            </Stack>
          </Stack>
        </Container>
      </Box>

      {/* STATS BAR */}
      <Box
        sx={{
          bgcolor: s.statBarBg,
          borderBottom: `1px solid ${theme.palette.divider}`,
        }}
      >
        <Container maxWidth="xl">
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(4, 1fr)' },
            }}
          >
            {ARCHIVE_STATS.map((stat, i) => (
              <Box
                key={stat.labelKey}
                sx={{
                  py: { xs: 3, md: 4 },
                  px: 2,
                  textAlign: 'center',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 0.5,
                  borderRight: {
                    xs: i % 2 === 0 ? `1px solid ${theme.palette.divider}` : 'none',
                    sm: i < 3 ? `1px solid ${theme.palette.divider}` : 'none',
                  },
                  borderBottom: {
                    xs: i < 2 ? `1px solid ${theme.palette.divider}` : 'none',
                    sm: 'none',
                  },
                }}
              >
                <Typography
                  sx={{
                    fontSize: { xs: '1.7rem', md: '2.4rem' },
                    fontWeight: 800,
                    letterSpacing: '-0.03em',
                    lineHeight: 1,
                    color: s.statValueColor,
                  }}
                >
                  {formatArchiveStatValue(archiveStats[stat.dataKey])}
                </Typography>
                <Typography
                  sx={{
                    fontSize: '0.67rem',
                    fontWeight: 600,
                    letterSpacing: '0.12em',
                    textTransform: 'uppercase',
                    color: s.statLabelColor,
                  }}
                >
                  {t(stat.labelKey)}
                </Typography>
              </Box>
            ))}
          </Box>
        </Container>
      </Box>

      {/* PHOTO CARDS */}
      <Container maxWidth="xl" sx={{ py: { xs: 6, md: 9 } }}>
        {/* Section header */}
        <Box sx={{ mb: { xs: 3.5, md: 5 } }}>
          <Typography
            component="h2"
            sx={{
              fontSize: { xs: '1.5rem', md: '1.9rem' },
              fontWeight: 800,
              letterSpacing: '-0.02em',
              color: 'text.primary',
            }}
          >
            {t('landing.cardsSection.title')}
          </Typography>
          <Typography
            sx={{
              mt: 0.75,
              fontSize: '0.9rem',
              color: 'text.secondary',
              maxWidth: 540,
            }}
          >
            {t('landing.cardsSection.description')}
          </Typography>
        </Box>

        {/* Grid */}
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: {
              xs: '1fr',
              sm: 'repeat(2, 1fr)',
              lg: 'repeat(4, 1fr)',
            },
            gap: { xs: 2, md: 2.5 },
          }}
        >
          {LANDING_CARDS.map((card) => (
            <Box
              key={card.to}
              component={RouterLink}
              to={localizedPath(card.to)}
              sx={{
                position: 'relative',
                display: 'block',
                textDecoration: 'none',
                borderRadius: '12px',
                overflow: 'hidden',
                aspectRatio: '3 / 4',
                animation: `${fadeUp} 600ms ${100 + card.index * 80}ms ease both`,
                '@media (prefers-reduced-motion: reduce)': { animation: 'none' },
                '&:hover .card-img': { transform: 'scale(1.06)' },
                '&:hover .card-overlay': {
                  background: s.cardOverlayHover,
                },
                '&:focus-visible': {
                  outline: `2px solid ${theme.palette.primary.main}`,
                  outlineOffset: 3,
                },
              }}
            >
              {/* Photo */}
              <Box
                className="card-img"
                component="img"
                src={card.image}
                alt={t(card.titleKey)}
                sx={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover',
                  display: 'block',
                  transition: 'transform 550ms cubic-bezier(0.25, 0.46, 0.45, 0.94)',
                }}
              />

              {/* Gradient + text */}
              <Box
                className="card-overlay"
                sx={{
                  position: 'absolute',
                  inset: 0,
                  background: s.cardOverlay,
                  transition: 'background 350ms ease',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'flex-end',
                  p: 3,
                }}
              >
                <Typography
                  sx={{
                    fontSize: '0.65rem',
                    fontWeight: 600,
                    letterSpacing: '0.18em',
                    textTransform: 'uppercase',
                    color: 'rgba(255,255,255,0.6)',
                    mb: 0.75,
                  }}
                >
                  {t(card.eyebrowKey)}
                </Typography>
                <Typography
                  component="h3"
                  sx={{
                    fontWeight: 800,
                    fontSize: { xs: '1.15rem', md: '1.25rem' },
                    letterSpacing: '-0.02em',
                    lineHeight: 1.15,
                    color: '#fff',
                    mb: 1.5,
                  }}
                >
                  {t(card.titleKey)}
                </Typography>
                <Typography
                  sx={{
                    fontSize: '0.76rem',
                    fontWeight: 600,
                    letterSpacing: '0.06em',
                    color: 'rgba(255,255,255,0.72)',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 0.75,
                  }}
                >
                  {t(card.ctaKey)}&nbsp;→
                </Typography>
              </Box>
            </Box>
          ))}
        </Box>
      </Container>
    </Box>
  )
}

export default HomePage
