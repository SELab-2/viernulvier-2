/**
 * Reusable MUI sx Pattern Styles
 *
 * Exports common sx prop patterns used across components.
 * Centralized here to reduce duplication and ensure consistency.
 * Each function takes a theme and returns an SxProps<Theme> object.
 */

import { SxProps, Theme } from '@mui/material/styles'
import { tokens } from './tokens'

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
        boxShadow: theme.shadows[3],
      },
    } as SxProps<Theme>,

    /**
     * Grid container for wrapping card layouts.
     * Responsive gap and flex-wrap for reflow.
     */
    gridContainer: {
      display: 'flex',
      flexWrap: 'wrap',
      gap: tokens.spacing.numericLg,
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

export type CommonStyles = ReturnType<typeof createCommonStyles>
