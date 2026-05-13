import { render } from '@testing-library/react'

import MediaFilesPageSkeleton from '../../../../features/media-files/pages/MediaFilesPageSkeleton'

const skeletonCount = (container: HTMLElement) =>
  container.querySelectorAll('.MuiSkeleton-root').length

describe('MediaFilesPageSkeleton', () => {
  it('renders the requested number of grid skeleton cards by default', () => {
    const { container } = render(<MediaFilesPageSkeleton cards={3} />)

    expect(skeletonCount(container)).toBe(21)
  })

  it('caps list skeleton rendering to eight cards', () => {
    const { container } = render(<MediaFilesPageSkeleton layout="list" cards={12} />)

    expect(skeletonCount(container)).toBe(56)
  })

  it('forces grid skeletons on mobile even when list layout is requested', () => {
    const { container } = render(<MediaFilesPageSkeleton layout="list" isMobile cards={2} />)

    expect(skeletonCount(container)).toBe(14)
  })
})
