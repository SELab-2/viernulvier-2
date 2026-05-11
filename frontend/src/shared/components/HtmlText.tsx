import { Box, Typography, type TypographyProps } from '@mui/material'
import type { ReactNode } from 'react'

import { sanitizeHtml } from '../../utils/SanitizeHtml'

export interface HtmlTextProps {
  html: string
  fallback?: ReactNode
  variant?: TypographyProps['variant']
  component?: TypographyProps['component']
  sx?: TypographyProps['sx']
}

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
