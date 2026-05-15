/**
 * Responsive navigation bar component.
 *
 * This component renders the main application navbar, including:
 * - Primary navigation links (desktop + mobile)
 * - Language switching based on localized routes
 * - Theme mode toggle (light/dark)
 * - Responsive mobile menu with collapse behavior
 *
 * It also synchronizes route-based language detection and ensures that
 * navigation paths are always correctly localized.
 */

import CloseIcon from '@mui/icons-material/Close'
import DarkModeOutlinedIcon from '@mui/icons-material/DarkModeOutlined'
import LightModeOutlinedIcon from '@mui/icons-material/LightModeOutlined'
import MenuIcon from '@mui/icons-material/Menu'
import {
  AppBar,
  Toolbar,
  Button,
  Stack,
  Box,
  IconButton,
  Container,
  Collapse,
  ClickAwayListener,
  useTheme,
} from '@mui/material'
import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useLocation, Link, useNavigate } from 'react-router-dom'

import { createCommonStyles, createNavbarStyles } from '../theme/styles'
import { tokens } from '../theme/tokens'
import { DarkMode, type ModeToggleProps } from '../types/Theme'
import {
  resolveCurrentLanguage,
  stripLanguagePrefix,
  toLocalizedPath,
  type SupportedLanguage,
} from '../utils/localizedRoutes'

const NAV_LINKS = [
  { labelKey: 'nav.home', to: '/' },
  { labelKey: 'nav.archive', to: '/archive' },
  { labelKey: 'nav.series', to: '/series' },
  { labelKey: 'nav.blogs', to: '/blogs' },
  { labelKey: 'nav.media', to: '/media' },
] as const

