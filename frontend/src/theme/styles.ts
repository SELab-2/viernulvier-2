/**
 * Reusable MUI sx Pattern Styles
 *
 * Exports common sx prop patterns used across components.
 * Centralized here to reduce duplication and ensure consistency.
 * Each function takes a theme and returns an SxProps<Theme> object.
 */

import { alpha } from '@mui/material/styles'

import { tokens } from './tokens'

import type { SxProps, SystemStyleObject, Theme } from '@mui/system'

export const createNavbarStyles = () => {
  return {
    activeLink: {
      borderBottomColor: tokens.colors.neutral.white,
    } as SystemStyleObject<Theme>,

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

    brandLogo: {
      height: '2.45em',
      width: 'auto',
      flexShrink: 0,
      display: 'block',
      filter: 'brightness(0) invert(1)',
    } as SystemStyleObject<Theme>,

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

export const createCommonStyles = (theme: Theme) => {
  return {
    /**
     * Base card styling: shadow, rounded corners, background.
     * Use as base for ProductionGridCard, ProductionListCard, etc.
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
     * Grid container for wrapping card layouts.
     */
    gridContainer: {
      display: 'grid',
      gridTemplateColumns: `repeat(auto-fit, min(${tokens.card.gridCardWidthPx}px, 100%))`,
      gap: tokens.spacing.numericLg,
      alignItems: 'stretch',
      justifyContent: 'center',
    } as SxProps<Theme>,

    /**
     * Navbar styling: sticky positioning, dark background.
     */
    navbar: {
      bgcolor: tokens.colors.neutral.black,
      boxShadow: tokens.shadows.navbar,
      position: 'sticky',
      top: 0,
      zIndex: tokens.zIndex.sticky,
    } as SxProps<Theme>,

    /**
     * Footer styling: dark background with contrast text.
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
     * Responsive image placeholder (aspect ratio 16/9).
     * Used in production cards for consistent image sizing.
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
     * Chip base: rounded, padded container.
     */
    chipBase: {
      borderRadius: tokens.borderRadius.md,
      padding: `${tokens.spacing.sm} ${tokens.spacing.md}`,
      cursor: 'pointer',
      transition: tokens.transitions.fast,
    } as SxProps<Theme>,

    /**
     * Container with maximum width and centered content.
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
     * Stack with vertical spacing and gap management.
     */
    stack: {
      display: 'flex',
      flexDirection: 'column',
      gap: tokens.spacing.numericMd,
    } as SxProps<Theme>,

    /**
     * Text that should be truncated with ellipsis.
     */
    textTruncate: {
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      whiteSpace: 'nowrap',
      transition: tokens.transitions.base,
    } as SxProps<Theme>,

    /**
     * Base styling for loading spinners or empty states.
     */
    centerContent: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    } as SxProps<Theme>,
  }
}

export const createHomePageStyles = (theme: Theme) => {
  const isDark = theme.palette.mode === 'dark'

  return {
    heroBackground: isDark
      ? 'linear-gradient(160deg, rgba(255,255,255,0.05) 0%, transparent 60%)'
      : 'linear-gradient(160deg, rgba(0,0,0,0.03) 0%, transparent 60%)',
    heroAccentLine: isDark
      ? 'linear-gradient(90deg, transparent, rgba(255,255,255,0.25) 40%, rgba(255,255,255,0.1) 70%, transparent)'
      : 'linear-gradient(90deg, transparent, rgba(0,0,0,0.15) 40%, rgba(0,0,0,0.06) 70%, transparent)',
    heroPanelBackground: isDark
      ? alpha(theme.palette.common.white, 0.03)
      : alpha(theme.palette.common.white, 0.82),
    inputBackground: isDark
      ? alpha(theme.palette.common.white, 0.04)
      : theme.palette.background.paper,
    tickerBackground: isDark
      ? alpha(theme.palette.common.white, 0.04)
      : alpha(theme.palette.common.black, 0.03),
    tickerText: isDark
      ? alpha(theme.palette.common.white, 0.38)
      : alpha(theme.palette.common.black, 0.42),
    subtleSurface: isDark
      ? alpha(theme.palette.common.white, 0.03)
      : alpha(theme.palette.common.black, 0.02),
    cardHoverBackground: isDark
      ? alpha(theme.palette.common.white, 0.04)
      : alpha(theme.palette.common.black, 0.02),
    cardHoverBorder: isDark
      ? alpha(theme.palette.common.white, 0.2)
      : alpha(theme.palette.common.black, 0.18),
    accentBorder: isDark
      ? alpha(theme.palette.common.white, 0.12)
      : alpha(theme.palette.common.black, 0.1),
  }
}

export type CommonStyles = ReturnType<typeof createCommonStyles>
