import { useTheme } from '@mui/material'
import { useTranslation } from 'react-i18next'
import sanitizeHtml from '../../utils/SanitizeHtml'

interface DescriptionProps {
  teaser: string
  description: string
}

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
        <div
          style={{
            fontSize: '1.05rem',
            lineHeight: 1.7,
            color: theme.palette.text.secondary,
            fontStyle: 'italic',
            marginBottom: '20px',
          }}
          dangerouslySetInnerHTML={{ __html: sanitizeHtml(teaser) }}
        />
      )}

      {description ? (
        <div
          style={{
            fontSize: '0.95rem',
            lineHeight: 1.8,
            color: theme.palette.text.primary,
          }}
          dangerouslySetInnerHTML={{ __html: sanitizeHtml(description) }}
        />
      ) : (
        <p
          style={{
            fontSize: '0.9rem',
            color: '#bbb',
            fontStyle: 'italic',
            fontFamily: 'sans-serif',
          }}
        >
          {t('productions.detail.noDescription', 'No description available.')}
        </p>
      )}
    </div>
  )
}
