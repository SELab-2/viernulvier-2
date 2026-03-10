import { render, screen } from '@testing-library/react'
import App from '../App'
import '../i18n'

describe('App', () => {
  it('renders navigation', () => {
    render(<App />)
    expect(screen.getByAltText('Viernulvier logo')).toBeInTheDocument()
    expect(screen.getByText('Archief')).toBeInTheDocument()
    expect(screen.getByText('Reeksen')).toBeInTheDocument()
    expect(screen.getByText('Artiesten')).toBeInTheDocument()
  })
})