// Sticky navbar with responsive desktop/mobile navigation.
const Navbar = ({ mode, onToggleMode }: ModeToggleProps) => {
  const theme = useTheme()
  const commonStyles = createCommonStyles(theme)
  const navbarStyles = createNavbarStyles()
  const { t, i18n } = useTranslation()
  const location = useLocation()
  const navigate = useNavigate()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const toolbarRef = useRef<HTMLDivElement | null>(null)

  // Route where the menu was opened; keeps mobile panel route-aware.
  const [menuOpenedAtPath, setMenuOpenedAtPath] = useState<string | null>(null)

  // Menu is only considered open for the route where it was triggered.
  const isEffectivelyOpen = mobileMenuOpen && menuOpenedAtPath === location.pathname

  const currentLanguage: SupportedLanguage = resolveCurrentLanguage(
    location.pathname,
    i18n.language,
    i18n.resolvedLanguage,
  )

  const nextLanguage: SupportedLanguage = currentLanguage === 'en' ? 'nl' : 'en'

  const currentPathWithoutLanguage = stripLanguagePrefix(location.pathname)

  const themeSwitchLabel =
    mode === DarkMode ? t('nav.switchToLightMode') : t('nav.switchToDarkMode')

  /**
   * Switches the active UI language by updating the localized URL.
   */
  const switchLanguage = (language: SupportedLanguage) => {
    const targetPath = `${toLocalizedPath(location.pathname, language)}${location.search}${location.hash}`
    navigate(targetPath)
  }

  /**
   * Determines whether a navigation item is active.
   */
  const isActive = (to: string) => {
    if (to === '/') {
      return currentPathWithoutLanguage === '/'
    }

    if (to === '/archive') {
      return (
        currentPathWithoutLanguage.startsWith('/archive') ||
        currentPathWithoutLanguage.startsWith('/productions')
      )
    }

    return currentPathWithoutLanguage.startsWith(to)
  }

  const localizedPath = (path: string) => toLocalizedPath(path, currentLanguage)

  /**
   * Closes the mobile navigation menu and resets route tracking.
   */
  const closeMobileMenu = () => {
    setMobileMenuOpen(false)
    setMenuOpenedAtPath(null)
  }

  /**
   * Toggles mobile menu open/close state.
   */
  const toggleMobileMenu = () => {
    if (isEffectivelyOpen) {
      setMobileMenuOpen(false)
      setMenuOpenedAtPath(null)
    } else {
      setMobileMenuOpen(true)
      setMenuOpenedAtPath(location.pathname)
    }
  }

  const baseListSx = { listStyle: 'none', m: 0, p: 0 }

  /**
   * Keeps CSS variable `--navbar-height` in sync with actual rendered height.
   * Used for layout calculations elsewhere in the app.
   */
  useEffect(() => {
    const toolbar = toolbarRef.current
    if (!toolbar) {
      return
    }

    const updateNavbarHeightVar = () => {
      const measuredHeight = Math.ceil(toolbar.getBoundingClientRect().height)

      if (measuredHeight <= 0) {
        return
      }

      const safeHeight = Math.max(measuredHeight, tokens.navbar.minHeight)
      document.documentElement.style.setProperty('--navbar-height', `${safeHeight}px`)
    }

    updateNavbarHeightVar()

    const supportsResizeObserver = typeof ResizeObserver !== 'undefined'
    const resizeObserver = supportsResizeObserver ? new ResizeObserver(updateNavbarHeightVar) : null

    if (resizeObserver) {
      resizeObserver.observe(toolbar)
    }

    window.addEventListener('resize', updateNavbarHeightVar)

    return () => {
      if (resizeObserver) {
        resizeObserver.disconnect()
      }
      window.removeEventListener('resize', updateNavbarHeightVar)
      document.documentElement.style.removeProperty('--navbar-height')
    }
  }, [])

  return (
    <AppBar position="sticky" component="nav" sx={commonStyles.navbar}>
      <ClickAwayListener onClickAway={closeMobileMenu}>
        <Container maxWidth="xl" sx={{ px: { xs: 2, sm: 3, md: 20 } }}>
          <Toolbar ref={toolbarRef} disableGutters sx={{ minHeight: tokens.navbar.minHeight }}>
            {/* Brand */}
            <Box component={Link} to={localizedPath('/')} sx={navbarStyles.brandLink}>
              <Box
                component="img"
                src="/vnv_archive_logo.png"
                alt="Viernulvier logo"
                sx={navbarStyles.brandLogo}
              />
            </Box>

            {/* Desktop navigation */}
            <Stack
              direction="row"
              spacing={1}
              component="ul"
              aria-label={t('nav.mainNav', 'Main navigation')}
              sx={{ ...baseListSx, display: { xs: 'none', lg: 'flex' }, alignItems: 'center' }}
            >
              {NAV_LINKS.map(({ labelKey, to }) => (
                <Box component="li" key={to}>
                  <Button
                    color="inherit"
                    component={Link}
                    to={localizedPath(to)}
                    aria-current={isActive(to) ? 'page' : undefined}
                    disableRipple
                    sx={[navbarStyles.navLink, ...(isActive(to) ? [navbarStyles.activeLink] : [])]}
                  >
                    {t(labelKey)}
                  </Button>
                </Box>
              ))}
            </Stack>

            {/* Theme + language controls */}
            <Stack
              direction="row"
              spacing={0}
              component="ul"
              sx={{ ...baseListSx, display: 'flex', alignItems: 'center' }}
            >
              <Box
                component="li"
                sx={{
                  pl: { xs: 1, sm: 2 },
                  ml: { xs: 0.5, sm: 1 },
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                <IconButton
                  size="small"
                  data-testid="theme-toggle-inline"
                  aria-label={themeSwitchLabel}
                  disableRipple
                  onClick={onToggleMode}
                  sx={{ p: { xs: '2px 4px', sm: '4px 6px' } }}
                >
                  {mode === DarkMode ? (
                    <DarkModeOutlinedIcon sx={{ fontSize: { xs: '1.15rem', sm: '1.5rem' }, color: theme.palette.primary.light, transition: tokens.transitions.fast, }} />
                  ) : (
                    <LightModeOutlinedIcon sx={{ fontSize: { xs: '1.15rem', sm: '1.5rem' }, color: theme.palette.primary.contrastText, transition: tokens.transitions.fast, }} />
                  )}
                </IconButton>
              </Box>

              <Box component="li" sx={{ pl: { xs: 1, sm: 2 }, ml: { xs: 0.5, sm: 1 } }}>
                <Button
                  size="small"
                  data-testid="language-toggle-inline"
                  color="inherit"
                  onClick={() => switchLanguage(nextLanguage)}
                  aria-label={`Switch language to ${currentLanguage === 'en' ? 'Dutch' : 'English'}`}
                  sx={{
                    minWidth: 'auto',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    fontWeight: 400,
                    fontSize: { xs: '0.85rem', sm: '0.95rem' },
                  }}
                >
                  {nextLanguage.toUpperCase()}
                </Button>
              </Box>
            </Stack>

            {/* Mobile menu button */}
            <IconButton
              color="inherit"
              data-testid="mobile-menu-trigger"
              aria-label={isEffectivelyOpen ? t('nav.closeMenu') : t('nav.openMenu')}
              onClick={toggleMobileMenu}
              sx={{ display: { xs: 'inline-flex', lg: 'none' }, ml: { xs: 1, sm: 2 } }}
            >
              {isEffectivelyOpen ? <CloseIcon /> : <MenuIcon />}
            </IconButton>
          </Toolbar>

          {/* Mobile navigation */}
          <Box>
            <Collapse
              in={isEffectivelyOpen}
              timeout="auto"
              unmountOnExit
              data-testid="mobile-nav-panel"
              sx={{ display: { xs: 'block', lg: 'none' } }}
            >
              <Stack component="ul" spacing={0.5} sx={{ ...baseListSx, py: 1 }}>
                {NAV_LINKS.map(({ labelKey, to }) => (
                  <Box component="li" key={`mobile-${to}`}>
                    <Button
                      fullWidth
                      color="inherit"
                      component={Link}
                      to={localizedPath(to)}
                      aria-current={isActive(to) ? 'page' : undefined}
                      onClick={closeMobileMenu}
                      disableRipple
                      sx={[
                        navbarStyles.navLink,
                        { justifyContent: 'flex-start' },
                        ...(isActive(to) ? [navbarStyles.activeLink] : []),
                      ]}
                    >
                      {t(labelKey)}
                    </Button>
                  </Box>
                ))}
              </Stack>
            </Collapse>
          </Box>
        </Container>
      </ClickAwayListener>
    </AppBar>
  )
}

export default Navbar
