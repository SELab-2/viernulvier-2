import { ThemeProvider, createTheme } from '@mui/material/styles'
import { render, screen } from '@testing-library/react'
import { I18nextProvider } from 'react-i18next'
import { MemoryRouter } from 'react-router-dom'

import BlogGridCard from '../../../../features/blogs/components/BlogGridCard'
import i18n from '../../../../i18n'
import { toLocalizedPath } from '../../../../utils/localizedRoutes'

import type { Blog } from '../../../../types/Blogs'

const baseBlog = (overrides: Partial<Blog> = {}): Blog => ({
  id: 7,
  slug: 'blog-7',
  published_at: '2026-04-23T10:00:00Z',
  cover_image: 'https://example.test/blog.jpg',
  title: { nl: 'Blogtitel', en: 'Blog title' },
  body: { nl: 'Body' },
  excerpt: { nl: '<p>Korte tekst</p>', en: '<p>Short text</p>' },
  display_title: 'Blogtitel',
  display_excerpt: 'Korte tekst',
  productions: [],
  ...overrides,
})

const renderCard = (blog: Blog) =>
  render(
    <MemoryRouter>
      <I18nextProvider i18n={i18n}>
        <ThemeProvider theme={createTheme()}>
          <BlogGridCard blog={blog} />
        </ThemeProvider>
      </I18nextProvider>
    </MemoryRouter>,
  )

describe('BlogGridCard', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('nl')
  })

  it('renders localized blog content and links to the detail route', () => {
    renderCard(baseBlog())

    expect(screen.getByRole('heading', { name: 'Blogtitel' })).toBeInTheDocument()
    expect(screen.getByText('Korte tekst')).toBeInTheDocument()
    expect(screen.getByRole('link')).toHaveAttribute('href', toLocalizedPath('/blogs/7', 'nl'))
    expect(screen.getByRole('img', { name: 'Blogtitel' })).toHaveAttribute(
      'src',
      'https://example.test/blog.jpg',
    )
    expect(screen.getByText(/2026/)).toBeInTheDocument()
  })

  it('uses fallback labels when title, excerpt, image and publication date are missing', () => {
    renderCard(
      baseBlog({
        published_at: null,
        cover_image: null,
        title: {},
        excerpt: {},
        display_title: '',
        display_excerpt: '',
      }),
    )

    expect(screen.getByRole('heading', { name: 'Geen titel beschikbaar' })).toBeInTheDocument()
    expect(screen.getByText('Geen samenvatting beschikbaar.')).toBeInTheDocument()
    expect(screen.getByText('Niet gepubliceerd')).toBeInTheDocument()
    expect(screen.getByAltText('Fallback image')).toBeInTheDocument()
  })
})
