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
  // Menu is open only on the route where it was triggered.
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

  // Switch active UI language by swapping the URL language segment.
  const switchLanguage = (language: SupportedLanguage) => {
    const targetPath = `${toLocalizedPath(location.pathname, language)}${location.search}${location.hash}`
    navigate(targetPath)
  }

  // Home route is exact; archive also covers compatibility production URLs.
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

  // Close mobile menu and clear route marker.
  const closeMobileMenu = () => {
    setMobileMenuOpen(false)
    setMenuOpenedAtPath(null)
  }

  // Toggle menu and store current path when opening.
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

  useEffect(() => {
    const toolbar = toolbarRef.current
    if (!toolbar) {
      return
    }

    const updateNavbarHeightVar = () => {
      const measuredHeight = Math.ceil(toolbar.getBoundingClientRect().height)

      // Avoid writing unusable values (e.g., 0 in jsdom/hidden states) so CSS fallback remains valid.
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
          <Toolbar
            ref={toolbarRef}
            disableGutters
            sx={{
              minHeight: tokens.navbar.minHeight,
            }}
          >
            {/* Brand: Archive logo */}
            <Box component={Link} to={localizedPath('/')} sx={navbarStyles.brandLink}>
              <Box
                component="img"
                src="/vnv_archive_logo.png"
                alt="Viernulvier logo"
                sx={navbarStyles.brandLogo}
              />
            </Box>

            {/* Main page links only stay inline on large screens; below lg they move to the dropdown. */}
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

            {/* Theme/language controls remain visible longer and only move into menu on xs. */}
            <Stack
              direction="row"
              spacing={0}
              component="ul"
              sx={{ ...baseListSx, display: 'flex', alignItems: 'center' }}
            >
              {/* Theme toggle */}
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
                  sx={{
                    p: { xs: '2px 4px', sm: '4px 6px' },
                    backgroundColor: 'transparent',
                  }}
                >
                  {mode === DarkMode ? (
                    <DarkModeOutlinedIcon
                      sx={{
                        fontSize: { xs: '1.15rem', sm: '1.5rem' },
                        color: theme.palette.primary.light,
                        transition: tokens.transitions.fast,
                      }}
                    />
                  ) : (
                    <LightModeOutlinedIcon
                      sx={{
                        fontSize: { xs: '1.15rem', sm: '1.5rem' },
                        color: theme.palette.primary.contrastText,
                        transition: tokens.transitions.fast,
                      }}
                    />
                  )}
                </IconButton>
              </Box>

              {/* Language switcher */}
              <Box component="li" sx={{ pl: { xs: 1, sm: 2 }, ml: { xs: 0.5, sm: 1 } }}>
                <Button
                  size="small"
                  data-testid="language-toggle-inline"
                  color="inherit"
                  // Single toggle button: switch to the other available language.
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

            {/* Burger button is shown whenever inline nav links are hidden (< lg). */}
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

          {/* Mobile nav panel slides down below navbar and matches container width. */}
          <Box>
            <Collapse
              in={isEffectivelyOpen}
              timeout="auto"
              unmountOnExit
              data-testid="mobile-nav-panel"
              sx={{ display: { xs: 'block', lg: 'none' } }}
            >
              <Stack
                component="ul"
                spacing={0.5}
                sx={{
                  ...baseListSx,
                  py: 1,
                }}
              >
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
