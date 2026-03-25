import { useTranslation } from 'react-i18next'
import sanitizeHtml from '../../utils/SanitizeHtml'

interface DescriptionProps {
  teaser: string
  description: string
}

export default function Description({ teaser, description }: DescriptionProps) {
  const { t } = useTranslation()

  return (
    <div className="production-description">
      {teaser && (
        <div
          style={{
            fontSize: '1.05rem',
            lineHeight: 1.7,
            color: '#333',
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
            color: '#444',
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
