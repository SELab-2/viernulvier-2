import { AppBar, Toolbar, Button, Stack, Box, Typography } from '@mui/material'
import { Link as RouterLink, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

const NAV_LINKS = [
  { labelKey: 'nav.home', to: '/' },
  { labelKey: 'nav.events', to: '/events' },
  { labelKey: 'nav.productions', to: '/productions' },
] as const

const Navbar = () => {
  const { t, i18n } = useTranslation()
  const location = useLocation()

  const switchLanguage = (language: 'en' | 'nl') => {
    i18n.changeLanguage(language)
  }

/**
 * Checks if the current route matches the given route.
 *
 * @param {string} to - The route to check.
 *
 * @returns {boolean} - True if the current route matches the given route, false otherwise.
 */
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
      <Toolbar sx={{ minHeight: 64 }}>
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
                  fontSize: '0.95rem',
                  letterSpacing: '0.02em',
                  ...(isActive(to) ? activeLinkSx : {}),
                  '&:hover': { bgcolor: 'rgba(255,255,255,0.08)' },
                }}
              >
                {t(labelKey)}
              </Button>
            </Box>
          ))}

          {/* Language switcher */}
          <Box
            component="li"
            sx={{ borderLeft: '1px solid rgba(255,255,255,0.25)', pl: 2, ml: 1 }}
            role="group"
            aria-label={t('nav.languageSwitcher', 'Language')}
          >
            {(['en', 'nl'] as const).map((lang) => (
              <Button
                key={lang}
                size="small"
                color="inherit"
                onClick={() => switchLanguage(lang)}
                aria-pressed={i18n.language === lang}
                sx={{
                  minWidth: 'auto',
                  fontWeight: i18n.language === lang ? 700 : 400,
                  opacity: i18n.language === lang ? 1 : 0.6,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}
              >
                {lang}
              </Button>
            ))}
          </Box>
        </Stack>
      </Toolbar>
    </AppBar>
  )
}

export default Navbar
