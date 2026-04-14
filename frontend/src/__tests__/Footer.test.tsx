import { cleanup, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import Footer from '../components/Footer'
import i18n from '../i18n'

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
    expect(screen.getByRole('link', { name: 'Archief' })).toHaveAttribute('href', '/')
    expect(screen.getByRole('link', { name: 'Reeksen' })).toHaveAttribute('href', '/series')
    expect(screen.getByRole('link', { name: 'Evenementen' })).toHaveAttribute('href', '/events')
    expect(screen.getByRole('link', { name: 'Verhalen' })).toHaveAttribute('href', '/blogs')
    expect(screen.getByText('blijf op de hoogte')).toBeInTheDocument()
  })

  it('switches to English footer labels', async () => {
    await i18n.changeLanguage('en')
    renderFooter()

    expect(screen.getByRole('link', { name: 'Archive' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Series' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Events' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Stories' })).toHaveAttribute('href', '/blogs')
    expect(screen.getByText('stay up to date')).toBeInTheDocument()
  })
})
