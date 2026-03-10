import {
  AppBar,
  Toolbar,
  Button,
  Stack,
  Box,
  Typography,
  IconButton,
  Container,
} from '@mui/material'
import DarkModeOutlinedIcon from '@mui/icons-material/DarkModeOutlined'
import LightModeOutlinedIcon from '@mui/icons-material/LightModeOutlined'
import { Link as RouterLink, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

const NAV_LINKS = [
  { labelKey: 'nav.home', to: '/' },
  { labelKey: 'nav.events', to: '/series' },
  { labelKey: 'nav.productions', to: '/artists' },
] as const

type NavbarProps = {
  mode: 'light' | 'dark'
  onToggleMode: () => void
}

const Navbar = ({ mode, onToggleMode }: NavbarProps) => {
  const { t, i18n } = useTranslation()
  const location = useLocation()

  // Toggle between the two supported UI languages.
  const switchLanguage = (language: 'en' | 'nl') => {
    i18n.changeLanguage(language)
  }

  // Keep root exact and allow nested detail routes to highlight their parent tab.
  const isActive = (to: string) =>
    to === '/' ? location.pathname === '/' : location.pathname.startsWith(to)

  const activeLinkSx = {
    borderBottom: '2px solid #fff',
    borderRadius: 0,
    pb: '2px',
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
                fontSize: '36px',
                lineHeight: 1,
                transform: 'translateY(4.5px)',
              }}
            >
              / Archive
            </Typography>
          </Box>

          {/* Nav links */}
          <Stack
            direction="row"
            spacing={1}
            alignItems="center"
            component="ul"
            aria-label={t('nav.mainNav', 'Main navigation')}
            sx={{ listStyle: 'none', m: 0, p: 0 }}
          >
            {NAV_LINKS.map(({ labelKey, to }) => (
              <Box component="li" key={to}>
                <Button
                  color="inherit"
                  component={RouterLink}
                  to={to}
                  aria-current={isActive(to) ? 'page' : undefined}
                  sx={{
                    textTransform: 'none',
                    fontSize: '1.05rem',
                    letterSpacing: '0.02em',
                    ...(isActive(to) ? activeLinkSx : {}),
                    '&:hover': { bgcolor: 'rgba(255,255,255,0.08)' },
                  }}
                >
                  {t(labelKey)}
                </Button>
              </Box>
            ))}

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
                aria-label={mode === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
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
                    width: 30,
                    height: 30,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
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
                    width: 30,
                    height: 30,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
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
                color="inherit"
                // Single toggle button: switch to the other available language.
                onClick={() => switchLanguage(i18n.language === 'en' ? 'nl' : 'en')}
                aria-label={`Switch language to ${i18n.language === 'en' ? 'Dutch' : 'English'}`}
                sx={{
                  minWidth: 'auto',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  fontWeight: 700,
                  fontSize: '0.95rem',
                }}
              >
                {i18n.language === 'en' ? 'EN' : 'NL'}
              </Button>
            </Box>
          </Stack>
        </Toolbar>
      </Container>
    </AppBar>
  )
}

export default Navbar
