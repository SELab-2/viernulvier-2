/*
 * Displays the main header section of a series detail page.
 *
 * Responsibilities:
 * - Renders series title (primary heading)
 * - Optionally renders an excerpt (short intro/summary)
 * - Renders full description (HTML-safe via HtmlText component)
 */

import { Stack, Typography } from '@mui/material'

import HtmlText from '../../../shared/components/HtmlText'

/**
 * Props for SeriesHeader component.
 */
type Props = {
  name: string
  excerpt?: string
  description: string
}

/**
 * Header section for series detail pages.
 * Combines title, optional excerpt, and full description.
 */
const SeriesHeader = ({ name, excerpt, description }: Props) => {
  return (
    <Stack spacing={2} sx={{ maxWidth: 760 }}>
      {/* Series title */}
      <Typography variant="h3" sx={{ fontWeight: 800, overflowWrap: 'break-word' }}>
        {name}
      </Typography>

      {/* Optional excerpt */}
      {excerpt ? (
        <HtmlText
          html={excerpt}
          variant="body1"
          component="div"
          sx={{
            color: 'text.secondary',
            overflowWrap: 'break-word',
            fontSize: 'inherit',
            fontStyle: 'italic',
          }}
        />
      ) : null}

      {/* Full description */}
      <HtmlText
        html={description}
        variant="body1"
        component="div"
        sx={{
          color: 'text.secondary',
          overflowWrap: 'break-word',
          fontSize: 'inherit',
        }}
      />
    </Stack>
  )
}

export default SeriesHeader
