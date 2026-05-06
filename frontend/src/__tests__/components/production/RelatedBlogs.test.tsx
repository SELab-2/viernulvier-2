import { render, screen } from '@testing-library/react'

import RelatedBlogs from '../../../components/production/RelatedBlogs'

import type { Blog } from '../../../types/Blogs'
import type { ReactNode } from 'react'

jest.mock('../../../components/BlogGridCard', () => ({
  __esModule: true,
  default: ({ blog }: { blog: Blog }) => (
    <article data-testid="blog-card">{blog.display_title}</article>
  ),
}))

jest.mock('../../../components/carousel/Carousel', () => ({
  __esModule: true,
  default: ({
    children,
    ariaLabel,
    previousLabel,
    nextLabel,
    slideLabel,
  }: {
    children: ReactNode
    ariaLabel: string
    previousLabel: string
    nextLabel: string
    slideLabel: string
  }) => (
    <section
      aria-label={ariaLabel}
      data-next-label={nextLabel}
      data-previous-label={previousLabel}
      data-slide-label={slideLabel}
    >
      {children}
    </section>
  ),
}))

jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, fallback?: string) => {
      const translations: Record<string, string> = {
        'productions.detail.relatedBlogs': 'Gerelateerde blogs',
        'carousel.previousSlide': 'Vorige slide',
        'carousel.nextSlide': 'Volgende slide',
        'carousel.goToSlide': 'Ga naar slide',
      }

      return translations[key] ?? fallback ?? key
    },
  }),
}))

const baseBlog = (overrides: Partial<Blog> = {}): Blog => ({
  id: 1,
  slug: 'blog-1',
  published_at: null,
  cover_image: null,
  title: { nl: 'Blog' },
  body: { nl: 'Body' },
  excerpt: { nl: 'Excerpt' },
  display_title: 'Blog',
  display_excerpt: 'Excerpt',
  productions: [],
  ...overrides,
})

describe('RelatedBlogs', () => {
  it('renders nothing when there are no related blogs', () => {
    const { container } = render(<RelatedBlogs blogs={[]} />)

    expect(container).toBeEmptyDOMElement()
  })

  it('renders related blog cards inside a labelled carousel', () => {
    render(
      <RelatedBlogs
        blogs={[
          baseBlog({ id: 1, display_title: 'Blog one' }),
          baseBlog({ id: 2, display_title: 'Blog two' }),
        ]}
      />,
    )

    const carousel = screen.getByRole('region', { name: 'Gerelateerde blogs' })
    expect(carousel).toHaveAttribute('data-previous-label', 'Vorige slide')
    expect(carousel).toHaveAttribute('data-next-label', 'Volgende slide')
    expect(carousel).toHaveAttribute('data-slide-label', 'Ga naar slide')
    expect(screen.getAllByTestId('blog-card')).toHaveLength(2)
    expect(screen.getByText('Blog one')).toBeInTheDocument()
    expect(screen.getByText('Blog two')).toBeInTheDocument()
  })
})
