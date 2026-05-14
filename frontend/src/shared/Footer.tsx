/**
 * Application footer component.
 *
 * This is a layout-level UI component responsible for rendering the global site footer.
 * It is used across all pages and contains:
 * - Organization contact details (address, phone, email)
 * - Localized navigation links that mirror the main site structure
 * - Social media icon links
 * - Newsletter subscription call-to-action
 *
 * The footer is language-aware and derives the active language from the current route,
 * ensuring all internal navigation links are correctly localized.
 *
 * It does NOT manage state or business logic; it only formats and displays data.
 * All localization is handled via i18n + route utilities.
 */

import { Box, Container, Link as MuiLink, Stack, Typography, useTheme } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Link as RouterLink, useLocation } from 'react-router-dom'
import { siFacebook, siInstagram, siTiktok, siYoutube } from 'simple-icons'

import { createCommonStyles } from '../theme/styles'
import { tokens } from '../theme/tokens'
import { resolveCurrentLanguage, toLocalizedPath } from '../utils/localizedRoutes'

/**
 * Internal navigation links shown in the footer.
 *
 * These mirror the main navigation structure and are translated using i18n keys.
 * The `to` value is always a canonical route and is later localized dynamically.
 */
const FOOTER_NAV_LINKS = [
  { labelKey: 'footer.nav.home', to: '/' },
  { labelKey: 'footer.nav.archive', to: '/archive' },
  { labelKey: 'footer.nav.series', to: '/series' },
  { labelKey: 'footer.nav.blogs', to: '/blogs' },
  { labelKey: 'footer.nav.media', to: '/media' },
] as const

/**
 * Custom LinkedIn icon definition using SVG path data.
 *
 * This is used because the Simple Icons package does not expose LinkedIn
 * in a format consistent with the rest of the imported icons.
 */
const siLinkedIn = {
  path: 'M0 1.146C0 .513.526 0 1.175 0h13.65C15.474 0 16 .513 16 1.146v13.708c0 .633-.526 1.146-1.175 1.146H1.175C.526 16 0 15.487 0 14.854zm4.943 12.248V6.169H2.542v7.225zm-1.2-8.212c.837 0 1.358-.554 1.358-1.248-.015-.709-.52-1.248-1.342-1.248S2.4 3.226 2.4 3.934c0 .694.521 1.248 1.327 1.248zm4.908 8.212V9.359c0-.216.016-.432.08-.586.173-.431.568-.878 1.232-.878.869 0 1.216.662 1.216 1.634v3.865h2.401V9.25c0-2.22-1.184-3.252-2.764-3.252-1.274 0-1.845.7-2.165 1.193v.025h-.016l.016-.025V6.169h-2.4c.03.678 0 7.225 0 7.225z',
}

/**
 * Social link model used for rendering icon buttons.
 *
 * Each item represents an external social platform with:
 * - label: accessibility + aria label
 * - href: external URL
 * - icon: SVG path data (Simple Icons)
 * - viewBox: optional override for consistent scaling
 */
type SocialLink = {
  label: string
  href: string
  icon: { path: string }
  viewBox?: string
}

/**
 * List of social media links rendered in the footer.
 *
 * These are external links and open in a new tab.
 * Icons are rendered as inline SVGs for full styling control.
 */
const SOCIAL_LINKS: readonly SocialLink[] = [
  { label: 'Facebook', href: 'https://www.facebook.com/VIERNULVIER.gent/', icon: siFacebook },
  { label: 'Instagram', href: 'https://www.instagram.com/viernulvier.gent/', icon: siInstagram },
  { label: 'TikTok', href: 'https://www.tiktok.com/@viernulvier.gent', icon: siTiktok },
  {
    label: 'YouTube',
    href: 'https://www.youtube.com/channel/UCdRYlqUQcIm6pbLgHHobQcQ',
    icon: siYoutube,
  },
  {
    label: 'LinkedIn',
    href: 'https://www.linkedin.com/company/viernulviergent',
    icon: siLinkedIn,
    viewBox: '0 0 16 16',
  },
]

/**
 * Footer component (global layout element).
 */
