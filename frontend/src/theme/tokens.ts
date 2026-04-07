/**
 * Design System Tokens
 *
 * Centralized design system constants used across the application.
 * These tokens ensure consistency in colors, spacing, typography, and other visual properties.
 */

export const tokens = {
  // ============================================================================
  // COLORS
  // ============================================================================

  colors: {
    // Accent (Brand)
    accent: {
      main: '#8224E3',
      contrastText: '#ffffff',
      light: '#9f47f0',
      dark: '#6a1ac7',
    },

    // Light Mode Colors
    light: {
      background: '#f4f5f7',
      surface: '#ffffff',
      text: '#1f1f1f',
      textMuted: '#666666',
      border: '#ebebeb',
      divider: '#e0e0e0',
      hover: '#f9f9f9',
    },

    // Dark Mode Colors
    dark: {
      background: '#0e1021',
      surface: '#181b2f',
      text: '#e6e9fb',
      textMuted: '#b8bed8',
      border: '#2c2f52',
      divider: '#3a3e5c',
      hover: '#1a1f3b',
    },

    // Neutral Colors (used in both themes)
    neutral: {
      black: '#000000',
      white: '#ffffff',
      gray50: '#f9f9f9',
      gray100: '#f3f4f6',
      gray200: '#e5e7eb',
      gray300: '#d1d5db',
      gray400: '#9ca3af',
      gray500: '#6b7280',
      gray600: '#4b5563',
      gray700: '#374151',
      gray800: '#1f2937',
      gray900: '#111111',
    },

    // Overlay and surface-specific colors
    overlay: {
      black05: 'rgba(0,0,0,0.05)',
      footerBorder: 'rgba(255,255,255,0.12)',
      mediaNavDark: 'rgba(10, 14, 40, 0.65)',
      mediaNavLight: 'rgba(255,255,255,0.8)',
    },

    media: {
      darkBackground: '#101436',
      lightBackground: '#f7f7f7',
    },

    // Semantic Colors
    semantic: {
      success: '#10b981',
      error: '#ef4444',
      warning: '#f59e0b',
      info: '#3b82f6',
    },
  },

  // ============================================================================
  // SPACING
  // ============================================================================

  spacing: {
    // Base unit: 4px (scale)
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    '2xl': '48px',
    '3xl': '64px',

    // Numeric for MUI sx prop (units of 8px)
    numericXs: 0.5, // 4px
    numericSm: 1, // 8px
    numericMd: 2, // 16px
    numericLg: 3, // 24px
    numericXl: 4, // 32px
    numeric2xl: 6, // 48px
    numeric3xl: 8, // 64px
  },

  // ============================================================================
  // SHADOWS
  // ============================================================================

  shadows: {
    subtle: '0 1px 2px rgba(0, 0, 0, 0.05)',
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    navbar: '0 1px 0 rgba(255, 255, 255, 0.1)',
    mediaControl: '0 2px 8px rgba(0,0,0,0.24)',
  },

  // ============================================================================
  // TYPOGRAPHY
  // ============================================================================

  typography: {
    fontFamily: ['ABC Monument Grotesk', 'Helvetica', 'Arial', 'sans-serif'].join(','),
    weights: {
      light: 300,
      regular: 400,
      medium: 500,
      bold: 700,
      heavy: 900,
    },
    sizes: {
      xs: '12px',
      sm: '14px',
      base: '16px',
      lg: '18px',
      xl: '20px',
      '2xl': '24px',
      '3xl': '30px',
      '4xl': '36px',
      '5xl': '48px',
    },
    lineHeights: {
      tight: 1.2,
      normal: 1.5,
      relaxed: 1.7,
    },
  },

  // ============================================================================
  // BORDER RADIUS
  // ============================================================================

  borderRadius: {
    none: '0px',
    xs: '2px',
    sm: '4px',
    md: '8px',
    lg: '12px',
    xl: '16px',
    '2xl': '24px',
    full: '9999px',
  },

  // ============================================================================
  // TRANSITIONS
  // ============================================================================

  transitions: {
    fast: '150ms ease',
    base: '200ms ease',
    slow: '300ms ease',
    verySlow: '500ms ease',
  },

  // ============================================================================
  // Z-INDEX
  // ============================================================================

  zIndex: {
    hide: -1,
    base: 0,
    dropdown: 1000,
    sticky: 1020,
    fixed: 1030,
    backdrop: 1040,
    offcanvas: 1050,
    modal: 1060,
    popover: 1070,
    tooltip: 1080,
  },

  // ============================================================================
  // BREAKPOINTS
  // ============================================================================

  breakpoints: {
    xs: '0px',
    sm: '600px',
    md: '960px',
    lg: '1264px',
    xl: '1920px',
  },

  // ============================================================================
  // COMPONENT SPECIFIC
  // ============================================================================

  navbar: {
    minHeight: 64,
  },

  card: {
    borderRadius: 4,
    padding: 3,
    borderRadiusPx: '16px',
    paddingPx: '24px',
  },

  chip: {
    borderRadius: 2,
    paddingY: 1,
    paddingX: 2,
  },
}

export type Tokens = typeof tokens
