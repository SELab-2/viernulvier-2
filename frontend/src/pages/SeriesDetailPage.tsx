import { Box, Button, Container, Divider, Stack, Typography } from '@mui/material'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import { useNavigate, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import SeriesHeader from '../components/series_details/SeriesHeader'
import SeriesStats from '../components/series_details/SeriesStats'
import ProductionCard from '../components/series_details/ProductionCard'
import TimelineItem from '../components/series_details/TimelineItem'

// TODO: Fetch series and productions from API instead of using hardcoded placeholder data.

type LocalizedText = {
  nl: string
  en: string
}

type PlaceholderProduction = {
  id: number
  year: string
  title: LocalizedText
  meta: LocalizedText
  description: LocalizedText
  tags: LocalizedText[]
  image: string
}

const placeholderSeries: {
  id: number
  type: string
  name: LocalizedText
  description: LocalizedText
  badge: LocalizedText
  stats: { value: string; label: LocalizedText }[]
  productions: PlaceholderProduction[]
} = {
  id: 12,
  type: 'theme',
  name: {
    nl: 'VIDEODROOM',
    en: 'VIDEODROOM',
  },
  description: {
    nl: 'Het audiovisuele festival dat de grenzen tussen muziek, beeld en performance verkent. Sinds 2013 brengt VIDEODROOM vernieuwende artiesten, live visuals en meeslepende clubnachten samen in één terugkerende reeks.',
    en: 'The audiovisual festival that explores the boundaries between music, image and performance. Since 2013, VIDEODROOM has brought together groundbreaking artists, live visuals and immersive club nights in one recurring series.',
  },
  badge: {
    nl: 'Terugkerende reeks',
    en: 'Recurring series',
  },
  stats: [
    {
      value: '11',
      label: { nl: 'Edities', en: 'Editions' },
    },
    {
      value: '2013–2024',
      label: { nl: 'Periode', en: 'Period' },
    },
    {
      value: '150+',
      label: { nl: 'Artiesten', en: 'Artists' },
    },
  ],
  productions: [
    {
      id: 101,
      year: '2024',
      title: {
        nl: 'VIDEODROOM 2024',
        en: 'VIDEODROOM 2024',
      },
      meta: {
        nl: '11e editie · 3–5 mei 2024 · Multiple locations',
        en: '11th edition · 3–5 May 2024 · Multiple locations',
      },
      description: {
        nl: 'De 11e editie bracht opnieuw cutting-edge elektronische muziek en visuele kunst samen, met headline sets, live cinema en nachtelijke performances verspreid over verschillende zalen.',
        en: 'The 11th edition once again brought together cutting-edge electronic music and visual art, with headline sets, live cinema and late-night performances spread across multiple venues.',
      },
      tags: [
        { nl: 'Festival', en: 'Festival' },
        { nl: 'Audiovisueel', en: 'Audiovisual' },
        { nl: '3 dagen', en: '3 days' },
        { nl: '25 artiesten', en: '25 artists' },
      ],
      image:
        'https://images.unsplash.com/photo-1501386761578-eac5c94b800a?auto=format&fit=crop&w=1200&q=80',
    },
    {
      id: 102,
      year: '2023',
      title: {
        nl: 'VIDEODROOM 2023',
        en: 'VIDEODROOM 2023',
      },
      meta: {
        nl: '10e editie (jubileum) · 12–14 mei 2023 · Multiple locations',
        en: '10th edition (anniversary) · 12–14 May 2023 · Multiple locations',
      },
      description: {
        nl: 'De jubileumeditie vierde tien jaar VIDEODROOM met een uitgebreid programma vol elektronische muziek, installaties en speciale gastperformances.',
        en: 'The anniversary edition celebrated ten years of VIDEODROOM with an expanded programme full of electronic music, installations and special guest performances.',
      },
      tags: [
        { nl: 'Festival', en: 'Festival' },
        { nl: 'Jubileumeditie', en: 'Anniversary edition' },
        { nl: '3 dagen', en: '3 days' },
        { nl: '30 artiesten', en: '30 artists' },
      ],
      image:
        'https://images.unsplash.com/photo-1516280440614-37939bbacd81?auto=format&fit=crop&w=1200&q=80',
    },
    {
      id: 103,
      year: '2022',
      title: {
        nl: 'VIDEODROOM 2022',
        en: 'VIDEODROOM 2022',
      },
      meta: {
        nl: '9e editie · 6–8 mei 2022 · Multiple locations',
        en: '9th edition · 6–8 May 2022 · Multiple locations',
      },
      description: {
        nl: 'Na een tussenperiode keerde VIDEODROOM terug met een focus op hybride performances, experimentele concertformats en immersieve scenografie.',
        en: 'After a break, VIDEODROOM returned with a focus on hybrid performances, experimental concert formats and immersive scenography.',
      },
      tags: [
        { nl: 'Festival', en: 'Festival' },
        { nl: 'Live visuals', en: 'Live visuals' },
        { nl: '3 dagen', en: '3 days' },
        { nl: '20 artiesten', en: '20 artists' },
      ],
      image:
        'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?auto=format&fit=crop&w=1200&q=80',
    },
  ],
}

function getLocalizedValue(value: LocalizedText, language: string): string {
  const normalizedLanguage = language.startsWith('en') ? 'en' : 'nl'
  return value[normalizedLanguage]
}

const SeriesDetailPage = () => {
  useParams<{ id: string }>()
  const navigate = useNavigate()
  const { t, i18n } = useTranslation()

  const series = placeholderSeries
  const seriesName = getLocalizedValue(series.name, i18n.language)
  const seriesDescription = getLocalizedValue(series.description, i18n.language)
  const seriesBadge = getLocalizedValue(series.badge, i18n.language)

  const localizedStats = series.stats.map((stat) => ({
    value: stat.value,
    label: getLocalizedValue(stat.label, i18n.language),
  }))

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

          <Typography variant="body2" color="text.secondary">
            {t('series.breadcrumb', {
              defaultValue: `Archief / Reeksen / ${seriesName}`,
            })}
          </Typography>
        </Stack>

        <SeriesHeader name={seriesName} description={seriesDescription} badge={seriesBadge} />

        <SeriesStats stats={localizedStats} />

        <Divider />

        <Stack spacing={1}>
          <Typography variant="h4" component="h2" sx={{ fontWeight: 700 }}>
            {t('series.allEditions')}
          </Typography>

          <Typography variant="body2" color="text.secondary">
            {t('series.allEditionsSubtitle')}
          </Typography>
        </Stack>

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

          {series.productions.map((production) => (
            <TimelineItem key={production.id} year={production.year}>
              <ProductionCard
                title={getLocalizedValue(production.title, i18n.language)}
                meta={getLocalizedValue(production.meta, i18n.language)}
                description={getLocalizedValue(production.description, i18n.language)}
                tags={production.tags.map((tag) => getLocalizedValue(tag, i18n.language))}
                image={production.image}
              />
            </TimelineItem>
          ))}
        </Stack>

        <Typography variant="caption" color="text.secondary">
          {t('series.placeholderNote', {
            defaultValue:
              'Placeholder-detailpagina, opgebouwd met voorbeeldproducties tot de API-koppeling klaar is.',
          })}
        </Typography>
      </Stack>
    </Container>
  )
}

export default SeriesDetailPage
