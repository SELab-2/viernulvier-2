import {
  AppBar,
  Toolbar,
  Button,
  Stack,
  Box,
  Typography,
  IconButton,
  Container,
  Collapse,
  ClickAwayListener,
} from '@mui/material'
import DarkModeOutlinedIcon from '@mui/icons-material/DarkModeOutlined'
import LightModeOutlinedIcon from '@mui/icons-material/LightModeOutlined'
import MenuIcon from '@mui/icons-material/Menu'
import CloseIcon from '@mui/icons-material/Close'
import { useState } from 'react'
import { Link as RouterLink, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

const NAV_LINKS = [
  { labelKey: 'nav.home', to: '/' },
  { labelKey: 'nav.events', to: '/series' },
  { labelKey: 'nav.productions', to: '/artists' },
] as const

type SupportedLanguage = 'en' | 'nl'

type NavbarProps = {
  mode: 'light' | 'dark'
  onToggleMode: () => void
}

// Sticky navbar with responsive desktop/mobile navigation.
const Navbar = ({ mode, onToggleMode }: NavbarProps) => {
  const { t, i18n } = useTranslation()
  const location = useLocation()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  // Route where the menu was opened; keeps mobile panel route-aware.
  const [menuOpenedAtPath, setMenuOpenedAtPath] = useState<string | null>(null)
  // Menu is open only on the route where it was triggered.
  const isEffectivelyOpen = mobileMenuOpen && menuOpenedAtPath === location.pathname
  const currentLanguage: SupportedLanguage = i18n.language === 'en' ? 'en' : 'nl'
  const nextLanguage: SupportedLanguage = currentLanguage === 'en' ? 'nl' : 'en'
  const themeSwitchLabel = mode === 'dark' ? t('nav.switchToLightMode') : t('nav.switchToDarkMode')

  // Switch active UI language.
  const switchLanguage = (language: SupportedLanguage) => {
    i18n.changeLanguage(language)
  }

  // Home route is exact; others use prefix match for nested pages.
  const isActive = (to: string) =>
    to === '/' ? location.pathname === '/' : location.pathname.startsWith(to)

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

  const activeLinkSx = {
    fontWeight: 700,
  }

  const baseListSx = { listStyle: 'none', m: 0, p: 0 }

  return (
    <AppBar
      position="sticky"
      component="nav"
      sx={{ bgcolor: '#000', boxShadow: '0 1px 0 rgba(255,255,255,0.1)' }}
    >
      <ClickAwayListener onClickAway={closeMobileMenu}>
        <Container maxWidth="xl" sx={{ px: { xs: 2, sm: 3, md: 20 } }}>
          <Toolbar disableGutters sx={{ minHeight: 64 }}>
            {/* Brand: logo + "/ Archive" */}
            <Box
              component={RouterLink}
              to="/"
              sx={{
                flexGrow: 1,
                display: 'flex',
                alignItems: 'center',
                gap: 1.5,
                textDecoration: 'none',
                whiteSpace: 'nowrap',
              }}
            >
              <Box
                component="img"
                src="/vnv_logo.png"
                alt="Viernulvier logo"
                sx={{
                  height: { xs: 32, sm: 36 },
                  width: 'auto',
                  display: 'block',
                  filter: 'brightness(0) invert(1)',
                }}
              />
              <Typography
                variant="subtitle1"
                sx={{
                  display: { xs: 'none', sm: 'block' },
                  color: '#fff',
                  fontWeight: 400,
                  letterSpacing: '0.03em',
                  fontSize: '24px',
                  lineHeight: 1,
                  transform: 'translateY(4.5px)',
                }}
              >
                / Archive
              </Typography>
            </Box>

            {/* Main page links only stay inline on large screens; below lg they move to the dropdown. */}
            <Stack
              direction="row"
              spacing={1}
              alignItems="center"
              component="ul"
              aria-label={t('nav.mainNav', 'Main navigation')}
              sx={{ ...baseListSx, display: { xs: 'none', lg: 'flex' } }}
            >
              {NAV_LINKS.map(({ labelKey, to }) => (
                <Box component="li" key={to}>
                  <Button
                    color="inherit"
                    component={RouterLink}
                    to={to}
                    aria-current={isActive(to) ? 'page' : undefined}
                    disableRipple
                    sx={{
                      textTransform: 'none',
                      fontSize: '1.05rem',
                      letterSpacing: '0.02em',
                      ...(isActive(to) ? activeLinkSx : {}),
                      '&:hover': { bgcolor: 'transparent' },
                    }}
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
              alignItems="center"
              component="ul"
              sx={{ ...baseListSx, display: 'flex' }}
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
                  {mode === 'dark' ? (
                    <DarkModeOutlinedIcon
                      sx={{
                        fontSize: { xs: '1.15rem', sm: '1.5rem' },
                        color: '#fff',
                        transition: 'color 0.2s',
                      }}
                    />
                  ) : (
                    <LightModeOutlinedIcon
                      sx={{
                        fontSize: { xs: '1.15rem', sm: '1.5rem' },
                        color: '#fff',
                        transition: 'color 0.2s',
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
                  {currentLanguage === 'en' ? 'EN' : 'NL'}
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
                      component={RouterLink}
                      to={to}
                      aria-current={isActive(to) ? 'page' : undefined}
                      onClick={closeMobileMenu}
                      disableRipple
                      sx={{
                        justifyContent: 'flex-start',
                        textTransform: 'none',
                        fontSize: '1.05rem',
                        letterSpacing: '0.02em',
                        ...(isActive(to) ? activeLinkSx : {}),
                        '&:hover': { bgcolor: 'transparent' },
                      }}
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
