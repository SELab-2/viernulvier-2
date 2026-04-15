import { Box, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'

import { tokens } from '../../theme/tokens'
import sanitizeHtml from '../../utils/SanitizeHtml'

interface DescriptionProps {
  teaser: string
  description: string
}

/**
 * Production description block.
 *
 * Displays teaser and full description as sanitized HTML.
 * If no description is available, shows translated placeholder text.
 */
export default function Description({ teaser, description }: DescriptionProps) {
  const { t } = useTranslation()

  return (
    <Box
      className="production-description"
      sx={{ color: 'text.primary', background: 'transparent' }}
    >
      {teaser && (
        <Box
          sx={{
            fontSize: tokens.typography.sizes.base,
            lineHeight: 1.7,
            color: 'text.secondary',
            fontStyle: 'italic',
            mb: 2.5,
            '& img': {
              maxWidth: '100%',
              height: 'auto',
            },
          }}
          dangerouslySetInnerHTML={{ __html: sanitizeHtml(teaser) }}
        />
      )}

      {description ? (
        <Box
          sx={{
            fontSize: tokens.typography.sizes.sm,
            lineHeight: 1.8,
            color: 'text.primary',
            '& img': {
              maxWidth: '100%',
              height: 'auto',
            },
          }}
          dangerouslySetInnerHTML={{ __html: sanitizeHtml(description) }}
        />
      ) : (
        <Typography
          component="p"
          sx={{
            fontSize: tokens.typography.sizes.sm,
            color: 'text.secondary',
            fontStyle: 'italic',
            fontFamily: tokens.typography.fontFamily,
          }}
        >
          {t('productions.detail.noDescription', 'No description available.')}
        </Typography>
      )}
    </Box>
  )
}
