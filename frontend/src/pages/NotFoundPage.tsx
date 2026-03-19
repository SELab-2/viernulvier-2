import { Button, Container, Paper, Stack, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Link as RouterLink } from 'react-router-dom'

const NotFoundPage = () => {
  const { t } = useTranslation()

  return (
    <Container
      sx={{
        display: 'flex',
        justifyContent: 'center',
        mt: 8,
      }}
    >
      <Paper
        sx={{
          p: { xs: 2, sm: 4, md: 6 },
          borderRadius: 4,
        }}
      >
        <Stack spacing={2} alignItems="flex-start">
          <Typography variant="h4" fontWeight="bold">
            {t('notFound.title')}
          </Typography>

          <Typography variant="body1" color="text.secondary">
            {t('notFound.description')}
          </Typography>

          <Button
            component={RouterLink}
            to="/"
            variant="outlined"
            sx={(theme) => ({
              px: 3,
              borderColor: theme.palette.text.primary,
              color: theme.palette.text.primary,
              '&:hover': {
                borderColor: theme.palette.text.primary,
                bgcolor: theme.palette.action.hover,
              },
            })}
          >
            {t('notFound.backHome')}
          </Button>
        </Stack>
      </Paper>
    </Container>
  )
}

export default NotFoundPage
