import { Button, Container, Paper, Stack, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'
import './App.css'

const App = () => {
  const { t, i18n } = useTranslation()

  const switchLanguage = (language: 'en' | 'nl') => {
    i18n.changeLanguage(language)
  }

  return (
    <Container className="app" maxWidth="md">
      <Paper className="app-card" elevation={3}>
        <Stack spacing={2}>
          <Typography variant="h3" component="h1">
            {t('title')}
          </Typography>
          <Typography variant="subtitle1">{t('subtitle')}</Typography>
          <Stack direction="row" spacing={1}>
            <Button variant="contained" onClick={() => switchLanguage('en')}>
              {t('english')}
            </Button>
            <Button variant="outlined" onClick={() => switchLanguage('nl')}>
              {t('dutch')}
            </Button>
          </Stack>
        </Stack>
      </Paper>
    </Container>
  )
}

export default App
