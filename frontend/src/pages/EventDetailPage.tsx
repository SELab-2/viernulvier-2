import { Container, Typography, Paper, Stack, Button } from '@mui/material'
import { useParams, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'

const EventDetailPage = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { t } = useTranslation()

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Stack spacing={3}>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/events')}>
          {t('events.backToEvents')}
        </Button>
        <Typography variant="h4" component="h1">
          {t('events.detailTitle')}: {id}
        </Typography>
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="body1">{t('events.detailPlaceholder', { id })}</Typography>
        </Paper>
      </Stack>
    </Container>
  )
}

export default EventDetailPage
