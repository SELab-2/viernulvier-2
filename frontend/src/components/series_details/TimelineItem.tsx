/*
 * Represents a single item in a vertical timeline.
 *
 * Desktop: dot (with z-index above the line) + year to its right, card fills remaining width.
 * When the year label is omitted (same year as the previous item), the dot is omitted too;
 * an empty column preserves alignment with labeled rows.
 * Mobile: centered year separator with dividers matching card width, card centered below.
 */

import { Box, Stack, Typography } from '@mui/material'

import type { ReactNode } from 'react'

type Props = {
  year: string
  showYearLabel?: boolean
  children: ReactNode
}

export const DOT_CENTER_X = 5

const TimelineItem = ({ year, showYearLabel = true, children }: Props) => {
  return (
    <Stack
      direction={{ xs: 'column', md: 'row' }}
      sx={{ alignItems: { md: 'flex-start' }, gap: { md: 2 } }}
    >
      {showYearLabel ? (
        <Stack
          direction="row"
          sx={{
            display: { xs: 'none', md: 'flex' },
            flexShrink: 0,
            alignItems: 'center',
            gap: 1,
          }}
        >
          <Box
            sx={{
              width: DOT_CENTER_X * 2,
              height: DOT_CENTER_X * 2,
              borderRadius: '50%',
              bgcolor: 'text.primary',
              flexShrink: 0,
              position: 'relative',
              zIndex: 1,
            }}
          />
          <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1 }}>
            {year}
          </Typography>
        </Stack>
      ) : (
        <Box
          aria-hidden
          sx={{
            display: { xs: 'none', md: 'block' },
            flexShrink: 0,
            minWidth: (theme) => `calc(${DOT_CENTER_X * 2}px + ${theme.spacing(1)} + 4ch)`,
          }}
        />
      )}

      <Box sx={{ flex: 1, width: '100%', minWidth: 0 }}>
        {showYearLabel ? (
          <Stack
            direction="row"
            sx={{
              display: { xs: 'flex', md: 'none' },
              alignItems: 'center',
              gap: 2,
              maxWidth: 350,
              width: '100%',
              mx: 'auto',
              mb: 1.5,
            }}
          >
            <Box sx={{ flex: 1, height: '1px', bgcolor: 'divider' }} />
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ flexShrink: 0, lineHeight: 1 }}
            >
              {year}
            </Typography>
            <Box sx={{ flex: 1, height: '1px', bgcolor: 'divider' }} />
          </Stack>
        ) : null}

        <Box
          sx={{
            display: { xs: 'flex', md: 'block' },
            justifyContent: 'center',
          }}
        >
          {children}
        </Box>
      </Box>
    </Stack>
  )
}

export default TimelineItem
