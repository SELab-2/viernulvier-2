/**
 * Reusable MUI sx Pattern Styles
 *
 * This module centralizes commonly used `sx` style objects for MUI components.
 * It helps reduce duplication and ensures consistent styling across the app.
 *
 * Styles are grouped by usage domain (navbar, layout, cards, etc.) and are
 * designed to be consumed via `sx={commonStyles.cardBase}` etc.
 */

import { alpha } from '@mui/material/styles'

import { tokens } from './tokens'
import { DarkMode } from '../types/Theme'

import type { SxProps, SystemStyleObject, Theme } from '@mui/system'

/**
 * Creates reusable navbar-related style objects.
 *
 * These styles define layout and visual rules for navigation elements such as
 * links, branding, and active states.
 *
 * @returns Object containing navbar-related sx style definitions
 */
export const createNavbarStyles = () => {
  return {
    /**
     * Style applied to the active navigation link.
     */
    activeLink: {
      borderBottomColor: tokens.colors.neutral.white,
    } as SystemStyleObject<Theme>,

    /**
     * Base styling for navigation links.
     */
    navLink: {
      textTransform: 'none',
      fontSize: '1.05rem',
      letterSpacing: '0.02em',
      fontWeight: tokens.typography.weights.regular,
      borderBottom: '2px solid transparent',
      borderRadius: 0,
      py: 0.75,
      '&:hover': { bgcolor: 'transparent' },
    } as SystemStyleObject<Theme>,

    /**
     * Branding link container styling.
     */
    brandLink: {
      flex: '0 1 auto',
      width: 'fit-content',
      maxWidth: '100%',
      display: 'inline-flex',
      alignItems: 'center',
      gap: { xs: '0.22em', sm: '0.35em' },
      minWidth: 0,
      fontSize: 'clamp(0.06rem, calc((100vw - 280px) / 240 + 0.56rem), 1rem)',
      lineHeight: 1,
      textDecoration: 'none',
      whiteSpace: 'nowrap',
      overflow: 'hidden',
      pr: { xs: 0, sm: 0.25 },
      mr: 'auto',
    } as SystemStyleObject<Theme>,

    /**
     * Logo image styling inside the brand area.
     */
    brandLogo: {
      maxHeight: '2.45em',
      width: '100%',
      minWidth: '185px',
      height: 'auto',
      flexShrink: 0,
      display: 'block',
      filter: 'brightness(0) invert(1)',
    } as SystemStyleObject<Theme>,

    /**
     * Text styling for archive branding label.
     */
    brandArchiveText: {
      display: 'block',
      color: tokens.colors.neutral.white,
      fontWeight: tokens.typography.weights.regular,
      letterSpacing: '0.03em',
      fontSize: '1.1em',
      lineHeight: 1,
      transform: 'translateY(4.5px)',
      whiteSpace: 'nowrap',
      minWidth: 0,
    } as SystemStyleObject<Theme>,
  }
}

/**
 * Creates shared UI style patterns based on the active theme.
 *
 * These styles are used across components such as cards, grids, layout
 * containers, and UI primitives like chips and links.
 *
 * @param theme Active MUI theme instance
 * @returns Object containing reusable sx style definitions
 */
export const createCommonStyles = (theme: Theme) => {
  return {
    /**
     * Base card styling: shadow, rounded corners, background.
     * Used as foundation for card components across the app.
     */
    cardBase: {
      borderRadius: tokens.card.borderRadiusPx,
      overflow: 'hidden',
      textDecoration: 'none',
      border: `1px solid ${theme.palette.divider}`,
      backgroundColor: theme.palette.background.paper,
      transition: tokens.transitions.base,
      '&:hover': {
        boxShadow: tokens.shadows.md,
      },
    } as SxProps<Theme>,

    /**
     * Grid container for card layouts using auto-fill behavior.
     *
     * Ensures responsive wrapping without manual breakpoint handling.
     */
    gridContainer: {
      display: 'grid',
      gridTemplateColumns: `repeat(auto-fill, min(${tokens.card.gridCardWidthPx}px, 100%))`,
      gap: tokens.spacing.numericLg,
      alignItems: 'stretch',
      justifyContent: 'var(--grid-align, center)',
    } as SxProps<Theme>,

    /**
     * Navbar container styling.
     */
    navbar: {
      bgcolor: tokens.colors.neutral.black,
      boxShadow: tokens.shadows.navbar,
      position: 'sticky',
      top: 0,
      zIndex: tokens.zIndex.sticky,
    } as SxProps<Theme>,

    /**
     * Footer container styling.
     */
    footer: {
      bgcolor: tokens.colors.neutral.gray900,
      color: tokens.colors.neutral.white,
      borderTop: `1px solid ${tokens.colors.overlay.footerBorder}`,
      mt: tokens.spacing.numericLg,
      fontStyle: 'normal',
      lineHeight: tokens.typography.lineHeights.relaxed,
      whiteSpace: 'nowrap',
    } as SxProps<Theme>,

    /**
     * Responsive media image styling (16:9 ratio).
     */
    responseImage: {
      aspectRatio: '16 / 9',
      objectFit: 'cover',
      width: '100%',
      height: 'auto',
    } as SxProps<Theme>,

    /**
     * Link hover effect with opacity transition.
     */
    linkHover: {
      transition: tokens.transitions.fast,
      '&:hover': {
        opacity: 0.7,
      },
    } as SxProps<Theme>,

    /**
     * Base chip styling.
     */
    chipBase: {
      borderRadius: tokens.borderRadius.md,
      padding: `${tokens.spacing.sm} ${tokens.spacing.md}`,
      cursor: 'pointer',
      transition: tokens.transitions.fast,
    } as SxProps<Theme>,

    /**
     * Centered max-width layout container.
     */
    container: {
      maxWidth: '1264px',
      mx: 'auto',
      px: {
        xs: tokens.spacing.numericSm,
        sm: tokens.spacing.numericMd,
        md: tokens.spacing.numericXl,
      },
    } as SxProps<Theme>,

    /**
     * Vertical stack layout.
     */
    stack: {
      display: 'flex',
      flexDirection: 'column',
      gap: tokens.spacing.numericMd,
    } as SxProps<Theme>,

    /**
     * Truncated text with ellipsis.
     */
    textTruncate: {
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      whiteSpace: 'nowrap',
      transition: tokens.transitions.base,
    } as SxProps<Theme>,

    /**
     * Centered content container.
     */
    centerContent: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    } as SxProps<Theme>,
  }
}

