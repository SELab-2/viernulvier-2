import ChevronLeftRoundedIcon from '@mui/icons-material/ChevronLeftRounded'
import ChevronRightRoundedIcon from '@mui/icons-material/ChevronRightRounded'
import { Box, IconButton, Stack, type SxProps, type Theme } from '@mui/material'
import useEmblaCarousel from 'embla-carousel-react'
import { WheelGesturesPlugin } from 'embla-carousel-wheel-gestures'
import { Children, useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'

export interface CarouselProps {
  children: ReactNode
  ariaLabel?: string
  maxWidth?: number | string
  loop?: boolean
  showArrows?: boolean
  showDots?: boolean
  previousLabel?: string
  nextLabel?: string
  slideLabel?: string
  sx?: SxProps<Theme>
}

/**
 * Generic Embla-based carousel with responsive page grouping, optional dots, and hover-revealed arrows.
 *
 * The component only manages layout and navigation state, callers are responsible for rendering the
 * actual slide content.
 */
function Carousel({
  children,
  ariaLabel = 'Carousel',
  maxWidth,
  loop = true,
  showArrows = true,
  showDots = true,
  previousLabel = 'Previous slide',
  nextLabel = 'Next slide',
  slideLabel = 'Go to slide',
  sx,
}: CarouselProps) {
  const DOT_SIZE = 11
  const DOT_GAP = 8

  const slides = useMemo(() => Children.toArray(children), [children])

  const [emblaRef, emblaApi] = useEmblaCarousel(
    { align: 'start', loop, skipSnaps: true, slidesToScroll: 'auto' },
    [WheelGesturesPlugin()],
  )
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [canScrollPrev, setCanScrollPrev] = useState(false)
  const [canScrollNext, setCanScrollNext] = useState(false)
  const activeDotRef = useRef<HTMLButtonElement | null>(null)

  // Embla reports snaps per page, which keeps the dots aligned with the visible slide groups.
  const snapCount = emblaApi?.scrollSnapList().length ?? Math.max(1, slides.length)

  /**
   * Syncs the arrow state and the active dot with the current Embla snap.
   */
  const updateControls = useCallback(() => {
    if (!emblaApi) return

    setSelectedIndex(emblaApi.selectedScrollSnap())
    setCanScrollPrev(emblaApi.canScrollPrev())
    setCanScrollNext(emblaApi.canScrollNext())
  }, [emblaApi])

  useEffect(() => {
    if (!emblaApi) return

    emblaApi.reInit({ align: 'start', loop, skipSnaps: true, slidesToScroll: 'auto' })
    emblaApi.on('select', updateControls)
    emblaApi.on('reInit', updateControls)
    updateControls()

    return () => {
      emblaApi.off('select', updateControls)
      emblaApi.off('reInit', updateControls)
    }
  }, [emblaApi, loop, updateControls])

  const scrollPrev = useCallback(() => emblaApi?.scrollPrev(), [emblaApi])
  const scrollNext = useCallback(() => emblaApi?.scrollNext(), [emblaApi])
  const scrollTo = useCallback((index: number) => emblaApi?.scrollTo(index), [emblaApi])

  useEffect(() => {
    activeDotRef.current?.scrollIntoView({
      behavior: 'smooth',
      block: 'nearest',
      inline: 'center',
    })
  }, [selectedIndex])

  if (slides.length === 0) {
    return null
  }

  const hasMultipleSlides = snapCount > 1

  return (
    <Box
      component="section"
      role="region"
      aria-roledescription="carousel"
      aria-label={ariaLabel}
      sx={(theme) => ({
        position: 'relative',
        width: '100%',
        maxWidth,
        mx: maxWidth ? 'auto' : 0,
        // Provide equal side inset so edge-card hover borders/shadows remain visible on both sides.
        px: {
          xs: theme.spacing(0.625),
          sm: theme.spacing(0.75),
        },
        ...((typeof sx === 'function' ? sx(theme) : sx) as object),
      })}
    >
      <Box
        sx={{
          position: 'relative',
          overflow: 'visible',
          '&:hover .carousel-nav, &:focus-within .carousel-nav': {
            opacity: 1,
            pointerEvents: 'auto',
          },
        }}
      >
        <Box
          ref={emblaRef}
          sx={{
            overflow: 'hidden',
            // Avoid tiny edge clipping on fractional viewport widths.
            px: '2px',
          }}
        >
          <Box
            sx={(theme) => ({
              display: 'flex',
              alignItems: 'stretch',
              touchAction: 'pan-y pinch-zoom',
              py: 1,
              // Keep equal horizontal breathing room on both sides so edge-card hover styles are not clipped.
              marginX: {
                xs: theme.spacing(-0.625),
                sm: theme.spacing(-0.75),
                md: theme.spacing(-0.75),
              },
            })}
          >
            {slides.map((slide, index) => (
              <Box
                key={index}
                sx={(theme) => ({
                  // Let each slide keep its natural width (e.g. the card's fixed width)
                  // so it can't overflow or overlap neighbours. Embla will group slides
                  // automatically via `slidesToScroll: 'auto'`.
                  flex: '0 0 auto',
                  minWidth: 0,
                  paddingX: theme.spacing(0.625),
                  [theme.breakpoints.up('sm')]: {
                    paddingX: theme.spacing(0.75),
                  },
                })}
              >
                {slide}
              </Box>
            ))}
          </Box>
        </Box>

        {showArrows ? (
          <>
            <IconButton
              type="button"
              aria-label={previousLabel}
              onClick={scrollPrev}
              onPointerUp={() => (document.activeElement as HTMLElement | null)?.blur()}
              disabled={!canScrollPrev && !loop}
              className="carousel-nav"
              sx={(theme) => ({
                position: 'absolute',
                top: '50%',
                left: 0,
                transform: 'translate(-50%, -50%)',
                zIndex: 2,
                border: `1px solid ${theme.palette.divider}`,
                backgroundColor: theme.palette.background.paper,
                boxShadow: '0 0 18px rgba(0, 0, 0, 0.06)',
                opacity: 0,
                pointerEvents: 'none',
                transition: 'opacity 160ms ease, transform 160ms ease, box-shadow 160ms ease',
                '&:hover': {
                  backgroundColor: theme.palette.background.paper,
                  boxShadow: '0 0 24px rgba(0, 0, 0, 0.10)',
                  transform: 'translate(-56%, -50%)',
                },
                '@media (hover: none)': {
                  opacity: 1,
                  pointerEvents: 'auto',
                },
                '&:focus-visible': {
                  opacity: 1,
                  pointerEvents: 'auto',
                },
              })}
            >
              <ChevronLeftRoundedIcon />
            </IconButton>

            <IconButton
              type="button"
              aria-label={nextLabel}
              onClick={scrollNext}
              onPointerUp={() => (document.activeElement as HTMLElement | null)?.blur()}
              disabled={!canScrollNext && !loop}
              className="carousel-nav"
              sx={(theme) => ({
                position: 'absolute',
                top: '50%',
                right: 0,
                transform: 'translate(50%, -50%)',
                zIndex: 2,
                border: `1px solid ${theme.palette.divider}`,
                backgroundColor: theme.palette.background.paper,
                boxShadow: '0 0 18px rgba(0, 0, 0, 0.06)',
                opacity: 0,
                pointerEvents: 'none',
                transition: 'opacity 160ms ease, transform 160ms ease, box-shadow 160ms ease',
                '&:hover': {
                  backgroundColor: theme.palette.background.paper,
                  boxShadow: '0 0 24px rgba(0, 0, 0, 0.10)',
                  transform: 'translate(56%, -50%)',
                },
                '@media (hover: none)': {
                  opacity: 1,
                  pointerEvents: 'auto',
                },
                '&:focus-visible': {
                  opacity: 1,
                  pointerEvents: 'auto',
                },
              })}
            >
              <ChevronRightRoundedIcon />
            </IconButton>
          </>
        ) : null}
      </Box>

      {hasMultipleSlides && (showArrows || showDots) ? (
        <Stack
          direction="row"
          alignItems="center"
          justifyContent="center"
          gap={2}
          sx={{ mt: 1.5, px: 0.5 }}
        >
          {showDots ? (
            <Box
              sx={{
                minWidth: 0,
                width: '100%',
                overflowX: 'auto',
                overflowY: 'hidden',
                WebkitOverflowScrolling: 'touch',
                scrollbarWidth: 'none',
                '&::-webkit-scrollbar': {
                  display: 'none',
                },
              }}
            >
              <Box
                sx={{
                  display: 'flex',
                  gap: `${DOT_GAP}px`,
                  justifyContent: 'center',
                  width: 'max-content',
                  minWidth: '100%',
                  mx: 'auto',
                  py: 0.25,
                }}
              >
                {Array.from({ length: snapCount }).map((_, index) => {
                  const active = index === selectedIndex

                  return (
                    <Box
                      key={index}
                      component="button"
                      ref={active ? activeDotRef : undefined}
                      type="button"
                      aria-label={`${slideLabel} ${index + 1}`}
                      aria-current={active ? 'true' : undefined}
                      onClick={() => scrollTo(index)}
                      sx={(theme) => ({
                        width: DOT_SIZE,
                        height: DOT_SIZE,
                        p: 0,
                        border: 'none',
                        borderRadius: 999,
                        backgroundColor: active
                          ? theme.palette.text.primary
                          : theme.palette.divider,
                        cursor: 'pointer',
                        opacity: active ? 1 : 0.55,
                        transition:
                          'transform 160ms ease, opacity 160ms ease, background-color 160ms ease',
                        '&:hover': {
                          transform: 'scale(1.12)',
                          opacity: 1,
                        },
                      })}
                    />
                  )
                })}
              </Box>
            </Box>
          ) : null}
        </Stack>
      ) : null}
    </Box>
  )
}

export default Carousel
