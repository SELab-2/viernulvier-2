import { render, screen } from '@testing-library/react'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import LoadingSpinner from '../components/LoadingSpinner'

const renderWithTheme = (mode: 'light' | 'dark') => {
  const theme = createTheme({
    palette: {
      mode,
    },
  })

  return {
    theme,
    ...render(
      <ThemeProvider theme={theme}>
        <LoadingSpinner />
      </ThemeProvider>,
    ),
  }
}

describe('LoadingSpinner', () => {
  it('renders with default label and status attributes', () => {
    render(<LoadingSpinner />)

    const spinner = screen.getByTestId('loading-spinner')
    expect(spinner).toBeInTheDocument()
    expect(spinner).toHaveAttribute('role', 'status')
    expect(spinner).toHaveAttribute('aria-label', 'Loading')
    expect(screen.getByText('Loading')).toBeInTheDocument()
  })

  it('uses the active theme text color by default', () => {
    const { theme } = renderWithTheme('dark')

    expect(screen.getByText('Loading')).toHaveStyle({ color: theme.palette.text.primary })
  })

  it('supports custom label, size, and fullscreen layout', () => {
    render(<LoadingSpinner label="Fetching events" size={48} fullScreen />)

    const spinner = screen.getByTestId('loading-spinner')
    expect(spinner).toHaveAttribute('aria-label', 'Fetching events')
    expect(screen.getByText('Fetching events')).toBeInTheDocument()
    expect(spinner).toHaveStyle({ width: '100vw', minHeight: '100vh' })
  })

  it('prefers an explicit color over the theme default', () => {
    renderWithTheme('light')
    render(<LoadingSpinner color="#ff5500" label="Custom color" />)

    expect(screen.getByText('Custom color')).toHaveStyle({ color: '#ff5500' })
  })
})
