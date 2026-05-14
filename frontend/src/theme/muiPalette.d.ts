/**
 * MUI theme augmentation for custom design tokens.
 *
 * This module extends the default Material UI theme typings to include
 * additional custom palette colors and enables their usage in components
 * such as Button via the `color` prop.
 *
 * It ensures TypeScript recognizes custom theme extensions consistently
 * across the application.
 */

import '@mui/material/styles'

/**
 * Extends the MUI Palette to include a custom `accent` color.
 */
declare module '@mui/material/styles' {
  interface Palette {
    accent: Palette['primary']
  }

  interface PaletteOptions {
    accent?: PaletteOptions['primary']
  }
}

/**
 * Enables usage of `color="accent"` on MUI Button components.
 */
declare module '@mui/material/Button' {
  interface ButtonPropsColorOverrides {
    accent: true
  }
}

export {}
