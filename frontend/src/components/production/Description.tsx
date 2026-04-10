import { Box, useTheme } from '@mui/material'
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
  const theme = useTheme()
  const { t } = useTranslation()

  return (
    <div
      className="production-description"
      style={{
        color: theme.palette.text.primary,
        background: 'transparent',
      }}
    >
      {teaser && (
        <Box
          sx={{
            fontSize: '1.05rem',
            lineHeight: 1.7,
            color: theme.palette.text.secondary,
            fontStyle: 'italic',
            marginBottom: '20px',
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
            fontSize: '0.95rem',
            lineHeight: 1.8,
            color: theme.palette.text.primary,
            '& img': {
              maxWidth: '100%',
              height: 'auto',
            },
          }}
          dangerouslySetInnerHTML={{ __html: sanitizeHtml(description) }}
        />
      ) : (
        <p
          style={{
            fontSize: '0.9rem',
            color: tokens.colors.neutral.gray400,
            fontStyle: 'italic',
            fontFamily: tokens.typography.fontFamily,
          }}
        >
          {t('productions.detail.noDescription', 'No description available.')}
        </p>
      )}
    </div>
  )
}
