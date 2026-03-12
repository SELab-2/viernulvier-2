import { render, screen } from '@testing-library/react'
import App from '../App'
import '../i18n'

describe('App', () => {
  it('renders navigation', () => {
    render(<App />)
    expect(screen.getByText('Archive')).toBeInTheDocument()
    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.getByText('Events')).toBeInTheDocument()
  })
})
