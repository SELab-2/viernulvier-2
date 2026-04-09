import ChevronLeftRoundedIcon from '@mui/icons-material/ChevronLeftRounded'
import ChevronRightRoundedIcon from '@mui/icons-material/ChevronRightRounded'
import { Box, IconButton, Stack, type SxProps, type Theme } from '@mui/material'
import useEmblaCarousel from 'embla-carousel-react'
import { WheelGesturesPlugin } from 'embla-carousel-wheel-gestures'
import {
  Children,
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'

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
 * Generic Embla-based carousel with optional dots, and hover-revealed arrows.
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
  const slides = useMemo(() => Children.toArray(children), [children])

  const [emblaRef, emblaApi] = useEmblaCarousel(
    { align: 'start', loop, skipSnaps: true, slidesToScroll: 'auto' },
    [WheelGesturesPlugin()],
  )
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [canScrollPrev, setCanScrollPrev] = useState(false)
  const [canScrollNext, setCanScrollNext] = useState(false)

  const snapCount = emblaApi?.scrollSnapList().length ?? Math.max(1, slides.length)

  const dotRefs = useRef<(HTMLButtonElement | null)[]>([])
  const dotsScrollRef = useRef<HTMLDivElement | null>(null)

  const updateControls = useCallback(() => {
    if (!emblaApi) return

    setSelectedIndex(emblaApi.selectedScrollSnap())
    setCanScrollPrev(emblaApi.canScrollPrev())
    setCanScrollNext(emblaApi.canScrollNext())
  }, [emblaApi])

  useEffect(() => {
    if (!emblaApi) return

    emblaApi.on('select', updateControls)
    emblaApi.on('reInit', updateControls)
    updateControls()

    return () => {
      emblaApi.off('select', updateControls)
      emblaApi.off('reInit', updateControls)
    }
  }, [emblaApi, updateControls])

  useLayoutEffect(() => {
    const el = dotRefs.current[selectedIndex]
    const container = dotsScrollRef.current
    if (!el || !container) return

    // Calculate the scroll position so that the dot is centered in the container
    // Doing it this way won't force a scroll towards the caroussel on a refresh
    const elLeft = el.offsetLeft
    const elWidth = el.offsetWidth
    const containerWidth = container.offsetWidth
    const targetScroll = elLeft - containerWidth / 2 + elWidth / 2

    let startTime: number | null = null

    function animateScroll(currentTime: number) {
      if (!startTime) {
        startTime = currentTime
      }

      const progress = Math.min((currentTime - startTime) / 650, 1)
      const ease = progress < 0.5 ? 2 * progress * progress : -1 + (4 - 2 * progress) * progress
      container!.scrollLeft = container!.scrollLeft + (targetScroll - container!.scrollLeft) * ease

      if (progress < 1) {
        requestAnimationFrame(animateScroll)
      }
    }
    requestAnimationFrame(animateScroll)
  }, [selectedIndex, snapCount])

  const scrollPrev = useCallback(() => emblaApi?.scrollPrev(), [emblaApi])
  const scrollNext = useCallback(() => emblaApi?.scrollNext(), [emblaApi])
  const scrollTo = useCallback((index: number) => emblaApi?.scrollTo(index), [emblaApi])

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
      position="relative"
      maxWidth={maxWidth}
      gap={2}
      sx={[
        {
          '@media (hover: hover)': {
            '&:hover .carousel-nav': {
              opacity: 1,
              pointerEvents: 'auto',
            },
          },
        },
        ...(Array.isArray(sx) ? sx : sx != null ? [sx] : []),
      ]}
    >
      <Box
        ref={emblaRef}
        sx={{
          overflow: 'hidden',
          pb: '4px',
          mb: '-4px',
        }}
      >
        <Box display="flex" gap={0} mx={-1} alignItems="stretch">
          {slides.map((slide, index) => (
            <Box key={index} px={1} boxSizing="border-box" display="flex" alignItems="stretch">
              {slide}
            </Box>
          ))}
        </Box>
      </Box>

      {showArrows && hasMultipleSlides ? (
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
              ref={dotsScrollRef}
              sx={{
                flex: 1,
                minWidth: 0,
                overflowX: 'auto',
                overflowY: 'hidden',
                scrollbarWidth: 'none',
                msOverflowStyle: 'none',
                '&::-webkit-scrollbar': { display: 'none' },
              }}
            >
              <Stack
                component="div"
                direction="row"
                spacing={1}
                flexWrap="nowrap"
                sx={{
                  width: 'max-content',
                  minWidth: '100%',
                  justifyContent: 'center',
                  boxSizing: 'border-box',
                  pl: 'calc(50% - 5.5px)',
                  pr: 'calc(50% - 5.5px)',
                  py: 0.25,
                }}
              >
                {Array.from({ length: snapCount }).map((_, index) => {
                  const active = index === selectedIndex

                  return (
                    <Box
                      key={index}
                      ref={(node) => {
                        dotRefs.current[index] = node as HTMLButtonElement | null
                      }}
                      component="button"
                      type="button"
                      aria-label={`${slideLabel} ${index + 1}`}
                      aria-current={active ? 'true' : undefined}
                      onClick={() => scrollTo(index)}
                      sx={(theme) => ({
                        width: 11,
                        height: 11,
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
              </Stack>
            </Box>
          ) : null}
        </Stack>
      ) : null}
    </Box>
  )
}

export default Carousel
