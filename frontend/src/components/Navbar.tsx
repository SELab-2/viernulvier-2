import {
  AppBar,
  Toolbar,
  Button,
  Stack,
  Box,
  Typography,
  IconButton,
  Container,
  Menu,
  MenuItem,
} from '@mui/material'
import DarkModeOutlinedIcon from '@mui/icons-material/DarkModeOutlined'
import LightModeOutlinedIcon from '@mui/icons-material/LightModeOutlined'
import MenuIcon from '@mui/icons-material/Menu'
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

const Navbar = ({ mode, onToggleMode }: NavbarProps) => {
  const { t, i18n } = useTranslation()
  const location = useLocation()
  // Anchor element for the hamburger dropdown menu on smaller breakpoints.
  const [mobileMenuAnchor, setMobileMenuAnchor] = useState<null | HTMLElement>(null)
  const currentLanguage: SupportedLanguage = i18n.language === 'en' ? 'en' : 'nl'
  const nextLanguage: SupportedLanguage = currentLanguage === 'en' ? 'nl' : 'en'
  const themeSwitchLabel = mode === 'dark' ? t('nav.switchToLightMode') : t('nav.switchToDarkMode')

  // Toggle between the two supported UI languages.
  const switchLanguage = (language: SupportedLanguage) => {
    i18n.changeLanguage(language)
  }

  // Keep root exact and allow nested detail routes to highlight their parent tab.
  const isActive = (to: string) =>
    to === '/' ? location.pathname === '/' : location.pathname.startsWith(to)

  const closeMobileMenu = () => {
    setMobileMenuAnchor(null)
  }

  const activeLinkSx = {
    fontWeight: 700,
  }

  const baseListSx = { listStyle: 'none', m: 0, p: 0 }

  const themeSquareBaseSx = {
    width: 30,
    height: 30,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  }

  return (
    <AppBar
      position="sticky"
      component="nav"
      sx={{ bgcolor: '#000', boxShadow: '0 1px 0 rgba(255,255,255,0.1)' }}
    >
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
                height: 36,
                width: 'auto',
                display: 'block',
                filter: 'brightness(0) invert(1)',
              }}
            />
            <Typography
              variant="subtitle1"
              sx={{
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
            sx={{ ...baseListSx, display: { xs: 'none', sm: 'flex' } }}
          >
            {/* Theme toggle */}
            <Box
              component="li"
              sx={{
                pl: 2,
                ml: 1,
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
                  display: 'flex',
                  alignItems: 'center',
                  p: '4px',
                  borderRadius: '4px',
                  backgroundColor: 'transparent',
                  gap: 0,
                }}
              >
                {/* Left square represents dark mode; active mode is rendered in white. */}
                <Box
                  sx={{
                    ...themeSquareBaseSx,
                    backgroundColor: mode === 'dark' ? '#fff' : '#d9d9d9',
                  }}
                >
                  <DarkModeOutlinedIcon
                    fontSize="medium"
                    sx={{
                      color: '#111',
                      transition: 'color 0.2s, background-color 0.2s',
                    }}
                  />
                </Box>
                {/* Right square represents light mode; active mode is rendered in white. */}
                <Box
                  sx={{
                    ...themeSquareBaseSx,
                    backgroundColor: mode === 'light' ? '#fff' : '#d9d9d9',
                  }}
                >
                  <LightModeOutlinedIcon
                    fontSize="medium"
                    sx={{
                      color: '#111',
                      transition: 'color 0.2s, background-color 0.2s',
                    }}
                  />
                </Box>
              </IconButton>
            </Box>

            {/* Language switcher */}
            <Box component="li" sx={{ pl: 2, ml: 1 }}>
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
                  fontWeight: 700,
                  fontSize: '0.95rem',
                }}
              >
                {currentLanguage === 'en' ? 'EN' : 'NL'}
              </Button>
            </Box>
          </Stack>

          {/* Burger dropdown menu is shown whenever inline nav links are hidden (< lg). */}
          <IconButton
            color="inherit"
            data-testid="mobile-menu-trigger"
            aria-label={t('nav.openMenu')}
            onClick={(event) => setMobileMenuAnchor(event.currentTarget)}
            sx={{ display: { xs: 'inline-flex', lg: 'none' }, ml: 2 }}
          >
            <MenuIcon />
          </IconButton>
          <Menu
            anchorEl={mobileMenuAnchor}
            open={Boolean(mobileMenuAnchor)}
            onClose={closeMobileMenu}
            sx={{ display: { xs: 'block', lg: 'none' } }}
          >
            {NAV_LINKS.map(({ labelKey, to }) => (
              <MenuItem
                key={to}
                component={RouterLink}
                to={to}
                selected={isActive(to)}
                onClick={closeMobileMenu}
              >
                {t(labelKey)}
              </MenuItem>
            ))}
            {/* Theme option is only shown in dropdown on xs (hidden on sm+ where inline switch exists). */}
            <MenuItem
              data-testid="theme-toggle-menu"
              sx={{ display: { xs: 'flex', sm: 'none' } }}
              aria-label={themeSwitchLabel}
              onClick={() => {
                onToggleMode()
                closeMobileMenu()
              }}
            >
              <Box sx={{ display: 'inline-flex', alignItems: 'center', lineHeight: 0 }}>
                {mode === 'dark' ? (
                  <DarkModeOutlinedIcon fontSize="small" sx={{ color: '#fff' }} />
                ) : (
                  <LightModeOutlinedIcon fontSize="small" sx={{ color: '#111' }} />
                )}
              </Box>
            </MenuItem>
            {/* Language option is only shown in dropdown on xs (hidden on sm+ where inline switch exists). */}
            <MenuItem
              data-testid="language-toggle-menu"
              sx={{ display: { xs: 'flex', sm: 'none' } }}
              onClick={() => {
                switchLanguage(nextLanguage)
                closeMobileMenu()
              }}
            >
              {currentLanguage === 'en' ? 'EN' : 'NL'}
            </MenuItem>
          </Menu>
        </Toolbar>
      </Container>
    </AppBar>
  )
}

export default Navbar
