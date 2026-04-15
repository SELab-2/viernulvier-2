import { ThemeProvider, createTheme } from '@mui/material/styles'
import { fireEvent, render, screen } from '@testing-library/react'

import ImageWithFallback from '../../components/ImageWithFallback'

import type { ReactElement } from 'react'

const lightTheme = createTheme({ palette: { mode: 'light' } })
const darkTheme = createTheme({ palette: { mode: 'dark' } })

const renderWithTheme = (ui: ReactElement, theme = lightTheme) =>
  render(<ThemeProvider theme={theme}>{ui}</ThemeProvider>)

describe('ImageWithFallback', () => {
  it('renders the remote image when src is provided', () => {
    renderWithTheme(<ImageWithFallback src="https://example.com/poster.jpg" alt="Show poster" />)

    const img = screen.getByRole('img', { name: 'Show poster' })
    expect(img).toHaveAttribute('src', 'https://example.com/poster.jpg')
  })

  it('renders the placeholder when src is null', () => {
    renderWithTheme(<ImageWithFallback src={null} alt="No art" />)

    expect(screen.getByRole('img', { name: 'No art' })).toHaveAttribute('aria-label', 'No art')
    expect(screen.getByAltText('Fallback image')).toHaveAttribute('src', '/vnv_logo.png')
  })

  it('renders the placeholder when src is undefined', () => {
    renderWithTheme(<ImageWithFallback alt="Missing" />)

    expect(screen.getByRole('img', { name: 'Missing' })).toBeInTheDocument()
  })

  it('renders the placeholder when src is an empty string', () => {
    renderWithTheme(<ImageWithFallback src="" alt="Empty" />)

    expect(screen.getByRole('img', { name: 'Empty' })).toBeInTheDocument()
  })

  it('switches to the placeholder after the primary image errors and invokes onError', () => {
    const onError = jest.fn()
    renderWithTheme(
      <ImageWithFallback src="https://example.com/broken.jpg" alt="Broken" onError={onError} />,
    )

    const primary = screen.getByRole('img', { name: 'Broken' })
    fireEvent.error(primary)

    expect(onError).toHaveBeenCalled()
    expect(screen.getByRole('img', { name: 'Broken' })).toBeInTheDocument()
    expect(screen.getByAltText('Fallback image')).toBeInTheDocument()
  })

  it('switches to the placeholder when onError is not provided', () => {
    renderWithTheme(<ImageWithFallback src="https://example.com/broken.jpg" alt="No handler" />)

    fireEvent.error(screen.getByRole('img', { name: 'No handler' }))

    expect(screen.getByAltText('Fallback image')).toBeInTheDocument()
  })

  it('applies dark-mode styling to the fallback logo', () => {
    renderWithTheme(<ImageWithFallback alt="Dark fallback" />, darkTheme)

    const logo = screen.getByAltText('Fallback image')
    expect(logo).toHaveStyle({ filter: 'brightness(0) invert(1)' })
  })

  it('does not apply invert filter in light mode', () => {
    renderWithTheme(<ImageWithFallback alt="Light fallback" />, lightTheme)

    const logo = screen.getByAltText('Fallback image')
    expect(logo).not.toHaveStyle({ filter: 'brightness(0) invert(1)' })
  })

  it('forwards extra Box props to the primary image', () => {
    renderWithTheme(
      <ImageWithFallback
        src="https://example.com/x.png"
        alt="With props"
        data-testid="poster"
        id="poster-img"
      />,
    )

    const img = screen.getByTestId('poster')
    expect(img).toHaveAttribute('id', 'poster-img')
  })

  it('merges sx onto the primary image', () => {
    renderWithTheme(
      <ImageWithFallback
        src="https://example.com/x.png"
        alt="Sized"
        sx={{ width: 120, height: 80 }}
      />,
    )

    const img = screen.getByRole('img', { name: 'Sized' })
    expect(img).toHaveStyle({ width: '120px', height: '80px' })
  })

  it('merges sx onto the fallback placeholder root', () => {
    renderWithTheme(<ImageWithFallback alt="Placeholder" sx={{ minWidth: 64 }} />)

    const placeholder = screen.getByRole('img', { name: 'Placeholder' })
    expect(placeholder).toHaveStyle({ minWidth: '64px' })
  })

  it('does not forward arbitrary DOM props to the fallback root (only the primary img branch spreads props)', () => {
    renderWithTheme(<ImageWithFallback alt="No spread" data-testid="not-on-fallback" />)

    expect(screen.queryByTestId('not-on-fallback')).not.toBeInTheDocument()
    expect(screen.getByRole('img', { name: 'No spread' })).toBeInTheDocument()
  })

  it('passes the native error event to onError', () => {
    const onError = jest.fn()
    renderWithTheme(
      <ImageWithFallback src="https://example.com/bad.png" alt="Err" onError={onError} />,
    )

    const img = screen.getByRole('img', { name: 'Err' })
    fireEvent.error(img, { type: 'error' })

    expect(onError).toHaveBeenCalledTimes(1)
    expect(onError.mock.calls[0][0]).toMatchObject({ type: 'error' })
  })
})
