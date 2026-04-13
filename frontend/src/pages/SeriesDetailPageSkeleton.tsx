import { Box, Container, Divider, Paper, Skeleton, Stack } from '@mui/material'

const SeriesDetailPageSkeleton = () => {
  return (
    <Container
      maxWidth="lg"
      sx={{ py: { xs: 3, md: 5 }, px: { xs: 2, sm: 3 }, overflowX: 'hidden' }}
    >
      <Stack spacing={3} data-testid="series-detail-skeleton">
        <Box sx={{ pb: 1.5, borderBottom: 1, borderColor: 'divider' }}>
          <Skeleton variant="text" width="42%" height={26} />
        </Box>

        <Stack spacing={1}>
          <Skeleton variant="text" width="46%" height={68} />
          <Skeleton variant="text" width="90%" height={32} />
          <Skeleton variant="text" width="80%" height={32} />
        </Stack>

        <Stack
          direction={{ xs: 'column', sm: 'row' }}
          spacing={{ xs: 2, sm: 5 }}
          divider={
            <Divider
              orientation="vertical"
              flexItem
              sx={{ display: { xs: 'none', sm: 'block' } }}
            />
          }
          sx={{ py: 1, width: 'fit-content', minWidth: { xs: '100%', sm: 'auto' } }}
        >
          {Array.from({ length: 3 }).map((_, index) => (
            <Box key={index} sx={{ minWidth: { xs: '100%', sm: 110 }, maxWidth: 170 }}>
              <Skeleton variant="text" width={64} height={52} />
              <Skeleton variant="text" width="70%" height={24} />
            </Box>
          ))}
        </Stack>

        <Divider />

        <Stack spacing={1}>
          <Skeleton variant="text" width="22%" height={52} />
          <Skeleton variant="text" width="70%" height={30} />
        </Stack>

        <Stack spacing={3} sx={{ position: 'relative', pl: { xs: 0, md: 3 } }}>
          <Box
            sx={{
              position: 'absolute',
              left: 11,
              top: 10,
              bottom: 10,
              width: '1px',
              bgcolor: 'divider',
              display: { xs: 'none', md: 'block' },
            }}
          />
          {Array.from({ length: 8 }).map((_, index) => (
            <Stack
              key={index}
              direction={{ xs: 'column', md: 'row' }}
              spacing={2}
              alignItems={{ xs: 'flex-start', md: 'flex-start' }}
            >
              <Stack
                direction={{ xs: 'row', md: 'column' }}
                spacing={1}
                alignItems="center"
                sx={{ width: { xs: 'auto', md: 40 }, flexShrink: 0 }}
              >
                <Skeleton
                  variant="circular"
                  width={10}
                  height={10}
                  sx={{ display: { xs: 'none', md: 'block' }, mt: 2 }}
                />
                <Skeleton variant="text" width={34} height={26} />
              </Stack>

              <Paper elevation={0} sx={{ p: 2.5, borderRadius: 2, width: '100%', minHeight: 210 }}>
                <Skeleton variant="text" width="52%" height={36} sx={{ mb: 0.5 }} />
                <Skeleton variant="text" width="72%" height={28} sx={{ mb: 1 }} />
                <Skeleton variant="text" width="97%" height={26} />
                <Skeleton variant="text" width="95%" height={26} />
                <Skeleton variant="text" width="92%" height={26} sx={{ mb: 1.5 }} />
                <Stack direction="row" spacing={1} flexWrap="wrap">
                  <Skeleton variant="rounded" width={78} height={28} />
                </Stack>
              </Paper>
            </Stack>
          ))}
        </Stack>
      </Stack>
    </Container>
  )
}

export default SeriesDetailPageSkeleton
