import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

export interface BreadcrumbItem {
  label: string
  translationKey?: string
  to?: string
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[]
  separator?: string
}

export default function Breadcrumbs({ items, separator = ' / ' }: BreadcrumbsProps) {
  const navigate = useNavigate()
  const { t } = useTranslation()

  const renderText = (item: BreadcrumbItem) => {
    if (item.translationKey) {
      return t(item.translationKey, item.label)
    }
    return item.label
  }

  return (
    <div
      style={{
        paddingBottom: '12px',
        fontSize: '0.90rem',
        color: '#999',
        borderBottom: '1px solid #ebebeb',
        fontFamily: "'Helvetica Neue', Arial, sans-serif",
      }}
    >
      {items.map((item, index) => {
        const text = renderText(item)
        const isLast = index === items.length - 1

        if (isLast) {
          return (
            <span key={`${item.label}-${index}`} style={{ color: '#111' }}>
              {text}
            </span>
          )
        }

        return (
          <span key={`${item.label}-${index}`}>
            <button
              onClick={() => {
                if (item.to) navigate(item.to)
              }}
              disabled={!item.to}
              style={{
                background: 'none',
                border: 'none',
                padding: 0,
                margin: 0,
                color: '#999',
                cursor: item.to ? 'pointer' : 'default',
                textDecoration: item.to ? 'underline' : 'none',
                font: 'inherit',
              }}
            >
              {text}
            </button>
            {separator}
          </span>
        )
      })}
    </div>
  )
}
