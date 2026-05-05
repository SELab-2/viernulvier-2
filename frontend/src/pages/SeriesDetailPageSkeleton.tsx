import { Box, Container, Divider, Paper, Skeleton, Stack } from '@mui/material'

const SeriesDetailPageSkeleton = () => {
  return (
    <Container maxWidth="lg" sx={{ py: 5 }}>
      <Stack spacing={4} data-testid="series-detail-skeleton">
        {/* Breadcrumbs */}
        <Box sx={{ pb: 1.5, borderBottom: 1, borderColor: 'divider' }}>
          <Skeleton variant="text" width="42%" height={26} />
        </Box>

        {/* Header */}
        <Stack spacing={1} sx={{ maxWidth: 760 }}>
          <Skeleton variant="text" width="46%" height={68} />
          <Skeleton variant="text" width="72%" height={26} />
          <Skeleton variant="text" width="90%" height={28} />
          <Skeleton variant="text" width="80%" height={28} />
        </Stack>

        {/* Stats */}
        <Stack
          direction="row"
          spacing={5}
          divider={<Divider orientation="vertical" flexItem />}
          sx={{ py: 1 }}
        >
          {Array.from({ length: 3 }).map((_, index) => (
            <Box key={index}>
              <Skeleton variant="text" width={64} height={52} />
              <Skeleton variant="text" width={80} height={24} />
            </Box>
          ))}
        </Stack>

        <Divider />

        {/* Section heading */}
        <Stack spacing={1}>
          <Skeleton variant="text" width="22%" height={52} />
          <Skeleton variant="text" width="60%" height={28} />
        </Stack>

        {/* Two-column layout: timeline left, production list right */}
        <Stack direction="row" spacing={4} sx={{ alignItems: 'flex-start' }}>
          {/* Timeline column */}
          <Stack spacing={3} sx={{ flexShrink: 0, pt: 0.5 }}>
            {Array.from({ length: 5 }).map((_, index) => (
              <Stack key={index} direction="row" sx={{ alignItems: 'center' }} spacing={1}>
                <Skeleton variant="circular" width={10} height={10} />
                <Skeleton variant="text" width={34} height={20} />
              </Stack>
            ))}
          </Stack>

          {/* Production list column */}
          <Stack spacing={2} sx={{ flex: 1, minWidth: 0 }}>
            {Array.from({ length: 5 }).map((_, index) => (
              <Paper key={index} elevation={0} sx={{ p: 2.5, borderRadius: 2 }}>
                <Skeleton variant="text" width="52%" height={36} sx={{ mb: 0.5 }} />
                <Skeleton variant="text" width="72%" height={26} sx={{ mb: 1 }} />
                <Skeleton variant="text" width="97%" height={22} />
                <Skeleton variant="text" width="90%" height={22} sx={{ mb: 1.5 }} />
                <Stack direction="row" spacing={1}>
                  <Skeleton variant="rounded" width={78} height={28} />
                </Stack>
              </Paper>
            ))}
          </Stack>
        </Stack>
      </Stack>
    </Container>
  )
}

export default SeriesDetailPageSkeleton
