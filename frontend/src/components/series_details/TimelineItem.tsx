/*
 * Represents a single item in a vertical timeline.
 * Displays a year marker and renders child content (e.g. a card).
 */

import { Box, Stack, Typography } from '@mui/material'
import type { ReactNode } from 'react'

type Props = {
  year: string
  children: ReactNode
}

const TimelineItem = ({ year, children }: Props) => {
  return (
    <Stack
      direction={{ xs: 'column', md: 'row' }}
      spacing={2}
      alignItems={{ xs: 'flex-start', md: 'flex-start' }}
      sx={{ position: 'relative' }}
    >
      {/* Timeline marker + year */}
      <Stack
        direction={{ xs: 'row', md: 'column' }}
        spacing={1}
        alignItems="center"
        sx={{ width: { xs: 'auto', md: 40 }, flexShrink: 0 }}
      >
        {/* Dot (only visible on desktop) */}
        <Box
          sx={{
            width: 10,
            height: 10,
            borderRadius: '50%',
            bgcolor: 'text.primary',
            display: { xs: 'none', md: 'block' },
            mt: 2,
          }}
        />

        {/* Year label */}
        <Typography variant="body2" color="text.secondary" sx={{ minWidth: 44 }}>
          {year}
        </Typography>
      </Stack>

      {/* Content (e.g. ProductionCard) */}
      <Box sx={{ flex: 1, width: '100%', minWidth: 0 }}>{children}</Box>
    </Stack>
  )
}

export default TimelineItem
