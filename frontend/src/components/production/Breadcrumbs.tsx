import { Box } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { useLocation, useNavigate } from 'react-router-dom'

import { tokens } from '../../theme/tokens'
import {
  DEFAULT_LANGUAGE,
  getLanguageFromPathname,
  normalizeLanguage,
  toLocalizedPath,
} from '../../utils/localizedRoutes'

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
  const { t, i18n } = useTranslation()
  const location = useLocation()
  const currentLanguage =
    getLanguageFromPathname(location.pathname) ??
    normalizeLanguage(i18n.resolvedLanguage ?? i18n.language) ??
    DEFAULT_LANGUAGE

  const renderText = (item: BreadcrumbItem) => {
    if (item.translationKey) {
      return t(item.translationKey, item.label)
    }
    return item.label
  }

  return (
    <Box
      className="breadcrumbs"
      component="nav"
      sx={(theme) => ({
        pb: 1.5,
        fontSize: tokens.typography.sizes.sm,
        color: theme.palette.text.secondary,
        background: 'transparent',
        borderBottom: `1px solid ${theme.palette.divider}`,
        fontFamily: tokens.typography.fontFamily,
      })}
    >
      {items.map((item, index) => {
        const text = renderText(item)
        const isLast = index === items.length - 1

        if (isLast) {
          return (
            <Box component="span" key={`${item.label}-${index}`} sx={{ color: 'text.primary' }}>
              {text}
            </Box>
          )
        }

        return (
          <Box component="span" key={`${item.label}-${index}`}>
            <Box
              component="button"
              onClick={() => {
                if (item.to) {
                  navigate(toLocalizedPath(item.to, currentLanguage))
                }
              }}
              disabled={!item.to}
              sx={(theme) => ({
                background: 'none',
                border: 'none',
                p: 0,
                m: 0,
                color: theme.palette.primary.main,
                cursor: item.to ? 'pointer' : 'default',
                textDecoration: item.to ? 'underline' : 'none',
                font: 'inherit',
              })}
            >
              {text}
            </Box>
            {separator}
          </Box>
        )
      })}
    </Box>
  )
}
