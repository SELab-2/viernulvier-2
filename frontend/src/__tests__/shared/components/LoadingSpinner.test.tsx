import { ThemeProvider, createTheme } from '@mui/material/styles'
import { render, screen } from '@testing-library/react'

import LoadingSpinner from '../../../shared/components/LoadingSpinner'

import type { ReactNode } from 'react'

const renderWithTheme = (mode: 'light' | 'dark', ui: ReactNode = <LoadingSpinner />) => {
  const theme = createTheme({
    palette: {
      mode,
    },
  })

  return {
    theme,
    ...render(<ThemeProvider theme={theme}>{ui}</ThemeProvider>),
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
    expect(spinner).toHaveStyle({ position: 'fixed', inset: '0' })

    // Verify size={48} is forwarded to the CircularProgress element.
    const progress = screen.getByRole('progressbar')
    expect(progress).toHaveStyle({ width: '48px', height: '48px' })
  })

  it('prefers an explicit color over the theme default', () => {
    renderWithTheme('light', <LoadingSpinner color="#ff5500" label="Custom color" />)

    expect(screen.getByText('Custom color')).toHaveStyle({ color: '#ff5500' })
  })
})
