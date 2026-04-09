import { Button, Container, Paper, Stack, Typography, useTheme } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Link as RouterLink } from 'react-router-dom'
import { createCommonStyles } from '../theme/styles'
import { tokens } from '../theme/tokens'

const NotFoundPage = () => {
  const theme = useTheme()
  const commonStyles = createCommonStyles(theme)
  const { t } = useTranslation()

  return (
    <Container
      sx={{
        ...commonStyles.centerContent,
        mt: tokens.spacing.numeric3xl,
      }}
    >
      <Paper
        sx={{
          p: {
            xs: tokens.spacing.numericMd,
            sm: tokens.spacing.numericXl,
            md: tokens.spacing.numeric2xl,
          },
          borderRadius: tokens.card.borderRadius,
        }}
      >
        <Stack spacing={tokens.spacing.numericMd} alignItems="flex-start">
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
              px: tokens.spacing.numericLg,
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
