import { Box, Skeleton, useTheme } from '@mui/material'

import { tokens } from '../../../theme/tokens'

const BlogDetailPageSkeleton = () => {
  const theme = useTheme()

  return (
    <Box
      className="blog-details-page"
      sx={(theme) => ({
        backgroundColor: theme.palette.background.default,
        color: theme.palette.text.primary,
      })}
    >
      <Box
        className="production-details-container"
        sx={(theme) => ({
          display: 'grid',
          gridTemplateColumns: '1fr',
          backgroundColor: theme.palette.background.default,
        })}
      >
        <Box
          className="production-details-left"
          sx={(theme) => ({ backgroundColor: theme.palette.background.default })}
        >
          <Box sx={{ borderBottom: `1px solid ${theme.palette.divider}`, pb: 1.5, mb: 3 }}>
            <Skeleton variant="text" width="45%" height={24} />
          </Box>

          <Box
            className="hero-image"
            sx={{
              width: '100%',
              aspectRatio: '16 / 7',
              borderRadius: tokens.borderRadius.sm,
              overflow: 'hidden',
              mb: 4,
            }}
          >
            <Skeleton variant="rectangular" width="100%" height="100%" />
          </Box>

          <Box sx={{ mb: 3 }}>
            <Skeleton variant="text" width={180} height={24} />
            <Skeleton variant="text" width="55%" height={48} />
          </Box>

          <Box>
            <Skeleton variant="text" width="100%" height={30} />
            <Skeleton variant="text" width="98%" height={30} />
            <Skeleton variant="text" width="96%" height={30} />
            <Skeleton variant="text" width="93%" height={30} />
            <Skeleton variant="text" width="95%" height={30} />
          </Box>
        </Box>
      </Box>

      <Box sx={{ p: 2, width: '100%', maxWidth: 1250, mx: 'auto', pb: 4 }}>
        <Skeleton variant="text" width={220} height={36} sx={{ mb: 1 }} />
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: 2,
          }}
        >
          <Skeleton variant="rectangular" height={160} />
          <Skeleton variant="rectangular" height={160} />
          <Skeleton variant="rectangular" height={160} />
        </Box>
      </Box>
    </Box>
  )
}

export default BlogDetailPageSkeleton
