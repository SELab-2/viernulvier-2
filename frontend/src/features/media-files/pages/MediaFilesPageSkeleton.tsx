import { Box, Skeleton, Stack } from '@mui/material'

interface MediaFileCardSkeletonProps {
  variant?: 'grid' | 'list'
}

/**
 * Skeleton placeholder for a single media file card.
 *
 * Purpose:
 * - Used while media items are loading (images/videos/documents)
 * - Mimics final layout to avoid layout shift when real content arrives
 *
 */
const MediaFileCardSkeleton = ({ variant = 'grid' }: MediaFileCardSkeletonProps) => {
  if (variant === 'list') {
    return (
      <Stack
        direction={{ xs: 'column', sm: 'row' }}
        sx={{
          width: '100%',
          minWidth: 0,
          overflow: 'hidden',
          borderRadius: 2,
          border: (theme) => `1px solid ${theme.palette.divider}`,
          bgcolor: 'background.paper',
        }}
      >
        {/* Media preview skeleton (image/video thumbnail area) */}
        <Stack sx={{ p: 2, flexShrink: 0 }}>
          <Skeleton
            variant="rounded"
            sx={{
              width: { xs: '100%', sm: 220 },
              aspectRatio: '16 / 9',
              borderRadius: 1,
            }}
          />
        </Stack>

        {/* Content skeleton (title + metadata lines) */}
        <Stack
          sx={{
            flex: 1,
            justifyContent: 'space-between',
            gap: 1.5,
            p: 3,
            minWidth: 0,
          }}
        >
          {/* Title + description lines */}
          <Stack spacing={1}>
            <Skeleton width="55%" height={32} />
            <Skeleton width="100%" />
            <Skeleton width="92%" />
            <Skeleton width="68%" />
          </Stack>

          {/* Footer metadata row (e.g. date / tags / actions) */}
          <Stack
            direction={{ xs: 'column', sm: 'row' }}
            spacing={1}
            sx={{
              alignItems: { xs: 'flex-start', sm: 'center' },
              justifyContent: { sm: 'space-between' },
            }}
          >
            <Skeleton width={140} />
            <Skeleton width={90} />
          </Stack>
        </Stack>
      </Stack>
    )
  }

  return (
    <Stack
      sx={{
        width: { xs: '100%', sm: 350 },
        maxWidth: '100%',
        height: '100%',
        overflow: 'hidden',
        borderRadius: 3,
        border: (theme) => `1px solid ${theme.palette.divider}`,
        bgcolor: 'background.paper',
      }}
    >
      {/* Media thumbnail skeleton (grid variant) */}
      <Skeleton
        variant="rectangular"
        sx={{
          aspectRatio: '16 / 9',
          width: '100%',
        }}
      />

      {/* Content section skeleton */}
      <Stack
        sx={{
          flex: 1,
          justifyContent: 'space-between',
          gap: 1.5,
          p: 3,
          minWidth: 0,
        }}
      >
        {/* Title + text lines */}
        <Stack spacing={1}>
          <Skeleton width="72%" height={32} />
          <Skeleton width="100%" />
          <Skeleton width="94%" />
          <Skeleton width="64%" />
        </Stack>

        {/* Footer metadata row */}
        <Stack
          direction="row"
          sx={{
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            rowGap: 0.5,
            columnGap: 1,
          }}
        >
          <Skeleton width={125} />
          <Skeleton width={80} />
        </Stack>
      </Stack>
    </Stack>
  )
}

interface MediaFilesPageSkeletonProps {
  layout?: 'grid' | 'list'
  isMobile?: boolean
  cards?: number
}

/**
 * Skeleton layout for the full media files page.
 *
 * Purpose:
 * - Simulates grid or list layout depending on current view mode
 * - Ensures consistent loading experience across breakpoints
 *
 * Behaviour:
 * - Mobile always forces grid layout for simplicity
 * - Limits number of list skeletons to avoid overly tall loading screens
 */
const MediaFilesPageSkeleton = ({
  layout = 'grid',
  isMobile = false,
  cards = 12,
}: MediaFilesPageSkeletonProps) => {
  const activeLayout = isMobile ? 'grid' : layout

  return (
    <Box sx={{ width: '100%' }}>
      {activeLayout === 'list' ? (
        // List layout skeleton (vertical stack)
        <Stack spacing={2}>
          {Array.from({ length: Math.min(cards, 8) }).map((_, index) => (
            <MediaFileCardSkeleton key={index} variant="list" />
          ))}
        </Stack>
      ) : (
        // Grid layout skeleton (responsive CSS grid)
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: {
              xs: '1fr',
              sm: 'repeat(2, minmax(0, 1fr))',
              lg: 'repeat(3, minmax(0, 1fr))',
            },
            gap: 3,
            justifyItems: { xs: 'stretch', sm: 'center' },
          }}
        >
          {Array.from({ length: cards }).map((_, index) => (
            <MediaFileCardSkeleton key={index} variant="grid" />
          ))}
        </Box>
      )}
    </Box>
  )
}

export default MediaFilesPageSkeleton
