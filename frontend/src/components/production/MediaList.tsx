import { useMediaQuery, useTheme } from '@mui/material'
import useEmblaCarousel from 'embla-carousel-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { tokens } from '../../theme/tokens'
import type { MediaItem } from '../../types/Media'

interface MediaListProps {
  mediaItems: MediaItem[]
}

// TODO: code duplicatie met functie in ProductionDetailPage
// TODO: arrow niet zo nice
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
 * - Powered by Embla Carousel for smooth, touch-enabled sliding
 */
export default function MediaList({ mediaItems }: MediaListProps) {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'))
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'))
  const slidesToScroll = isMobile ? 1 : isTablet ? 2 : 3

  const navButtonBackground =
    theme.palette.mode === 'dark'
      ? tokens.colors.overlay.mediaNavDark
      : tokens.colors.overlay.mediaNavLight

  const slides = useMemo(
    () =>
      mediaItems
        .map((item) => ({ ...item, imageUrl: getBestImageUrl(item) }))
        .filter((item) => item.imageUrl),
    [mediaItems],
  )

  const total = slides.length

  const [emblaRef, emblaApi] = useEmblaCarousel({
    loop: true,
    slidesToScroll,
    align: 'start',
  })

  const [currentIndex, setCurrentIndex] = useState(0)

  useEffect(() => {
    if (!emblaApi) return
    const onSelect = () => setCurrentIndex(emblaApi.selectedScrollSnap())
    emblaApi.on('select', onSelect)
    onSelect()
    return () => {
      emblaApi.off('select', onSelect)
    }
  }, [emblaApi])

  useEffect(() => {
    if (!emblaApi) return
    emblaApi.reInit({ loop: true, slidesToScroll, align: 'start' })
  }, [emblaApi, slidesToScroll])

  const goPrevious = useCallback(() => emblaApi?.scrollPrev(), [emblaApi])
  const goNext = useCallback(() => emblaApi?.scrollNext(), [emblaApi])

  if (!slides.length) {
    return null
  }

  const displayIndex = currentIndex * slidesToScroll + 1

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
          background: theme.palette.background.paper,
          border: `1px solid ${theme.palette.divider}`,
          padding: '8px',
        }}
      >
        <div ref={emblaRef} style={{ overflow: 'hidden' }}>
          <div
            style={{
              display: 'flex',
              marginLeft: '-8px',
            }}
          >
            {slides.map((item) => (
              <div
                key={item.id}
                style={{
                  flex: `0 0 calc(${100 / slidesToScroll}%)`,
                  minWidth: 0,
                  paddingLeft: '8px',
                  boxSizing: 'border-box',
                }}
              >
                <div
                  style={{
                    width: '100%',
                    aspectRatio: '16/9',
                    overflow: 'hidden',
                    borderRadius: '6px',
                    background:
                      theme.palette.mode === 'dark'
                        ? tokens.colors.media.darkBackground
                        : tokens.colors.media.lightBackground,
                  }}
                >
                  <img
                    src={item.imageUrl as string}
                    alt={item.display_title || item.original_filename || 'Media item'}
                    style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
                  />
                </div>
              </div>
            ))}
          </div>
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
            boxShadow: tokens.shadows.mediaControl,
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
            boxShadow: tokens.shadows.mediaControl,
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
        {`${displayIndex} / ${total}`}
      </div>
    </section>
  )
}
