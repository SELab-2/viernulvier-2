/**
 * Material-UI Theme Configuration
 *
 * Centralizes all theme creation and palette configuration using design tokens.
 * Supports light and dark modes with semantic color mapping.
 */

import '@mui/material/styles'
import { createTheme, ThemeOptions } from '@mui/material/styles'
import { tokens } from './tokens'

// Type augmentation for custom accent palette
declare module '@mui/material/styles' {
  interface Palette {
    accent: Palette['primary']
  }
  interface PaletteOptions {
    accent?: PaletteOptions['primary']
  }
}

declare module '@mui/material/Button' {
  interface ButtonPropsColorOverrides {
    accent: true
  }
}

/**
 * Creates a Material-UI theme for the given mode (light or dark).
 * All colors reference design tokens for consistency.
 *
 * @param mode - 'light' or 'dark'
 * @returns MUI Theme object ready to use with ThemeProvider
 */
export const createAppTheme = (mode: 'light' | 'dark' = 'light') => {
  const isDark = mode === 'dark'
  const colorSet = isDark ? tokens.colors.dark : tokens.colors.light

  const themeOptions: ThemeOptions = {
    palette: {
      mode,
      primary: {
        main: tokens.colors.accent.main,
        light: tokens.colors.accent.light,
        dark: tokens.colors.accent.dark,
        contrastText: tokens.colors.accent.contrastText,
      },
      accent: {
        main: tokens.colors.accent.main,
        light: tokens.colors.accent.light,
        dark: tokens.colors.accent.dark,
        contrastText: tokens.colors.accent.contrastText,
      },
      background: {
        default: colorSet.background,
        paper: colorSet.surface,
      },
      text: {
        primary: colorSet.text,
        secondary: colorSet.textMuted,
      },
      divider: colorSet.divider,
      ...(isDark && {
        action: {
          hover: colorSet.hover,
          disabled: tokens.colors.dark.textMuted,
          disabledBackground: tokens.colors.dark.border,
        },
      }),
    },
    typography: {
      fontFamily: tokens.typography.fontFamily,
      h1: {
        fontSize: tokens.typography.sizes['5xl'],
        fontWeight: tokens.typography.weights.bold,
        lineHeight: tokens.typography.lineHeights.tight,
      },
      h2: {
        fontSize: tokens.typography.sizes['4xl'],
        fontWeight: tokens.typography.weights.bold,
        lineHeight: tokens.typography.lineHeights.tight,
      },
      h3: {
        fontSize: tokens.typography.sizes['3xl'],
        fontWeight: tokens.typography.weights.bold,
        lineHeight: tokens.typography.lineHeights.tight,
      },
      h4: {
        fontSize: tokens.typography.sizes['2xl'],
        fontWeight: tokens.typography.weights.bold,
        lineHeight: tokens.typography.lineHeights.tight,
      },
      h5: {
        fontSize: tokens.typography.sizes.xl,
        fontWeight: tokens.typography.weights.bold,
        lineHeight: tokens.typography.lineHeights.normal,
      },
      h6: {
        fontSize: tokens.typography.sizes.lg,
        fontWeight: tokens.typography.weights.bold,
        lineHeight: tokens.typography.lineHeights.normal,
      },
      body1: {
        fontSize: tokens.typography.sizes.base,
        lineHeight: tokens.typography.lineHeights.normal,
      },
      body2: {
        fontSize: tokens.typography.sizes.sm,
        lineHeight: tokens.typography.lineHeights.normal,
      },
      button: {
        fontFamily: tokens.typography.fontFamily,
        fontWeight: tokens.typography.weights.medium,
      },
    },
    breakpoints: {
      values: {
        xs: parseInt(tokens.breakpoints.xs),
        sm: parseInt(tokens.breakpoints.sm),
        md: parseInt(tokens.breakpoints.md),
        lg: parseInt(tokens.breakpoints.lg),
        xl: parseInt(tokens.breakpoints.xl),
      },
    },
    shape: {
      borderRadius: parseInt(tokens.borderRadius.md),
    },
    spacing: 8, // 8px base unit for MUI spacing scale
    shadows: [
      'none',
      tokens.shadows.sm,
      tokens.shadows.md,
      tokens.shadows.lg,
      tokens.shadows.xl,
      'none',
      'none',
      'none',
      'none',
      'none',
      'none',
      'none',
      'none',
      'none',
      'none',
      'none',
      'none',
      'none',
      'none',
      'none',
      'none',
      'none',
      'none',
      'none',
      'none',
    ] as const,
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            borderRadius: tokens.borderRadius.md,
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: tokens.borderRadius.lg,
            border: `1px solid ${colorSet.border}`,
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: {
            borderRadius: tokens.borderRadius.md,
          },
        },
      },
    },
  }

  return createTheme(themeOptions)
}

// Export augmentation marker
export {}
