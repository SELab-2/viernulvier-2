import { Box, Paper, Skeleton, Stack } from '@mui/material'
import { useTheme } from '@mui/material/styles'

import { createCommonStyles } from '../../../theme/styles'
import { tokens } from '../../../theme/tokens'

import type { SearchViewMode } from '../search/types'

/**
 * CollectionResultsSkeleton
 *
 * Displays a loading placeholder for collection result pages (grid or list layout).
 * This is used while data is being fetched to avoid layout shift and improve perceived performance.
 *
 * Behavior:
 * - Switches between list and grid skeletons based on layout + mobile state
 * - Uses consistent card dimensions to match real result cards
 *
 * This component only renders UI placeholders, no data logic involved.
 */

interface CollectionResultsSkeletonProps {
  layout: SearchViewMode
  isMobile: boolean
  cards?: number
}

const CollectionResultsSkeleton = ({
  layout,
  isMobile,
  cards = 12,
}: CollectionResultsSkeletonProps) => {
  const theme = useTheme()

  // Shared grid layout styles used for consistency across collection pages
  const commonStyles = createCommonStyles(theme)

  // On mobile we always force grid layout regardless of passed layout prop
  const activeLayout: SearchViewMode = isMobile ? 'grid' : layout

  /**
   * LIST SKELETON
   * Used for vertical stacked results (e.g. mobile or list view mode)
   */
  if (activeLayout === 'list') {
    return (
      <Stack spacing={2} data-testid="collection-results-skeleton">
        {Array.from({ length: cards }).map((_, index) => (
          <Paper key={index} variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
            <Stack spacing={1.5}>
              {/* Title placeholder */}
              <Skeleton variant="text" width="45%" height={30} />

              {/* Secondary line placeholder */}
              <Skeleton variant="text" width="70%" height={24} />

              {/* Tertiary line placeholder */}
              <Skeleton variant="text" width="55%" height={22} />
            </Stack>
          </Paper>
        ))}
      </Stack>
    )
  }

  /**
   * GRID SKELETON
   * Used for card-based layouts with image + text structure
   */
  return (
    <Box
      data-testid="collection-results-skeleton"
      sx={{
        ...commonStyles.gridContainer,
        justifyContent: { xs: 'center', md: 'flex-start' },
      }}
    >
      {Array.from({ length: cards }).map((_, index) => (
        <Paper
          key={index}
          variant="outlined"
          sx={{
            width: { xs: '100%', sm: 350 },
            maxWidth: 350,
            minHeight: { xs: 300, sm: 335 },
            display: 'flex',
            flexDirection: 'column',
            borderRadius: tokens.card.borderRadius,
            overflow: 'hidden',
          }}
        >
          {/* Image placeholder */}
          <Skeleton
            variant="rectangular"
            sx={{
              width: '100%',
              height: { xs: 180, sm: 197 },
              flexShrink: 0,
            }}
          />

          {/* Text content placeholder */}
          <Box sx={{ p: tokens.spacing.numericLg, flex: 1 }}>
            <Skeleton variant="text" width="70%" height={30} />
            <Skeleton variant="text" width="55%" height={22} sx={{ mb: 1.5 }} />
            <Skeleton variant="text" width="45%" height={20} />
          </Box>
        </Paper>
      ))}
    </Box>
  )
}

export default CollectionResultsSkeleton
