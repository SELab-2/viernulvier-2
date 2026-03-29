import { useNavigate } from 'react-router-dom'
import { useTheme } from '@mui/material'
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

/**
 * Breadcrumbs component for page navigation hierarchy.
 *
 * props:
 * - items: breadcrumb path entries in order from home to current page.
 * - separator: string shown between segments.
 *
 * Behavior:
 * - last item is shown as current page label not clickable.
 * - intermediate items are rendered as buttons when `to` is provided.
 * - each item can optionally be translated via `translationKey`.
 */
export default function Breadcrumbs({ items, separator = ' / ' }: BreadcrumbsProps) {
  const navigate = useNavigate()
  const theme = useTheme()
  const { t } = useTranslation()

  const renderText = (item: BreadcrumbItem) => {
    if (item.translationKey) {
      return t(item.translationKey, item.label)
    }
    return item.label
  }

  return (
    <div
      className="breadcrumbs"
      style={{
        paddingBottom: '12px',
        fontSize: '0.90rem',
        color: theme.palette.text.secondary,
        background: 'transparent',
        borderBottom: `1px solid ${theme.palette.divider}`,
        fontFamily: "'Helvetica Neue', Arial, sans-serif",
      }}
    >
      {items.map((item, index) => {
        const text = renderText(item)
        const isLast = index === items.length - 1

        if (isLast) {
          return (
            <span key={`${item.label}-${index}`} style={{ color: theme.palette.text.primary }}>
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
                color: theme.palette.primary.main,
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
