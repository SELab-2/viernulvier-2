import { render, screen } from '@testing-library/react'
import App from '../App'
import '../i18n'

describe('App', () => {
  it('renders the default title', () => {
    render(<App />)
    expect(screen.getByRole('heading', { name: 'Archive workspace' })).toBeInTheDocument()
  })
})
