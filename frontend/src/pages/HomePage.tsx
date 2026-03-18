import { Container, Paper, Stack, Typography, Box } from '@mui/material'
import { useTranslation } from 'react-i18next'
import SearchBar from '../components/searchbar/SearchBar'
import Tag from '../components/Tag'

const HomePage = () => {
  const { t } = useTranslation()
  return (
    <Container maxWidth="md" sx={{ py: 6 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Stack spacing={3}>
          <Typography variant="h3" component="h1">
            {t('title')}
          </Typography>
          <Typography variant="subtitle1">{t('subtitle')}</Typography>
        </Stack>
        <Box sx={{ mt: 4 }}>
          <SearchBar />
        </Box>

        {/* Test tags for description and reeks context */}
        <Box sx={{ mt: 4, display: 'flex', gap: 2 }}>
          {/* Description tag example */}
          <Tag name="Festival" displayName="Festival" context="description" />
          {/* Reeks tag example */}
          <Tag name="VIDEODROOM" displayName="Reeks: VIDEODROOM" context="series" />
        </Box>
      </Paper>
    </Container>
  )
}

export default HomePage
