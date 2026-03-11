import { Container, Paper, Stack, Typography } from '@mui/material'
import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from '../services/api'

const HomePage = () => {
  const { t } = useTranslation()

  useEffect( () => {
    const fetchData = async() => {
      try {
        const data = await api.get("/events/");
        console.log(data.data);
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    }
    
    fetchData();
  }, []);

  return (
    <Container maxWidth="md" sx={{ py: 6 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Stack spacing={3}>
          <Typography variant="h3" component="h1">
            {t('title')}
          </Typography>
          <Typography variant="subtitle1">{t('subtitle')}</Typography>
        </Stack>
      </Paper>
    </Container>
  )
}

export default HomePage
