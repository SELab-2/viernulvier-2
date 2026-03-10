import { render, screen } from '@testing-library/react'
import App from '../App'
import '../i18n'

describe('App', () => {
  it('renders navigation', () => {
    render(<App />)
    expect(screen.getByAltText('Viernulvier logo')).toBeInTheDocument()
    expect(screen.getByText('Archive')).toBeInTheDocument()
    expect(screen.getByText('Series')).toBeInTheDocument()
    expect(screen.getByText('Artists')).toBeInTheDocument()
  })
})
