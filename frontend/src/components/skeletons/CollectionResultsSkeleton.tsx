import { Box, Paper, Skeleton, Stack } from '@mui/material'
import type { SearchViewMode } from '../searchbar/types'
import { createCommonStyles } from '../../theme/styles'
import { tokens } from '../../theme/tokens'
import { useTheme } from '@mui/material/styles'

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
  const commonStyles = createCommonStyles(theme)
  const activeLayout: SearchViewMode = isMobile ? 'grid' : layout

  if (activeLayout === 'list') {
    return (
      <Stack spacing={2} data-testid="collection-results-skeleton">
        {Array.from({ length: cards }).map((_, index) => (
          <Paper key={index} variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
            <Stack spacing={1.5}>
              <Skeleton variant="text" width="45%" height={30} />
              <Skeleton variant="text" width="70%" height={24} />
              <Skeleton variant="text" width="55%" height={22} />
            </Stack>
          </Paper>
        ))}
      </Stack>
    )
  }

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
          <Skeleton
            variant="rectangular"
            sx={{
              width: '100%',
              height: { xs: 180, sm: 197 },
              flexShrink: 0,
            }}
          />
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