const Footer = () => {
  const theme = useTheme()
  const commonStyles = createCommonStyles(theme)
  const { t, i18n } = useTranslation()
  const location = useLocation()

  /**
   * Active UI language derived from current URL + i18n state.
   * This ensures footer links always match the current localized route context.
   */
  const currentLanguage = resolveCurrentLanguage(
    location.pathname,
    i18n.language,
    i18n.resolvedLanguage,
  )

  const email = t('footer.address.email')
  const phone = t('footer.address.phone')

  /**
   * Helper that converts a canonical route into a localized route.
   */
  const localizedPath = (path: string) => toLocalizedPath(path, currentLanguage)

  return (
    <Box component="footer" sx={commonStyles.footer}>
      <Container
        maxWidth="xl"
        sx={{
          display: 'flex',
          flexDirection: { xs: 'column', md: 'row' },
          justifyContent: 'center',
          alignItems: { xs: 'center', md: 'flex-start' },
          textAlign: { xs: 'center', md: 'left' },
          lineHeight: tokens.typography.lineHeights.relaxed,
          whiteSpace: 'nowrap',
          rowGap: tokens.spacing.numericLg,
          columnGap: tokens.spacing.numeric2xl,
          p: tokens.spacing.numericXl,
        }}
      >
        {/* CONTACT SECTION */}

        <Stack spacing={0.25} component="address" sx={{ fontStyle: 'normal' }}>
          <Typography variant="body1">{t('footer.address.org')}</Typography>
          <Typography variant="body1">{t('footer.address.street')}</Typography>
          <Typography variant="body1">{t('footer.address.city')}</Typography>

          {/* Phone link (click-to-call) */}
          <MuiLink
            href={`tel:${phone.replace(/[^+\d]/g, '')}`}
            color="inherit"
            underline="none"
            sx={commonStyles.linkHover}
          >
            {phone}
          </MuiLink>

          {/* Email link */}
          <MuiLink
            href={`mailto:${email}`}
            color="inherit"
            underline="none"
            sx={commonStyles.linkHover}
          >
            {email}
          </MuiLink>

          <Typography variant="body1">{t('footer.address.vat')}</Typography>
        </Stack>

        {/* NAVIGATION SECTION */}

        <Stack spacing={0.6}>
          {FOOTER_NAV_LINKS.map(({ labelKey, to }) => (
            <MuiLink
              key={to}
              component={RouterLink}
              to={localizedPath(to)}
              color="inherit"
              underline="none"
              sx={commonStyles.linkHover}
            >
              {t(labelKey)}
            </MuiLink>
          ))}
        </Stack>

        {/* SOCIAL + CTA SECTION */}

        <Stack spacing={tokens.spacing.numericMd} sx={{ alignItems: 'center' }}>
          {/* Social icons row */}
          <Stack direction="row" spacing={tokens.spacing.numericSm}>
            {SOCIAL_LINKS.map(({ label, href, icon, viewBox }) => (
              <MuiLink
                key={label}
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                aria-label={label}
                underline="none"
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: 36,
                  height: 36,
                  borderRadius: tokens.borderRadius.full,
                  bgcolor: tokens.colors.neutral.black,
                  color: tokens.colors.neutral.white,
                  transition: tokens.transitions.fast,
                  '&:hover': { bgcolor: tokens.colors.neutral.gray600 },
                }}
              >
                <Box
                  component="svg"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox={viewBox ?? '0 0 24 24'}
                  fill="currentColor"
                  width={18}
                  height={18}
                  aria-hidden="true"
                  sx={{ display: 'block' }}
                >
                  <path d={icon.path} />
                </Box>
              </MuiLink>
            ))}
          </Stack>

          {/* Newsletter CTA */}
          <MuiLink
            href="https://www.viernulvier.gent/nl/newsletter-inschrijven-q1lr"
            target="_blank"
            rel="noopener noreferrer"
            underline="none"
            sx={{
              px: tokens.spacing.numericMd,
              py: tokens.spacing.numericSm,
              width: 'fit-content',
              border: `1.5px solid ${tokens.colors.neutral.white}`,
              borderRadius: tokens.borderRadius.full,
              color: tokens.colors.neutral.white,
              fontSize: tokens.typography.sizes.sm,
              letterSpacing: '0.02em',
              transition: tokens.transitions.fast,
              '&:hover': {
                bgcolor: tokens.colors.neutral.white,
                color: tokens.colors.neutral.gray900,
              },
            }}
          >
            {t('footer.newsletter.cta')}
          </MuiLink>
        </Stack>
      </Container>
    </Box>
  )
}

export default Footer