/**
 * Creates home page specific style tokens derived from theme mode.
 *
 * These styles are used for hero sections, cards, inputs, and subtle UI
 * effects that differ between light and dark mode.
 *
 * @param theme Active MUI theme instance
 * @returns Object containing homepage-specific style values
 */
export const createHomePageStyles = (theme: Theme) => {
  return {
    // Hero
    heroOverlay:
      'linear-gradient(to bottom, rgba(8,10,14,0.08) 0%, rgba(8,10,14,0.52) 55%, rgba(8,10,14,0.88) 100%)',
    heroOverlayVignette:
      'radial-gradient(ellipse at 70% 40%, transparent 40%, rgba(8,10,14,0.30) 100%)',
    heroFallbackGradient:
      'linear-gradient(135deg, rgba(8,10,14,1) 0%, rgba(18,28,58,1) 45%, rgba(12,38,52,1) 75%, rgba(8,10,14,1) 100%)' /** Small decorative label above the main title */,
    heroEyebrowColor: 'rgba(255,255,255,0.65)' as const,
    heroTitleColor: theme.palette.common.white,
    heroDescriptionColor: alpha(theme.palette.common.white, 0.82),

    // Search
    searchIconColor: 'rgba(0,0,0,0.40)',
    searchInputBg: 'rgba(255,255,255,0.96)',
    searchInputText: 'rgba(0,0,0,0.87)',
    searchInputPlaceholder: 'rgba(0,0,0,0.40)',
    searchInputBorder: 'rgba(0,0,0,0.12)',
    searchInputBorderHover: 'rgba(0,0,0,0.28)',
    searchInputBorderFocus: 'rgba(0,0,0,0.54)',
    searchButtonBg: tokens.colors.neutral.black,
    searchButtonBgHover: '#333333',
    searchButtonText: tokens.colors.neutral.white,

    // CTA buttons
    primaryButtonBg: theme.palette.common.white,
    primaryButtonText: tokens.colors.neutral.black,
    primaryButtonBgHover: alpha(theme.palette.common.white, 0.88),

    secondaryButtonBorder: alpha(theme.palette.common.white, 0.5),
    secondaryButtonBorderHover: alpha(theme.palette.common.white, 0.8),
    secondaryButtonBgHover: alpha(theme.palette.common.white, 0.1),
    secondaryButtonText: theme.palette.common.white,

    tertiaryButtonText: alpha(theme.palette.common.white, 0.8),
    tertiaryButtonTextHover: theme.palette.common.white,

    // Stats bar
    statBarBg: theme.palette.background.paper,
    statValueColor: theme.palette.text.primary,
    statLabelColor: theme.palette.text.secondary,

    // Photo cards
    cardOverlay:
      'linear-gradient(to top, rgba(0,0,0,0.80) 0%, rgba(0,0,0,0.20) 55%, transparent 100%)',
    cardOverlayHover:
      'linear-gradient(to top, rgba(0,0,0,0.90) 0%, rgba(0,0,0,0.35) 60%, transparent 100%)',

    // Misc utility (mode-aware)
    inputBackground:
      theme.palette.mode === DarkMode
        ? alpha(theme.palette.common.white, 0.04)
        : theme.palette.background.paper,
    tickerBackground:
      theme.palette.mode === DarkMode
        ? alpha(theme.palette.common.white, 0.04)
        : alpha(theme.palette.common.black, 0.03),
    tickerText:
      theme.palette.mode === DarkMode
        ? alpha(theme.palette.common.white, 0.38)
        : alpha(theme.palette.common.black, 0.42),
    subtleSurface:
      theme.palette.mode === DarkMode
        ? alpha(theme.palette.common.white, 0.03)
        : alpha(theme.palette.common.black, 0.02),
    cardHoverBackground:
      theme.palette.mode === DarkMode
        ? alpha(theme.palette.common.white, 0.04)
        : alpha(theme.palette.common.black, 0.02),
    cardHoverBorder:
      theme.palette.mode === DarkMode
        ? alpha(theme.palette.common.white, 0.2)
        : alpha(theme.palette.common.black, 0.18),
    accentBorder:
      theme.palette.mode === DarkMode
        ? alpha(theme.palette.common.white, 0.12)
        : alpha(theme.palette.common.black, 0.1),
  }
}

/**
 * Type helper representing the return type of createCommonStyles.
 */
export type CommonStyles = ReturnType<typeof createCommonStyles>
