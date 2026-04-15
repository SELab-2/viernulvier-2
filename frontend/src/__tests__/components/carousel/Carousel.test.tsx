import { Box } from '@mui/material'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'

import Carousel from '../../../components/carousel/Carousel'

type Listener = () => void

const listeners = {
  select: new Set<Listener>(),
  reInit: new Set<Listener>(),
}

let selectedIndex = 0
const totalSnaps = 2

function emit(event: keyof typeof listeners) {
  listeners[event].forEach((listener) => listener())
}

jest.mock('embla-carousel-react', () => ({
  __esModule: true,
  default: () => [
    jest.fn(),
    {
      selectedScrollSnap: () => selectedIndex,
      scrollSnapList: () => Array.from({ length: totalSnaps }, (_, index) => index),
      canScrollPrev: () => totalSnaps > 1,
      canScrollNext: () => totalSnaps > 1,
      scrollPrev: () => {
        selectedIndex = (selectedIndex - 1 + totalSnaps) % totalSnaps
        emit('select')
      },
      scrollNext: () => {
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
  ],
}))

beforeEach(() => {
  Element.prototype.scrollTo = jest.fn()
})

describe('Carousel', () => {
  beforeEach(() => {
    selectedIndex = 0
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
})
