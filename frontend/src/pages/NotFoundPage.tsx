import { Button, Container, Paper, Stack, Typography, useTheme } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Link as RouterLink, useLocation } from 'react-router-dom'

import { createCommonStyles } from '../theme/styles'
import { tokens } from '../theme/tokens'
import { resolveCurrentLanguage, toLocalizedPath } from '../utils/localizedRoutes'

/**
 * NotFoundPage
 *
 * Fallback route page displayed when a user navigates to an unknown route.
 *
 * Responsibilities:
 * - Shows localized 404 content
 * - Provides navigation back to the localized home page
 * - Respects current language routing context
 */
const NotFoundPage = () => {
  const theme = useTheme()

  /**
   * Shared layout styles used across pages for consistent centering behavior.
   */
  const commonStyles = createCommonStyles(theme)

  const location = useLocation()
  const { t, i18n } = useTranslation()

  /**
   * Resolve correct language based on:
   * - current URL path
   * - i18n current language
   * - i18n resolved language
   */
  const currentLanguage = resolveCurrentLanguage(
    location.pathname,
    i18n.language,
    i18n.resolvedLanguage,
  )

  /**
   * Localized home route used for the "back to home" button.
   */
  const homePath = toLocalizedPath('/', currentLanguage)

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
        <Stack spacing={tokens.spacing.numericMd} sx={{ alignItems: 'flex-start' }}>
          {/* Page title */}
          <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
            {t('notFound.title')}
          </Typography>

          {/* Description text */}
          <Typography variant="body1" color="text.secondary">
            {t('notFound.description')}
          </Typography>

          {/* Navigation back button */}
          <Button
            component={RouterLink}
            to={homePath}
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
