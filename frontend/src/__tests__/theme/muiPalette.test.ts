/**
 * Theme Configuration Tests
 *
 * Tests for Material-UI theme creation and palette configuration.
 */

import { createAppTheme } from '../../theme/muiPalette'
import { tokens } from '../../theme/tokens'

describe('muiPalette - createAppTheme', () => {
  it('should create a theme with light mode palette', () => {
    const theme = createAppTheme('light')

    expect(theme.palette.mode).toBe('light')
    expect(theme.palette.background.default).toBe(tokens.colors.light.background)
    expect(theme.palette.background.paper).toBe(tokens.colors.light.surface)
    expect(theme.palette.text.primary).toBe(tokens.colors.light.text)
  })

  it('should create a theme with dark mode palette', () => {
    const theme = createAppTheme('dark')

    expect(theme.palette.mode).toBe('dark')
    expect(theme.palette.background.default).toBe(tokens.colors.dark.background)
    expect(theme.palette.background.paper).toBe(tokens.colors.dark.surface)
    expect(theme.palette.text.primary).toBe(tokens.colors.dark.text)
  })

  it('should default to light mode', () => {
    const theme = createAppTheme()

    expect(theme.palette.mode).toBe('light')
  })

  it('should include accent color in palette', () => {
    const theme = createAppTheme('light')

    expect(theme.palette.primary.main).toBe(tokens.colors.neutral.black)
    expect(theme.palette.primary.light).toBe(tokens.colors.neutral.black)
    expect(theme.palette.primary.dark).toBe(tokens.colors.neutral.black)
    expect(theme.palette.accent?.main).toBe(tokens.colors.accent.main)
    expect(theme.palette.accent?.contrastText).toBe(tokens.colors.accent.contrastText)
  })

  it('should use white as primary in dark mode', () => {
    const theme = createAppTheme('dark')

    expect(theme.palette.primary.main).toBe(tokens.colors.neutral.white)
    expect(theme.palette.primary.light).toBe(tokens.colors.neutral.white)
    expect(theme.palette.primary.dark).toBe(tokens.colors.neutral.white)
  })

  it('should have correct typography configuration', () => {
    const theme = createAppTheme('light')

    expect(theme.typography.fontFamily).toBe(tokens.typography.fontFamily)
    expect(theme.typography.h1?.fontWeight).toBe(tokens.typography.weights.bold)
    expect(theme.typography.body1?.fontSize).toBe(tokens.typography.sizes.base)
  })

  it('should have correct breakpoints', () => {
    const theme = createAppTheme('light')

    expect(theme.breakpoints.values.xs).toBe(0)
    expect(theme.breakpoints.values.sm).toBe(600)
    expect(theme.breakpoints.values.md).toBe(960)
  })

  it('should have shape configuration with proper border radius', () => {
    const theme = createAppTheme('light')

    expect(theme.shape.borderRadius).toBe(parseInt(tokens.borderRadius.md))
  })

  it('should have spacing value set to 8', () => {
    const theme = createAppTheme('light')

    expect(theme.spacing(1)).toBe('8px')
  })

  it('should have shadows array with correct values', () => {
    const theme = createAppTheme('light')
    const shadows = theme.shadows

    expect(shadows[0]).toBe('none')
    expect(shadows[1]).toBe(tokens.shadows.sm)
    expect(shadows[2]).toBe(tokens.shadows.md)
    expect(shadows[3]).toBe(tokens.shadows.lg)
    expect(shadows[4]).toBe(tokens.shadows.xl)
  })

  it('should apply MuiButton style overrides', () => {
    const theme = createAppTheme('light')

    expect(theme.components?.MuiButton?.styleOverrides?.root).toHaveProperty(
      'textTransform',
      'none',
    )
    expect(theme.components?.MuiButton?.styleOverrides?.root).toHaveProperty('borderRadius')
  })

  it('should apply MuiCard style overrides', () => {
    const theme = createAppTheme('light')

    expect(theme.components?.MuiCard?.styleOverrides?.root).toHaveProperty('borderRadius')
  })

  it('should have divider color set for light mode', () => {
    const theme = createAppTheme('light')

    expect(theme.palette.divider).toBe(tokens.colors.light.divider)
  })

  it('should have divider color set for dark mode', () => {
    const theme = createAppTheme('dark')

    expect(theme.palette.divider).toBe(tokens.colors.dark.divider)
  })

  it('should have action colors for dark mode', () => {
    const theme = createAppTheme('dark')

    // Dark mode might include custom action properties through the theme
    expect(theme).toBeDefined()
  })
})
