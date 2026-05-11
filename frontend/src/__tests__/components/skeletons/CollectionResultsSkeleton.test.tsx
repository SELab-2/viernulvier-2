import { ThemeProvider, createTheme } from '@mui/material/styles'
import { render, screen } from '@testing-library/react'

import CollectionResultsSkeleton from '../../../shared/components/skeletons/CollectionResultsSkeleton'

import type { ComponentProps } from 'react'

const renderSkeleton = (props?: Partial<ComponentProps<typeof CollectionResultsSkeleton>>) =>
  render(
    <ThemeProvider theme={createTheme()}>
      <CollectionResultsSkeleton layout="grid" isMobile={false} {...props} />
    </ThemeProvider>,
  )

const skeletonCount = (container: HTMLElement) =>
  container.querySelectorAll('.MuiSkeleton-root').length

describe('CollectionResultsSkeleton', () => {
  it('uses twelve cards by default when card count is omitted', () => {
    const { container } = renderSkeleton()

    expect(screen.getByTestId('collection-results-skeleton')).toBeInTheDocument()
    expect(skeletonCount(container)).toBe(48)
  })

  it('renders list placeholders with three text skeletons per card', () => {
    const { container } = renderSkeleton({ layout: 'list', cards: 4 })

    expect(screen.getByTestId('collection-results-skeleton')).toBeInTheDocument()
    expect(skeletonCount(container)).toBe(12)
  })

  it('renders grid placeholders with image and text skeletons per card', () => {
    const { container } = renderSkeleton({ layout: 'grid', cards: 3 })

    expect(screen.getByTestId('collection-results-skeleton')).toBeInTheDocument()
    expect(skeletonCount(container)).toBe(12)
  })

  it('forces grid placeholders on mobile even when list layout is requested', () => {
    const { container } = renderSkeleton({ layout: 'list', isMobile: true, cards: 2 })

    expect(screen.getByTestId('collection-results-skeleton')).toBeInTheDocument()
    expect(skeletonCount(container)).toBe(8)
  })
})
