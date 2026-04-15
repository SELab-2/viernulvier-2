import { Container, Typography, Paper, Stack, Link as MuiLink } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

const ArtistsPage = () => {
  const { t } = useTranslation()

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Stack spacing={3}>
        <Typography variant="h4" component="h1">
          {t('productions.title')}
        </Typography>
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="body1" gutterBottom>
            {t('productions.listPlaceholder')}
          </Typography>
          <Typography variant="body2" sx={{ mt: 2 }}>
            Example:{' '}
            <MuiLink component={Link} to="/artists/456" underline="hover">
              View Artist #456
            </MuiLink>
          </Typography>
        </Paper>
      </Stack>
    </Container>
  )
}

export default ArtistsPage
