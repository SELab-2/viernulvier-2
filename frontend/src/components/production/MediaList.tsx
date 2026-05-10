import CloseRoundedIcon from '@mui/icons-material/CloseRounded'
import PlayArrowRoundedIcon from '@mui/icons-material/PlayArrowRounded'
import { Box, IconButton, Modal, Typography } from '@mui/material'
import { useState, type KeyboardEvent } from 'react'

import { tokens } from '../../theme/tokens'
import { DarkMode } from '../../types/Theme'
import Carousel from '../carousel/Carousel'

import type { MediaItem } from '../../types/Media'

interface MediaListProps {
  mediaItems: MediaItem[]
  videoUrls?: string[]
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
 * Returns a thumbnail URL for supported video providers.
 * Currently supports:
 * - YouTube
 * - YouTube Shorts
 * - Vimeo (thumbnail not publicly available without API)
 * - SoundCloud (no direct thumbnail support)
 *
 * Returns null when no thumbnail can be generated.
 */
function getVideoThumbnail(raw: string): string | null {
  try {
    const url = new URL(raw)
    const host = url.hostname.toLowerCase()

    // YouTube
    if (host.includes('youtube.com') || host === 'youtu.be') {
      let videoId: string | null = null

      // Standard YouTube URL (https://www.youtube.com/watch?v=abc123)
      if (host.includes('youtube.com')) {
        videoId = url.searchParams.get('v')

        // YouTube Shorts (https://youtube.com/shorts/abc123)
        if (!videoId && url.pathname.startsWith('/shorts/')) {
          videoId = url.pathname.split('/')[2] || null
        }

        // YouTube Embed (https://youtube.com/embed/abc123)
        if (!videoId && url.pathname.startsWith('/embed/')) {
          videoId = url.pathname.split('/')[2] || null
        }
      }

      // Short URL (https://youtu.be/abc123)
      if (host === 'youtu.be') {
        videoId = url.pathname.replace('/', '')
      }

      if (videoId) {
        return `https://img.youtube.com/vi/${videoId}/hqdefault.jpg`
      }
    }

    // Vimeo thumbnails require API/oEmbed support
    if (host.includes('vimeo.com')) {
      return null
    }

    // SoundCloud has no simple public thumbnail endpoint
    if (host.includes('soundcloud.com')) {
      return null
    }
  } catch {
    // Ignore invalid URLs
  }

  return null
}

/**
 * Converts supported video URLs into embeddable player URLs.
 *
 * Supports:
 * - YouTube
 * - YouTube Shorts
 * - Vimeo
 * - SoundCloud
 * - Loom
 *
 * Returns the original URL if it cannot be converted.
 */
function toEmbedUrl(raw: string): string {
  try {
    const url = new URL(raw)
    const host = url.hostname.toLowerCase()

    // YouTube
    if (host.includes('youtube.com') || host === 'youtu.be') {
      let videoId: string | null = null

      // Standard watch URL
      if (host.includes('youtube.com')) {
        videoId = url.searchParams.get('v')

        // Shorts
        if (!videoId && url.pathname.startsWith('/shorts/')) {
          videoId = url.pathname.split('/')[2] || null
        }

        // Existing embed URL
        if (!videoId && url.pathname.startsWith('/embed/')) {
          videoId = url.pathname.split('/')[2] || null
        }
      }

      // Shortened URL
      if (host === 'youtu.be') {
        videoId = url.pathname.replace('/', '')
      }

      if (videoId) {
        return `https://www.youtube.com/embed/${videoId}?autoplay=1&rel=0`
      }
    }

    // Vimeo
    if (host.includes('vimeo.com')) {
      const parts = url.pathname.split('/').filter(Boolean)
      const videoId = parts[parts.length - 1]

      if (videoId) {
        return `https://player.vimeo.com/video/${videoId}?autoplay=1`
      }
    }

    // SoundCloud
    if (host.includes('soundcloud.com')) {
      return `https://w.soundcloud.com/player/?url=${encodeURIComponent(raw)}&auto_play=true`
    }

    // Loom
    if (host.includes('loom.com')) {
      const parts = url.pathname.split('/').filter(Boolean)
      const videoId = parts[parts.length - 1]

      if (videoId) {
        return `https://www.loom.com/embed/${videoId}`
      }
    }
  } catch {
    // Ignore invalid URLs
  }

  return raw
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
export default function MediaList({ mediaItems, videoUrls = [] }: MediaListProps) {
  const [activeImage, setActiveImage] = useState<{ src: string; alt: string } | null>(null)
  const [activeVideoUrl, setActiveVideoUrl] = useState<string | null>(null)

  const mediaWithImage = mediaItems
    .map((item) => ({ item, imageUrl: getBestImageUrl(item) }))
    .filter((entry) => entry.imageUrl)

  if (!mediaWithImage.length && !videoUrls.length) {
    return null
  }

  const openPreview = (src: string, alt: string) => setActiveImage({ src, alt })
  const closePreview = () => {
    setActiveImage(null)
    setActiveVideoUrl(null)
  }

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
          {videoUrls.map((url, idx) => (
            <Box
              key={`video-${idx}`}
              sx={{
                width: { xs: 'calc(100vw - 80px)', sm: 350 },
                maxWidth: 'calc(100vw - 80px)',
              }}
            >
              <Box
                role="button"
                tabIndex={0}
                onClick={() => setActiveVideoUrl(url)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault()
                    setActiveVideoUrl(url)
                  }
                }}
                sx={(theme) => ({
                  position: 'relative',
                  width: '100%',
                  aspectRatio: '16 / 9',
                  overflow: 'hidden',
                  borderRadius: tokens.borderRadius.md,
                  backgroundColor:
                    theme.palette.mode === DarkMode
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
                {getVideoThumbnail(url) ? (
                  <Box
                    component="img"
                    src={getVideoThumbnail(url) as string}
                    alt={`Video ${idx + 1}`}
                    sx={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
                  />
                ) : (
                  <Box
                    sx={(theme) => ({
                      width: '100%',
                      height: '100%',
                      backgroundColor:
                        theme.palette.mode === DarkMode
                          ? tokens.colors.media.darkBackground
                          : tokens.colors.media.lightBackground,
                    })}
                  />
                )}
                <Box
                  sx={{
                    position: 'absolute',
                    inset: 0,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    pointerEvents: 'none',
                  }}
                >
                  <Box
                    sx={(theme) => ({
                      width: 48,
                      height: 48,
                      borderRadius: '50%',
                      backgroundColor: theme.palette.background.paper,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      boxShadow: '0 2px 12px rgba(0,0,0,0.30)',
                      svg: { color: theme.palette.text.primary, fontSize: 28 },
                    })}
                  >
                    <PlayArrowRoundedIcon />
                  </Box>
                </Box>
              </Box>
            </Box>
          ))}

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
                    theme.palette.mode === DarkMode
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
        open={Boolean(activeImage) || Boolean(activeVideoUrl)}
        onClose={closePreview}
        slotProps={{
          backdrop: {
            sx: (theme) => ({
              backgroundColor:
                theme.palette.mode === DarkMode
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
              borderRadius: 1.5,
              overflow: 'hidden',
              boxShadow: (theme) => theme.shadows[4],
              ...(activeVideoUrl && { aspectRatio: '16 / 9' }),
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

            {activeImage && (
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
            )}

            {activeVideoUrl && (
              <Box
                component="iframe"
                src={toEmbedUrl(activeVideoUrl)}
                title="Video player"
                allow="autoplay; fullscreen; picture-in-picture"
                allowFullScreen
                sx={{
                  display: 'block',
                  width: '100%',
                  aspectRatio: '16 / 9',
                  border: 0,
                  backgroundColor: 'background.paper',
                }}
              />
            )}
          </Box>
        </Box>
      </Modal>
    </Box>
  )
}
