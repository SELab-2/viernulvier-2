import { Box, Skeleton, Stack } from '@mui/material'

const MediaFilesPageSkeleton = () => {
  return (
    <Box sx={{ p: { xs: 2, md: 3 } }}>
      <Stack spacing={3}>
        {/* Title */}
        <Stack spacing={1}>
          <Skeleton width={220} height={40} />
          <Skeleton width={320} />
        </Stack>

        {/* Filters / controls */}
        <Stack direction="row" spacing={2}>
          <Skeleton variant="rounded" width={140} height={40} />
          <Skeleton variant="rounded" width={140} height={40} />
          <Skeleton variant="rounded" width={100} height={40} />
        </Stack>

        {/* Grid */}
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: {
              xs: '1fr',
              sm: 'repeat(2, 1fr)',
              md: 'repeat(3, 1fr)',
              lg: 'repeat(4, 1fr)',
            },
            gap: 3,
          }}
        >
          {Array.from({ length: 8 }).map((_, i) => (
            <Stack key={i} spacing={1.5}>
              <Skeleton variant="rectangular" height={180} />
              <Skeleton width="80%" />
              <Skeleton width="60%" />
            </Stack>
          ))}
        </Box>
      </Stack>
    </Box>
  )
}

export default MediaFilesPageSkeleton
