import { render, screen } from '@testing-library/react'

import BlogList from '../../../../features/blogs/components/BlogList'

import type { Blog } from '../../../../types/Blogs'
import type { ReactNode } from 'react'

jest.mock('../../../../features/blogs/components/BlogListCard', () => ({
  __esModule: true,
  default: ({ blog }: { blog: Blog }) => <div data-testid="blog-list-card">{blog.id}</div>,
}))

jest.mock('../../../../shared/components/GenericList', () => ({
  __esModule: true,
  default: ({ items, renderItem }: { items: Blog[]; renderItem: (item: Blog) => ReactNode }) => (
    <div data-testid="generic-list">
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

describe('BlogList', () => {
  it('renders one BlogListCard per blog via GenericList', () => {
    render(
      <BlogList blogs={[baseBlog({ id: 1, slug: 'one' }), baseBlog({ id: 2, slug: 'two' })]} />,
    )

    expect(screen.getByTestId('generic-list')).toBeInTheDocument()
    expect(screen.getAllByTestId('blog-list-card')).toHaveLength(2)
    expect(screen.getByText('1')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
  })
})
