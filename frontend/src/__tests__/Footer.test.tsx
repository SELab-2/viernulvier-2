import { cleanup, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import i18n from '../i18n'
import Footer from '../shared/Footer'

const renderFooter = () =>
  render(
    <MemoryRouter>
      <Footer />
    </MemoryRouter>,
  )

describe('Footer', () => {
  const initialLanguage = i18n.resolvedLanguage ?? i18n.language ?? 'nl'

  afterEach(async () => {
    cleanup()
    await i18n.changeLanguage(initialLanguage)
  })

  it('renders Dutch footer fields and navigation labels', async () => {
    await i18n.changeLanguage('nl')
    renderFooter()

    expect(screen.getByText('Kunstencentrum VIERNULVIER vzw')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Home' })).toHaveAttribute('href', '/nl')
    expect(screen.getByRole('link', { name: 'Archief' })).toHaveAttribute('href', '/nl/archief')
    expect(screen.getByRole('link', { name: 'Reeksen' })).toHaveAttribute('href', '/nl/reeksen')
    expect(screen.getByRole('link', { name: 'Blogs' })).toHaveAttribute('href', '/nl/blogs')
    expect(screen.getByRole('link', { name: 'Media' })).toHaveAttribute('href', '/nl/media')
    expect(screen.getByText('blijf op de hoogte')).toBeInTheDocument()
  })

  it('switches to English footer labels', async () => {
    await i18n.changeLanguage('en')
    renderFooter()

    expect(screen.getByRole('link', { name: 'Home' })).toHaveAttribute('href', '/en')
    expect(screen.getByRole('link', { name: 'Archive' })).toHaveAttribute('href', '/en/archive')
    expect(screen.getByRole('link', { name: 'Series' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Blogs' })).toHaveAttribute('href', '/en/blogs')
    expect(screen.getByRole('link', { name: 'Media' })).toHaveAttribute('href', '/en/media')
    expect(screen.getByText('stay up to date')).toBeInTheDocument()
  })
})
