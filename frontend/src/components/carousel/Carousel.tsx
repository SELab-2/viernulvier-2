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
    { align: 'start', loop, duration: 28, slidesToScroll: 'auto' },
    [WheelGesturesPlugin()],
  )
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [canScrollPrev, setCanScrollPrev] = useState(false)
  const [canScrollNext, setCanScrollNext] = useState(false)

  const snapCount = emblaApi?.scrollSnapList().length ?? Math.max(1, slides.length)

  const dotRefs = useRef<Array<HTMLButtonElement | null>>([])
  const hasInteracted = useRef(false)

  const updateControls = useCallback(() => {
    if (!emblaApi) {
      return
    }

    const newIndex = emblaApi.selectedScrollSnap()
    if (newIndex !== selectedIndex) {
      hasInteracted.current = true
    }

    setSelectedIndex(newIndex)
    setCanScrollPrev(emblaApi.canScrollPrev())
    setCanScrollNext(emblaApi.canScrollNext())
  }, [emblaApi, selectedIndex])

  useEffect(() => {
    if (!emblaApi) {
      return
    }

    emblaApi.on('select', updateControls)
    emblaApi.on('reInit', updateControls)
    const frameId = requestAnimationFrame(updateControls)

    return () => {
      cancelAnimationFrame(frameId)
      emblaApi.off('select', updateControls)
      emblaApi.off('reInit', updateControls)
    }
  }, [emblaApi, updateControls])

  useLayoutEffect(() => {
    if (!hasInteracted.current) {
      return
    }
    const el = dotRefs.current[selectedIndex]
    if (!el || typeof el.scrollIntoView !== 'function') {
      return
    }
    el.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' })
  }, [selectedIndex])

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
      sx={[
        {
          position: 'relative',
          maxWidth,
          gap: 2,
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
        <Box sx={{ display: 'flex', gap: 0, mx: -1, alignItems: 'stretch' }}>
          {slides.map((slide, index) => (
            <Box
              key={index}
              sx={{
                flex: '0 0 auto',
                px: 1,
                boxSizing: 'border-box',
                display: 'flex',
                alignItems: 'stretch',
              }}
            >
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
              boxShadow: theme.shadows[1],
              opacity: 0,
              pointerEvents: 'none',
              transition:
                'opacity 220ms ease, transform 220ms cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 220ms ease',
              '&:hover': {
                backgroundColor: theme.palette.background.paper,
                boxShadow: theme.shadows[3],
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
              boxShadow: theme.shadows[1],
              opacity: 0,
              pointerEvents: 'none',
              transition:
                'opacity 220ms ease, transform 220ms cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 220ms ease',
              '&:hover': {
                backgroundColor: theme.palette.background.paper,
                boxShadow: theme.shadows[3],
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
          sx={{ alignItems: 'center', justifyContent: 'center', gap: 2, mt: 1.5, px: 0.5 }}
        >
          {showDots ? (
            <Box
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
                sx={{
                  flexWrap: 'nowrap',
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
                          'transform 200ms cubic-bezier(0.34, 1.56, 0.64, 1), opacity 200ms ease, background-color 200ms ease',
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
