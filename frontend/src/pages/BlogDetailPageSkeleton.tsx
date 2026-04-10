import { Box, Skeleton, useTheme } from '@mui/material'

const BlogDetailPageSkeleton = () => {
  const theme = useTheme()

  return (
    <div
      className="blog-details-page"
      style={{
        backgroundColor: theme.palette.background.default,
        color: theme.palette.text.primary,
      }}
    >
      <div
        className="production-details-container"
        style={{ backgroundColor: theme.palette.background.default, gridTemplateColumns: '1fr' }}
      >
        <div
          className="production-details-left"
          style={{ backgroundColor: theme.palette.background.default }}
        >
          <Box sx={{ borderBottom: `1px solid ${theme.palette.divider}`, pb: 1.5, mb: 3 }}>
            <Skeleton variant="text" width="45%" height={24} />
          </Box>

          <div
            className="hero-image"
            style={{
              width: '100%',
              aspectRatio: '16/7',
              borderRadius: '4px',
              overflow: 'hidden',
              marginBottom: '32px',
            }}
          >
            <Skeleton variant="rectangular" width="100%" height="100%" />
          </div>

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
        </div>
      </div>

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
    </div>
  )
}

export default BlogDetailPageSkeleton
