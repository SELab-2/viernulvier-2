import { Box } from '@mui/material'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'

import Carousel from '../../../shared/components/Carousel'

type Listener = () => void

const listeners = {
  select: new Set<Listener>(),
  reInit: new Set<Listener>(),
}

let selectedIndex = 0
let totalSnaps = 2
let loopEnabled = true

function emit(event: keyof typeof listeners) {
  listeners[event].forEach((listener) => listener())
}

jest.mock('embla-carousel-react', () => ({
  __esModule: true,
  default: (options?: { loop?: boolean }) => {
    loopEnabled = options?.loop ?? true

    return [
      jest.fn(),
      {
        selectedScrollSnap: () => selectedIndex,
        scrollSnapList: () => Array.from({ length: totalSnaps }, (_, index) => index),
        canScrollPrev: () => loopEnabled || selectedIndex > 0,
        canScrollNext: () => loopEnabled || selectedIndex < totalSnaps - 1,
        scrollPrev: () => {
          if (!loopEnabled && selectedIndex === 0) {
            return
          }
          selectedIndex = (selectedIndex - 1 + totalSnaps) % totalSnaps
          emit('select')
        },
        scrollNext: () => {
          if (!loopEnabled && selectedIndex >= totalSnaps - 1) {
            return
          }
          selectedIndex = (selectedIndex + 1) % totalSnaps
          emit('select')
        },
        scrollTo: (index: number) => {
          selectedIndex = index
          emit('select')
        },
        reInit: () => emit('reInit'),
        on: (event: keyof typeof listeners, callback: Listener) => {
          listeners[event].add(callback)
        },
        off: (event: keyof typeof listeners, callback: Listener) => {
          listeners[event].delete(callback)
        },
      },
    ]
  },
}))

beforeEach(() => {
  Element.prototype.scrollTo = jest.fn()
})

describe('Carousel', () => {
  beforeEach(() => {
    selectedIndex = 0
    totalSnaps = 2
    loopEnabled = true
    listeners.select.clear()
    listeners.reInit.clear()
  })

  it('renders generic children and exposes navigation controls', async () => {
    render(
      <Carousel
        ariaLabel="Featured productions"
        previousLabel="Previous"
        nextLabel="Next"
        slideLabel="Slide"
      >
        <Box>One</Box>
        <Box>Two</Box>
        <Box>Three</Box>
        <Box>Four</Box>
        <Box>Five</Box>
      </Carousel>,
    )

    expect(screen.getByRole('region', { name: 'Featured productions' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Previous' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Next' })).toBeInTheDocument()

    expect(screen.getAllByRole('button', { name: /Slide/ })).toHaveLength(2)
    expect(screen.getByRole('button', { name: 'Slide 1' })).toHaveAttribute('aria-current', 'true')

    fireEvent.click(screen.getByRole('button', { name: 'Next' }))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Slide 2' })).toHaveAttribute(
        'aria-current',
        'true',
      )
    })

    fireEvent.click(screen.getByRole('button', { name: 'Next' }))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Slide 1' })).toHaveAttribute(
        'aria-current',
        'true',
      )
    })
  })

  it('returns null when no slides are provided', () => {
    const { container } = render(<Carousel ariaLabel="Empty carousel">{[]}</Carousel>)

    expect(container).toBeEmptyDOMElement()
  })

  it('hides arrows and dots when there is only one snap', () => {
    totalSnaps = 1

    render(
      <Carousel
        ariaLabel="Single slide"
        previousLabel="Previous"
        nextLabel="Next"
        slideLabel="Slide"
      >
        <Box>Only one</Box>
      </Carousel>,
    )

    expect(screen.queryByRole('button', { name: 'Previous' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Next' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Slide/ })).not.toBeInTheDocument()
  })

  it('disables edge arrows when loop is off', async () => {
    render(
      <Carousel
        ariaLabel="Non looping"
        previousLabel="Previous"
        nextLabel="Next"
        slideLabel="Slide"
        loop={false}
      >
        <Box>One</Box>
        <Box>Two</Box>
      </Carousel>,
    )

    const previousButton = screen.getByRole('button', { name: 'Previous' })
    const nextButton = screen.getByRole('button', { name: 'Next' })

    await waitFor(() => {
      expect(previousButton).toBeDisabled()
      expect(nextButton).not.toBeDisabled()
    })

    fireEvent.click(nextButton)

    await waitFor(() => {
      expect(previousButton).not.toBeDisabled()
      expect(nextButton).toBeDisabled()
      expect(screen.getByRole('button', { name: 'Slide 2' })).toHaveAttribute(
        'aria-current',
        'true',
      )
    })
  })
})
