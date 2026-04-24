import { Box, Typography, type TypographyProps } from '@mui/material'
import { isValidElement, type ReactNode } from 'react'

import sanitizeHtml from '../utils/SanitizeHtml'

interface HtmlTextProps extends Omit<TypographyProps, 'children'> {
  /**
   * HTML content to render safely.
   * If empty or falsy, renders the fallback element instead.
   */
  html?: string
  /**
   * Optional fallback text when html is empty.
   * Rendered as a Typography with `color="text.secondary"` and `fontStyle="italic"` by default.
   */
  fallback?: ReactNode
  /**
   * Additional sx styles applied to the rendered Box (or Typography if fallback is shown).
   */
  sx?: TypographyProps['sx']
}

/**
 * Safely renders HTML content with optional fallback.
 *
 * Uses DOMPurify to sanitize HTML before rendering via dangerouslySetInnerHTML.
 * If html is empty/falsy, renders the fallback element instead.
 * Automatically styles images to be responsive (max-width 100%, height auto).
 *
 * @example
 * // Render HTML with no fallback
 * <HtmlText html={description} />
 *
 * @example
 * // Render HTML with fallback text
 * <HtmlText html={excerpt} fallback={<Typography>No excerpt available</Typography>} />
 *
 * @example
 * // With custom typography props
 * <HtmlText html={content} variant="body2" component="div" fallback="No content" />
 */
export default function HtmlText({
  html,
  fallback,
  component = 'div',
  variant,
  sx,
  ...props
}: HtmlTextProps) {
  if (!html?.trim()) {
    // Render fallback if html is empty
    if (fallback) {
      // If fallback is already a node, return it as-is
      if (isValidElement(fallback)) {
        return fallback
      }
      // Otherwise wrap fallback string in Typography
      return (
        <Typography
          variant={variant}
          component={component}
          color="text.secondary"
          sx={{
            fontStyle: 'italic',
            ...sx,
          }}
          {...props}
        >
          {fallback}
        </Typography>
      )
    }
    return null
  }

  // Render sanitized HTML
  return (
    <Box
      component={component}
      sx={{
        '& img': {
          maxWidth: '100%',
          height: 'auto',
        },
        ...sx,
      }}
      dangerouslySetInnerHTML={{ __html: sanitizeHtml(html) }}
      {...props}
    />
  )
}
