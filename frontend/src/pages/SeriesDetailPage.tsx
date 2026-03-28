import { Container, Typography, Paper, Stack, Button, Chip, Divider, Box } from '@mui/material'
import { useNavigate, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'

const placeholderSeriesTag = {
  id: 12,
  type: 'theme',
  name: 'Hedendaags',
  url: '',
  source: '',
  source_type: '',
  is_external: false,
  is_enabled: true,
  short_description: null,
  url_title: '',
}

const SeriesDetailPage = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { t } = useTranslation()

  const series = placeholderSeriesTag

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Stack spacing={3}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/series')}
          sx={{ alignSelf: 'flex-start' }}
        >
          {t('series.backToSeries', { defaultValue: 'Back to series' })}
        </Button>

        <Box>
          <Typography variant="overline" color="text.secondary">
            {t('series.detailLabel', { defaultValue: 'Productiereeks' })}
          </Typography>
          <Typography variant="h4" component="h1" gutterBottom>
            {series.name}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {t('series.detailSubtitle', {
              defaultValue: 'Voorbeeldweergave van een detailpagina voor een reeks-tag.',
            })}
          </Typography>
        </Box>

        <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
          <Chip label={`${t('series.id', { defaultValue: 'ID' })}: ${series.id}`} />
          <Chip label={`${t('series.type', { defaultValue: 'Type' })}: ${series.type}`} />
          <Chip
            color={series.is_enabled ? 'success' : 'default'}
            label={
              series.is_enabled
                ? t('series.enabled', { defaultValue: 'Enabled' })
                : t('series.disabled', { defaultValue: 'Disabled' })
            }
          />
          <Chip
            color={series.is_external ? 'info' : 'default'}
            label={
              series.is_external
                ? t('series.external', { defaultValue: 'External' })
                : t('series.internal', { defaultValue: 'Internal' })
            }
          />
        </Stack>

        <Paper elevation={2} sx={{ p: 3 }}>
          <Stack spacing={2.5}>
            <Box>
              <Typography variant="h6" gutterBottom>
                {t('series.overview', { defaultValue: 'Overzicht' })}
              </Typography>
              <Typography variant="body1">
                {t('series.placeholderDescription', {
                  defaultValue:
                    'Deze pagina gebruikt tijdelijk een placeholder-tag uit een productie-instantie zodat je de lay-out kunt beoordelen voordat de echte API-koppeling is toegevoegd.',
                })}
              </Typography>
            </Box>

            <Divider />

            <Stack spacing={1.5}>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  {t('series.name', { defaultValue: 'Naam' })}
                </Typography>
                <Typography variant="body1">{series.name}</Typography>
              </Box>

              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  {t('series.tagType', { defaultValue: 'Tagtype' })}
                </Typography>
                <Typography variant="body1">{series.type}</Typography>
              </Box>

              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  {t('series.shortDescription', { defaultValue: 'Korte beschrijving' })}
                </Typography>
                <Typography variant="body1">
                  {series.short_description ??
                    t('series.noDescription', {
                      defaultValue: 'Geen korte beschrijving beschikbaar.',
                    })}
                </Typography>
              </Box>

              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  {t('series.source', { defaultValue: 'Bron' })}
                </Typography>
                <Typography variant="body1">
                  {series.source || t('common.notAvailable', { defaultValue: 'Niet beschikbaar' })}
                </Typography>
              </Box>

              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  {t('series.sourceType', { defaultValue: 'Brontype' })}
                </Typography>
                <Typography variant="body1">
                  {series.source_type ||
                    t('common.notAvailable', { defaultValue: 'Niet beschikbaar' })}
                </Typography>
              </Box>

              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  {t('series.routeParam', { defaultValue: 'Route parameter' })}
                </Typography>
                <Typography variant="body1">{id ?? '—'}</Typography>
              </Box>
            </Stack>
          </Stack>
        </Paper>
      </Stack>
    </Container>
  )
}

export default SeriesDetailPage