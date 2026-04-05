import ChevronLeftRoundedIcon from '@mui/icons-material/ChevronLeftRounded'
import ChevronRightRoundedIcon from '@mui/icons-material/ChevronRightRounded'
import { Box, IconButton, Stack, type SxProps, type Theme } from '@mui/material'
import { useMediaQuery, useTheme } from '@mui/material'
import useEmblaCarousel from 'embla-carousel-react'
import { WheelGesturesPlugin } from 'embla-carousel-wheel-gestures'
import { Children, useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'

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
  const slides = useMemo(() => Children.toArray(children), [children])
  const theme = useTheme()

  // Group more items per view on larger screens so the dots represent pages instead of individual slides.
  const isXlUp = useMediaQuery(theme.breakpoints.up('xl'))
  const isLgUp = useMediaQuery(theme.breakpoints.up('lg'))
  const isMdUp = useMediaQuery(theme.breakpoints.up('md'))
  const isSmUp = useMediaQuery(theme.breakpoints.up('sm'))
  const slidesToScroll = isXlUp ? 4 : isLgUp ? 3 : isMdUp ? 3 : isSmUp ? 2 : 1
  const [emblaRef, emblaApi] = useEmblaCarousel(
    { align: 'start', loop, skipSnaps: true, slidesToScroll },
    [WheelGesturesPlugin()],
  )
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [canScrollPrev, setCanScrollPrev] = useState(false)
  const [canScrollNext, setCanScrollNext] = useState(false)

  // Embla reports snaps per page, which keeps the dots aligned with the visible slide groups.
  const snapCount =
    emblaApi?.scrollSnapList().length ?? Math.max(1, Math.ceil(slides.length / slidesToScroll))

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

    // Reinitialize when the responsive grouping changes so the snap count stays correct.
    emblaApi.reInit({ align: 'start', loop, skipSnaps: true, slidesToScroll })
    emblaApi.on('select', updateControls)
    emblaApi.on('reInit', updateControls)
    updateControls()

    return () => {
      emblaApi.off('select', updateControls)
      emblaApi.off('reInit', updateControls)
    }
  }, [emblaApi, loop, slidesToScroll, updateControls])

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
                flex: '0 0 100%',
                minWidth: 0,
                paddingX: theme.spacing(0.625),
                [theme.breakpoints.up('sm')]: {
                  flexBasis: '50%',
                  paddingX: theme.spacing(0.75),
                },
                [theme.breakpoints.up('md')]: {
                  flexBasis: '33.3333%',
                  paddingX: theme.spacing(0.75),
                },
                [theme.breakpoints.up('lg')]: {
                  flexBasis: '33.3333%',
                  paddingX: theme.spacing(0.75),
                },
                [theme.breakpoints.up('xl')]: {
                  flexBasis: '25%',
                  paddingX: theme.spacing(0.75),
                },
              })}
            >
              {slide}
            </Box>
          ))}
        </Box>
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
            <Stack
              component="div"
              direction="row"
              spacing={1}
              justifyContent="center"
              flexWrap="wrap"
              sx={{ flex: 1, minWidth: 0 }}
            >
              {Array.from({ length: snapCount }).map((_, index) => {
                const active = index === selectedIndex

                return (
                  <Box
                    key={index}
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
                      backgroundColor: active ? theme.palette.text.primary : theme.palette.divider,
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
          ) : null}
        </Stack>
      ) : null}

      {showArrows ? (
        <>
          <IconButton
            type="button"
            aria-label={previousLabel}
            onClick={scrollPrev}
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
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.08)',
              opacity: 0,
              pointerEvents: 'none',
              transition: 'opacity 160ms ease, transform 160ms ease, box-shadow 160ms ease',
              '&:hover': {
                backgroundColor: theme.palette.background.paper,
                boxShadow: '0 12px 28px rgba(0, 0, 0, 0.12)',
                transform: 'translate(-56%, -50%)',
              },
              '@media (hover: none)': {
                opacity: 1,
                pointerEvents: 'auto',
              },
              '.MuiBox-root:hover &,&:focus-visible': {
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
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.08)',
              opacity: 0,
              pointerEvents: 'none',
              transition: 'opacity 160ms ease, transform 160ms ease, box-shadow 160ms ease',
              '&:hover': {
                backgroundColor: theme.palette.background.paper,
                boxShadow: '0 12px 28px rgba(0, 0, 0, 0.12)',
                transform: 'translate(56%, -50%)',
              },
              '@media (hover: none)': {
                opacity: 1,
                pointerEvents: 'auto',
              },
              '.MuiBox-root:hover &,&:focus-visible': {
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
  )
}

export default Carousel
