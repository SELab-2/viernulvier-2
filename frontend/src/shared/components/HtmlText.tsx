import { Box, Typography, type TypographyProps } from '@mui/material'

import { sanitizeHtml } from '../../utils/SanitizeHtml'

import type { ReactNode } from 'react'

/**
 * Props for HtmlText component.
 *
 * This component safely renders sanitized HTML content or falls back to
 * plain text / ReactNode content when HTML is empty or invalid.
 */
export interface HtmlTextProps {
  /**
   * Raw HTML string to render.
   * This will be sanitized before being injected into the DOM.
   */
  html: string

  /**
   * Optional fallback content shown when HTML is empty or invalid.
   * Can be a string or any ReactNode.
   */
  fallback?: ReactNode

  /**
   * MUI Typography variant used when rendering fallback strings.
   * @default "body1"
   */
  variant?: TypographyProps['variant']

  /**
   * Underlying HTML element used when rendering sanitized HTML.
   * @default "div"
   */
  component?: TypographyProps['component']

  /**
   * MUI sx styling applied to both HTML and fallback render paths.
   */
  sx?: TypographyProps['sx']
}

/**
 * HtmlText
 *
 * A safe HTML rendering component that:
 * - Sanitizes raw HTML before rendering
 * - Uses `dangerouslySetInnerHTML` only on sanitized content
 * - Provides flexible fallback rendering (string or ReactNode)
 *
 * Rendering logic:
 * 1. If sanitized HTML is non-empty -> render HTML inside a Box
 * 2. Else if fallback is string -> render Typography
 * 3. Else if fallback is ReactNode -> render as-is
 * 4. Else -> render null
 */
const HtmlText = ({ html, fallback, variant = 'body1', component = 'div', sx }: HtmlTextProps) => {
  const sanitizedHtml = sanitizeHtml(html ?? '')

  if (sanitizedHtml.trim()) {
    return <Box component={component} sx={sx} dangerouslySetInnerHTML={{ __html: sanitizedHtml }} />
  }

  if (fallback === undefined || fallback === null || fallback === '') {
    return null
  }

  if (typeof fallback === 'string') {
    return (
      <Typography component="p" variant={variant} sx={sx}>
        {fallback}
      </Typography>
    )
  }

  return <>{fallback}</>
}

export default HtmlText
