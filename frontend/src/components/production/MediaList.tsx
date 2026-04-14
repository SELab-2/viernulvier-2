import CloseRoundedIcon from '@mui/icons-material/CloseRounded'
import { Box, IconButton, Modal, useTheme } from '@mui/material'
import { useState, type KeyboardEvent } from 'react'

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
  const theme = useTheme()
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
    <section
      className="media-list"
      aria-label="Production media carousel"
      style={{
        width: '100%',
        maxWidth: '1250px',
        margin: '24px auto 0',
        padding: '0 16px',
        borderRadius: '8px',
        background: 'transparent',
        color: theme.palette.text.primary,
      }}
    >
      <h2
        style={{
          margin: '0 0 12px',
          fontSize: '1.1rem',
          fontWeight: 600,
          color: theme.palette.text.primary,
        }}
      >
        Media
      </h2>

      <div
        style={{
          borderRadius: '10px',
          background: 'transparent',
          padding: 0,
        }}
      >
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
            <div
              key={item.id}
              style={{
                width: '350px',
                maxWidth: 'calc(100vw - 80px)',
              }}
            >
              <div
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
                style={{
                  width: '100%',
                  aspectRatio: '16/9',
                  overflow: 'hidden',
                  borderRadius: '8px',
                  background: theme.palette.mode === 'dark' ? '#101436' : '#f7f7f7',
                  border: `1px solid ${theme.palette.divider}`,
                  cursor: 'pointer',
                  transition: 'transform 180ms ease, box-shadow 180ms ease',
                }}
                onMouseEnter={(event) => {
                  event.currentTarget.style.transform = 'translateY(-2px)'
                  event.currentTarget.style.boxShadow = '0 8px 24px rgba(0,0,0,0.18)'
                }}
                onMouseLeave={(event) => {
                  event.currentTarget.style.transform = 'translateY(0)'
                  event.currentTarget.style.boxShadow = 'none'
                }}
              >
                <img
                  src={imageUrl as string}
                  alt={item.display_title || item.original_filename || 'Media item'}
                  style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
                />
              </div>
            </div>
          ))}
        </Carousel>
      </div>

      <Modal
        open={Boolean(activeImage)}
        onClose={closePreview}
        slotProps={{
          backdrop: {
            sx: {
              backgroundColor: 'rgba(35, 35, 35, 0.72)',
            },
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
              boxShadow: '0 20px 60px rgba(0,0,0,0.45)',
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
                color: '#fff',
                backgroundColor: 'rgba(0, 0, 0, 0.45)',
                '&:hover': {
                  backgroundColor: 'rgba(0, 0, 0, 0.62)',
                },
              }}
            >
              <CloseRoundedIcon />
            </IconButton>

            {activeImage ? (
              <img
                src={activeImage.src}
                alt={activeImage.alt}
                style={{
                  width: '100%',
                  maxHeight: '90vh',
                  objectFit: 'contain',
                  background: '#111',
                  display: 'block',
                }}
              />
            ) : null}
          </Box>
        </Box>
      </Modal>
    </section>
  )
}
