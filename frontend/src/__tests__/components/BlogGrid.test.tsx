import { render, screen } from '@testing-library/react'
import type { ReactNode } from 'react'
import BlogGrid from '../../components/BlogGrid'
import type { Blog } from '../../types/Blogs'

jest.mock('../../components/BlogGridCard', () => ({
  __esModule: true,
  default: ({ blog }: { blog: Blog }) => <div data-testid="blog-grid-card">{blog.id}</div>,
}))

jest.mock('../../components/GenericGrid', () => ({
  __esModule: true,
  default: ({ items, renderItem }: { items: Blog[]; renderItem: (item: Blog) => ReactNode }) => (
    <div data-testid="generic-grid">
      {items.map((item) => (
        <div key={item.id}>{renderItem(item)}</div>
      ))}
    </div>
  ),
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

describe('BlogGrid', () => {
  it('renders one BlogGridCard per blog via GenericGrid', () => {
    render(
      <BlogGrid blogs={[baseBlog({ id: 1, slug: 'one' }), baseBlog({ id: 2, slug: 'two' })]} />,
    )

    expect(screen.getByTestId('generic-grid')).toBeInTheDocument()
    expect(screen.getAllByTestId('blog-grid-card')).toHaveLength(2)
    expect(screen.getByText('1')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
  })
})
