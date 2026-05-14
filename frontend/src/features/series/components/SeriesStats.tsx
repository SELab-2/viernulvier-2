/*
 * Displays a row of key statistics for a series.
 * Switches between a single column (small screens) and a single row (larger screens).
 *
 * This component is purely presentational:
 * - It expects precomputed stats from the parent
 * - It does not perform any formatting or data fetching
 * - It only handles responsive layout + display logic
 */

import { Box, Divider, Stack, Typography } from '@mui/material'

/**
 * Single statistic entry displayed in the UI.
 */
type Stat = {
  value: string
  label: string
}

/**
 * Props for SeriesStats component.
 */
type Props = {
  stats: Stat[]
}

/**
 * Renders a responsive list of series-related statistics.
 * Used in series detail pages to display aggregated metadata
 * such as number of editions, time range, and type.
 */
const SeriesStats = ({ stats }: Props) => {
  return (
    <Stack
      direction={{ xs: 'column', sm: 'row' }}
      spacing={{ xs: 2, sm: 5 }}
      divider={
        <Divider orientation="vertical" flexItem sx={{ display: { xs: 'none', sm: 'block' } }} />
      }
      sx={{ py: 1 }}
    >
      {stats.map((stat) => (
        <Box key={stat.value + stat.label}>
          {/* Value (primary metric) */}
          <Typography variant="h4" sx={{ fontWeight: 800 }}>
            {stat.value}
          </Typography>

          {/* Label (description of metric) */}
          <Typography variant="body2" color="text.secondary">
            {stat.label}
          </Typography>
        </Box>
      ))}
    </Stack>
  )
}

export default SeriesStats
