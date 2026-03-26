import { Box, Container, Link as MuiLink, Stack, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Link as RouterLink } from 'react-router-dom'
import { siFacebook, siInstagram, siTiktok, siYoutube } from 'simple-icons'

const FOOTER_NAV_LINKS = [
  { labelKey: 'footer.nav.home', to: '/' },
  { labelKey: 'footer.nav.series', to: '/series' },
  { labelKey: 'footer.nav.events', to: '/events' },
] as const

const siLinkedIn = {
  path: 'M0 1.146C0 .513.526 0 1.175 0h13.65C15.474 0 16 .513 16 1.146v13.708c0 .633-.526 1.146-1.175 1.146H1.175C.526 16 0 15.487 0 14.854zm4.943 12.248V6.169H2.542v7.225zm-1.2-8.212c.837 0 1.358-.554 1.358-1.248-.015-.709-.52-1.248-1.342-1.248S2.4 3.226 2.4 3.934c0 .694.521 1.248 1.327 1.248zm4.908 8.212V9.359c0-.216.016-.432.08-.586.173-.431.568-.878 1.232-.878.869 0 1.216.662 1.216 1.634v3.865h2.401V9.25c0-2.22-1.184-3.252-2.764-3.252-1.274 0-1.845.7-2.165 1.193v.025h-.016l.016-.025V6.169h-2.4c.03.678 0 7.225 0 7.225z',
}

type SocialLink = {
  label: string
  href: string
  icon: { path: string }
  viewBox?: string
}

const SOCIAL_LINKS: ReadonlyArray<SocialLink> = [
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

const Footer = () => {
  const { t } = useTranslation()

  const email = t('footer.address.email')
  const phone = t('footer.address.phone')

  return (
    <Box
      component="footer"
      sx={{
        bgcolor: '#111111',
        color: '#ffffff',
        borderTop: '1px solid rgba(255,255,255,0.12)',
        mt: 6,
        fontStyle: 'normal',
        lineHeight: 1.7,
        whiteSpace: 'nowrap',
      }}
    >
      <Container
        maxWidth="xl"
        sx={{
          display: 'flex',
          flexDirection: { xs: 'column', md: 'row' },
          justifyContent: 'center',
          alignItems: { xs: 'center', md: 'flex-start' },
          textAlign: { xs: 'center', md: 'left' },
          lineHeight: 1.7,
          whiteSpace: 'nowrap',
          rowGap: 6,
          columnGap: 12,
          p: 6,
        }}
      >
        <Stack
          spacing={0.25}
          component="address"
          sx={{
            fontStyle: 'normal',
          }}
        >
          <Typography variant="body1">{t('footer.address.org')}</Typography>
          <Typography variant="body1">{t('footer.address.street')}</Typography>
          <Typography variant="body1">{t('footer.address.city')}</Typography>
          <MuiLink
            href={`tel:${phone.replace(/[^+\d]/g, '')}`}
            color="inherit"
            underline="none"
            sx={{
              '&:hover': { opacity: 0.7 },
            }}
          >
            {phone}
          </MuiLink>
          <MuiLink
            href={`mailto:${email}`}
            color="inherit"
            underline="none"
            sx={{
              '&:hover': { opacity: 0.7 },
            }}
          >
            {email}
          </MuiLink>
          <Typography variant="body1">{t('footer.address.vat')}</Typography>
        </Stack>

        <Stack spacing={0.6}>
          {FOOTER_NAV_LINKS.map(({ labelKey, to }) => (
            <MuiLink
              key={to}
              component={RouterLink}
              to={to}
              color="inherit"
              underline="none"
              sx={{
                transition: 'opacity 0.15s ease',
                '&:hover': { opacity: 0.7 },
              }}
            >
              {t(labelKey)}
            </MuiLink>
          ))}
        </Stack>

        <Stack spacing={2} sx={{ alignItems: 'center' }}>
          <Stack direction="row" spacing={1}>
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
                  borderRadius: '999px',
                  bgcolor: '#000000',
                  color: '#ffffff',
                  transition: 'background-color 0.15s ease',
                  '&:hover': { bgcolor: '#333333' },
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

          <MuiLink
            href="https://www.viernulvier.gent/nl/newsletter-inschrijven-q1lr"
            target="_blank"
            rel="noopener noreferrer"
            underline="none"
            sx={{
              px: 2,
              py: 1,
              width: 'fit-content',
              border: '1.5px solid #ffffff',
              borderRadius: '999px',
              color: '#ffffff',
              fontSize: '0.8rem',
              letterSpacing: '0.02em',
              transition: 'background-color 0.15s ease, color 0.15s ease',
              '&:hover': {
                bgcolor: '#ffffff',
                color: '#111111',
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
