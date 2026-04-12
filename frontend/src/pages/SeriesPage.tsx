import { Container, Typography, Paper, Stack, Link as MuiLink } from '@mui/material'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

const SeriesPage = () => {
  const { t } = useTranslation()

  // TODO: Fetch series list from API and display them here
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Stack spacing={3}>
        <Typography variant="h4" component="h1">
          {t('series.title')}
        </Typography>
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="body1" gutterBottom>
            {t('series.listPlaceholder')}
          </Typography>
          <Typography variant="body2" sx={{ mt: 2 }}>
            Example:{' '}
            <MuiLink component={Link} to="/series/10" underline="hover">
              View Series #10
            </MuiLink>
          </Typography>
        </Paper>
      </Stack>
    </Container>
  )
}

export default SeriesPage
