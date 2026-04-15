import CloseRoundedIcon from '@mui/icons-material/CloseRounded'
import { Box, IconButton, Modal, Typography } from '@mui/material'
import { useState, type KeyboardEvent } from 'react'

import { tokens } from '../../theme/tokens'
import Carousel from '../carousel/Carousel'

import type { MediaItem } from '../../types/Media'

interface MediaListProps {
  mediaItems: MediaItem[]
}

/**
 * Pick the most suitable image URL from crop metadata.
 *
 * Preference order:
 * - crop named "FE3_header"
 * - crop named "hd_ready"
 * - first crop with image_url
 * - null when no crop URL exists
 */
function getBestImageUrl(item: MediaItem): string | null {
  const cropPriority = ['FE3_header', 'hd_ready']
  const findInPriority = cropPriority
    .map((name) => item.crops.find((crop) => crop.name === name && !!crop.image_url))
    .find(Boolean)

  if (findInPriority?.image_url) {
    return findInPriority?.image_url
  }

  const fallback = item.crops.find((crop) => !!crop.image_url)
  return fallback?.image_url ?? null
}

/**
 * Media carousel component for production detail view.
 *
 * Features:
 * - Dark mode aware styling via MUI theme
 * - Responsive one-item viewport on mobile + basic thumbnail strip
 * - Arrow buttons (pijl symbolen) for non-touch navigation
 * - Powered by Embla Carousel for smooth, touch-enabled sliding
 */
export default function MediaList({ mediaItems }: MediaListProps) {
  const [activeImage, setActiveImage] = useState<{ src: string; alt: string } | null>(null)

  const mediaWithImage = mediaItems
    .map((item) => ({ item, imageUrl: getBestImageUrl(item) }))
    .filter((entry) => entry.imageUrl)

  if (!mediaWithImage.length) {
    return null
  }

  const openPreview = (src: string, alt: string) => setActiveImage({ src, alt })
  const closePreview = () => setActiveImage(null)

  const handleKeyOpen = (event: KeyboardEvent<HTMLDivElement>, src: string, alt: string) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      openPreview(src, alt)
    }
  }

  return (
    <Box
      className="media-list"
      aria-label="Production media carousel"
      component="section"
      sx={(theme) => ({
        width: '100%',
        maxWidth: 1250,
        mx: 'auto',
        mt: 3,
        px: 2,
        borderRadius: tokens.borderRadius.md,
        background: 'transparent',
        color: theme.palette.text.primary,
      })}
    >
      <Typography
        component="h2"
        sx={{
          mb: 1.5,
          fontSize: tokens.typography.sizes.lg,
          fontWeight: tokens.typography.weights.bold,
          color: 'text.primary',
        }}
      >
        Media
      </Typography>

      <Box sx={{ borderRadius: tokens.borderRadius.md, background: 'transparent', p: 0 }}>
        <Carousel
          ariaLabel="Production media carousel"
          maxWidth="100%"
          loop
          showDots
          showArrows
          previousLabel="Previous media"
          nextLabel="Next media"
          sx={{ width: '100%' }}
        >
          {mediaWithImage.map(({ item, imageUrl }) => (
            <Box
              key={item.id}
              sx={{
                width: { xs: 'calc(100vw - 80px)', sm: 350 },
                maxWidth: 'calc(100vw - 80px)',
              }}
            >
              <Box
                role="button"
                tabIndex={0}
                onClick={() =>
                  openPreview(
                    imageUrl as string,
                    item.display_title || item.original_filename || 'Media item',
                  )
                }
                onKeyDown={(event) =>
                  handleKeyOpen(
                    event,
                    imageUrl as string,
                    item.display_title || item.original_filename || 'Media item',
                  )
                }
                sx={(theme) => ({
                  width: '100%',
                  aspectRatio: '16 / 9',
                  overflow: 'hidden',
                  borderRadius: tokens.borderRadius.md,
                  backgroundColor:
                    theme.palette.mode === 'dark'
                      ? tokens.colors.media.darkBackground
                      : tokens.colors.media.lightBackground,
                  border: `1px solid ${theme.palette.divider}`,
                  cursor: 'pointer',
                  transition: 'transform 180ms ease, box-shadow 180ms ease',
                  '&:hover, &:focus-visible': {
                    transform: 'translateY(-2px)',
                    boxShadow: tokens.shadows.mediaControl,
                  },
                  '&:focus-visible': {
                    outline: `2px solid ${theme.palette.primary.main}`,
                    outlineOffset: 2,
                  },
                })}
              >
                <Box
                  component="img"
                  src={imageUrl as string}
                  alt={item.display_title || item.original_filename || 'Media item'}
                  sx={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
                />
              </Box>
            </Box>
          ))}
        </Carousel>
      </Box>

      <Modal
        open={Boolean(activeImage)}
        onClose={closePreview}
        slotProps={{
          backdrop: {
            sx: (theme) => ({
              backgroundColor:
                theme.palette.mode === 'dark'
                  ? tokens.colors.overlay.modalBackdropDark
                  : tokens.colors.overlay.modalBackdropLight,
            }),
          },
        }}
      >
        <Box
          onClick={closePreview}
          sx={{
            position: 'fixed',
            inset: 0,
            display: 'grid',
            placeItems: 'center',
            p: { xs: 2, md: 4 },
          }}
        >
          <Box
            onClick={(event) => event.stopPropagation()}
            sx={{
              position: 'relative',
              width: 'min(1200px, 96vw)',
              maxHeight: '90vh',
              borderRadius: 1.5,
              overflow: 'hidden',
              boxShadow: (theme) => theme.shadows[4],
            }}
          >
            <IconButton
              aria-label="Close preview"
              onClick={closePreview}
              sx={{
                position: 'absolute',
                top: 10,
                right: 10,
                zIndex: 2,
                color: 'text.primary',
                backgroundColor: 'action.hover',
                '&:hover': {
                  backgroundColor: 'action.selected',
                },
              }}
            >
              <CloseRoundedIcon />
            </IconButton>

            {activeImage ? (
              <Box
                component="img"
                src={activeImage.src}
                alt={activeImage.alt}
                sx={{
                  width: '100%',
                  maxHeight: '90vh',
                  objectFit: 'contain',
                  backgroundColor: 'background.paper',
                  display: 'block',
                }}
              />
            ) : null}
          </Box>
        </Box>
      </Modal>
    </Box>
  )
}
