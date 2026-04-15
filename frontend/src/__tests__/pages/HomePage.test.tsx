import { ThemeProvider, createTheme } from '@mui/material/styles'
import { render, screen } from '@testing-library/react'
import { I18nextProvider } from 'react-i18next'
import { MemoryRouter } from 'react-router-dom'

import i18n from '../../i18n'
import HomePage from '../../pages/HomePage'

const renderPage = () =>
  render(
    <MemoryRouter>
      <I18nextProvider i18n={i18n}>
        <ThemeProvider theme={createTheme()}>
          <HomePage />
        </ThemeProvider>
      </I18nextProvider>
    </MemoryRouter>,
  )

describe('HomePage', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('nl')
  })

  it('renders the landing hero and archive links', () => {
    renderPage()

    expect(
      screen.getByRole('heading', {
        name: 'Het levende archief van VIERNULVIER.',
      }),
    ).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Open het archief' })).toHaveAttribute(
      'href',
      '/archive',
    )
    expect(screen.getByRole('link', { name: 'Bekijk reeksen' })).toHaveAttribute('href', '/series')
    expect(screen.getByRole('link', { name: 'Lees verhalen' })).toHaveAttribute('href', '/blogs')
    expect(screen.getByRole('heading', { name: 'Ontdek reeksen' })).toBeInTheDocument()
  })

  it('renders equally tall entry cards', () => {
    const { container } = renderPage()

    const cardLinks = Array.from(container.querySelectorAll('a[href]')).filter((link) =>
      Boolean(link.querySelector('h3')),
    )

    expect(cardLinks).toHaveLength(4)
    cardLinks.forEach((link) => {
      expect(link).toHaveStyle('min-height: 200px')
    })
  })
})
