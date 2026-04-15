import { Box, Skeleton, useTheme } from '@mui/material'

const ProductionDetailPageSkeleton = () => {
  const theme = useTheme()

  return (
    <Box
      className="production-details-page"
      sx={{
        backgroundColor: theme.palette.background.default,
        color: theme.palette.text.primary,
      }}
      data-testid="production-detail-skeleton"
    >
      <Box
        className="production-details-container"
        sx={{ backgroundColor: theme.palette.background.default }}
      >
        <Box
          className="production-details-left"
          sx={{ backgroundColor: theme.palette.background.default }}
        >
          <Box sx={{ borderBottom: `1px solid ${theme.palette.divider}`, pb: 1.5, mb: 3 }}>
            <Skeleton variant="text" width="45%" height={24} />
          </Box>

          <Box
            className="hero-image"
            sx={{
              width: '100%',
              aspectRatio: '16/7',
              borderRadius: '4px',
              overflow: 'hidden',
              marginBottom: '32px',
            }}
          >
            <Skeleton variant="rectangular" width="100%" height="100%" />
          </Box>

          <Box sx={{ mb: 3 }}>
            <Skeleton variant="text" width="60%" height={44} />
            <Skeleton variant="text" width="40%" height={28} />
          </Box>

          <Box>
            <Skeleton variant="text" width="100%" height={30} />
            <Skeleton variant="text" width="97%" height={30} />
            <Skeleton variant="text" width="95%" height={30} />
            <Skeleton variant="text" width="98%" height={30} />
          </Box>
        </Box>

        <Box
          className="production-details-right"
          sx={{
            backgroundColor: theme.palette.background.default,
            borderLeft: `1px solid ${theme.palette.divider}`,
          }}
        >
          <Box sx={{ mb: 3 }}>
            <Skeleton variant="text" width="56%" height={46} />
            <Skeleton variant="text" width="68%" height={28} sx={{ mb: 2 }} />

            <Box sx={{ borderTop: `1px solid ${theme.palette.divider}`, mb: 0.5 }} />

            {Array.from({ length: 5 }).map((_, index) => (
              <Box
                key={index}
                sx={{
                  display: 'grid',
                  gridTemplateColumns: '130px 1fr',
                  gap: 1,
                  py: 1.75,
                  borderBottom: `1px solid ${theme.palette.divider}`,
                }}
              >
                <Skeleton variant="text" width={86} height={24} />
                <Skeleton variant="text" width={index === 1 ? '45%' : '60%'} height={24} />
              </Box>
            ))}

            <Box sx={{ display: 'flex', gap: 1, mt: 3, flexWrap: 'wrap' }}>
              <Skeleton variant="rounded" width={110} height={34} />
              <Skeleton variant="rounded" width={88} height={34} />
            </Box>
          </Box>

          <Box
            sx={(theme) => ({
              mt: 3,
              p: 2,
              border: `1px solid ${theme.palette.divider}`,
              backgroundColor: theme.palette.background.paper,
              borderRadius: '4px',
            })}
          >
            <Skeleton variant="text" width="40%" height={28} sx={{ mb: 1 }} />
            {Array.from({ length: 2 }).map((_, index) => (
              <Box
                key={index}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 1.5,
                  py: 1.2,
                  borderTop: index === 0 ? 'none' : `1px solid ${theme.palette.divider}`,
                }}
              >
                <Box sx={{ flex: 1 }}>
                  <Skeleton variant="text" width="44%" height={24} />
                  <Skeleton variant="text" width="66%" height={22} />
                </Box>
                <Skeleton variant="rounded" width={30} height={30} />
              </Box>
            ))}
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

export default ProductionDetailPageSkeleton
