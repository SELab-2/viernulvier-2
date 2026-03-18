import { render, screen } from '@testing-library/react'
import App from '../App'
import '../i18n'

describe('App', () => {
  beforeEach(() => {
    window.history.pushState({}, '', '/')
  })

  it('renders navigation', () => {
    render(<App />)
    expect(screen.getByAltText('Viernulvier logo')).toBeInTheDocument()
    expect(screen.getByText('Archief')).toBeInTheDocument()
    expect(screen.getByText('Reeksen')).toBeInTheDocument()
    expect(screen.getByText('Artiesten')).toBeInTheDocument()
  })

  it('renders not found page on unknown route', () => {
    window.history.pushState({}, '', '/does-not-exist')

    render(<App />)

    expect(screen.getByRole('heading', { name: 'Pagina niet gevonden' })).toBeInTheDocument()
    expect(
      screen.getByText('De pagina die je zoekt bestaat niet of is verplaatst.'),
    ).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Terug naar archief' })).toHaveAttribute('href', '/')
  })
})
