import { useMemo, useState } from 'react'
import { useMediaQuery, useTheme } from '@mui/material'
import type { MediaItem } from '../../types/Media'

interface MediaListProps {
  mediaItems: MediaItem[]
}

// TODO: code duplicatie met functie in ProductionDetailPage
// TODO: arrow niet zo nice
// TODO: animaties bij switch
// TODO: vergoot afbeelding bij klick
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
 * - Inline documentation + typed props
 */
export default function MediaList({ mediaItems }: MediaListProps) {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'))
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'))
  const itemsPerSlide = isMobile ? 1 : isTablet ? 2 : 3

  const [currentIndex, setCurrentIndex] = useState(0)
  const navButtonBackground =
    theme.palette.mode === 'dark' ? 'rgba(10, 14, 40, 0.65)' : 'rgba(255,255,255,0.8)'

  const slides = useMemo(
    () =>
      mediaItems
        .map((item) => ({ ...item, imageUrl: getBestImageUrl(item) }))
        .filter((item) => item.imageUrl),
    [mediaItems],
  )

  const total = slides.length

  const normalizedCurrentIndex = total > 0 ? ((currentIndex % total) + total) % total : 0

  const visibleSlides = useMemo(() => {
    if (total <= itemsPerSlide) {
      return slides
    }

    return Array.from({ length: itemsPerSlide }).map((_, i) => {
      return slides[(normalizedCurrentIndex + i) % total]
    })
  }, [slides, normalizedCurrentIndex, itemsPerSlide, total])

  if (!slides.length) {
    return null
  }

  function goPrevious() {
    setCurrentIndex((old) => (old - itemsPerSlide + total) % total)
  }

  function goNext() {
    setCurrentIndex((old) => (old + itemsPerSlide) % total)
  }

  return (
    <section
      className="media-list"
      aria-label="Production media carousel"
      style={{
        width: '100%',
        maxWidth: '1250px',
        margin: '24px auto 0',
        padding: '16px',
        borderRadius: '8px',
        background: theme.palette.background.paper,
        color: theme.palette.text.primary,
        border: `1px solid ${theme.palette.divider}`,
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
          position: 'relative',
          borderRadius: '8px',
          overflow: 'hidden',
          background: theme.palette.background.default,
          border: `1px solid ${theme.palette.divider}`,
        }}
      >
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: `repeat(${itemsPerSlide}, minmax(0, 1fr))`,
            gap: '8px',
            width: '100%',
            minHeight: '220px',
            padding: '8px',
            boxSizing: 'border-box',
            background: theme.palette.background.paper,
          }}
        >
          {visibleSlides.length ? (
            visibleSlides.map((item) => (
              <div
                key={item.id}
                style={{
                  width: '100%',
                  aspectRatio: '16/9',
                  overflow: 'hidden',
                  borderRadius: '6px',
                  background: theme.palette.mode === 'dark' ? '#101436' : '#f7f7f7',
                }}
              >
                <img
                  src={item.imageUrl as string}
                  alt={item.display_title || item.original_filename || 'Media item'}
                  style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
                />
              </div>
            ))
          ) : (
            <div
              style={{
                width: '100%',
                height: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: theme.palette.text.disabled,
              }}
            >
              No image
            </div>
          )}
        </div>

        <button
          type="button"
          onClick={goPrevious}
          aria-label="Previous media"
          style={{
            position: 'absolute',
            top: '50%',
            left: '12px',
            transform: 'translateY(-50%)',
            border: 'none',
            borderRadius: '50%',
            width: '36px',
            height: '36px',
            background: navButtonBackground,
            color: theme.palette.text.primary,
            cursor: 'pointer',
            boxShadow: '0 2px 8px rgba(0,0,0,0.24)',
            display: 'grid',
            placeItems: 'center',
          }}
        >
          ‹
        </button>

        <button
          type="button"
          onClick={goNext}
          aria-label="Next media"
          style={{
            position: 'absolute',
            top: '50%',
            right: '12px',
            transform: 'translateY(-50%)',
            border: 'none',
            borderRadius: '50%',
            width: '36px',
            height: '36px',
            background: navButtonBackground,
            color: theme.palette.text.primary,
            cursor: 'pointer',
            boxShadow: '0 2px 8px rgba(0,0,0,0.24)',
            display: 'grid',
            placeItems: 'center',
          }}
        >
          ›
        </button>
      </div>

      <div
        style={{
          marginTop: '12px',
          textAlign: 'center',
          color: theme.palette.text.secondary,
          fontSize: '0.9rem',
        }}
      >
        {`${normalizedCurrentIndex + 1} / ${total}`}
      </div>
    </section>
  )
}
