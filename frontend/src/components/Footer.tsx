import { Box, Container, Link as MuiLink, Stack, Typography } from '@mui/material'
import { siFacebook, siInstagram, siTiktok, siYoutube } from 'simple-icons'
import { Link as RouterLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

const FOOTER_NAV_LINKS = [
  { labelKey: 'footer.nav.home', to: '/' },
  { labelKey: 'footer.nav.series', to: '/series' },
  { labelKey: 'footer.nav.events', to: '/events' },
] as const

type SocialIcon = {
  path: string
}

const SOCIAL_LINKS = [
  { label: 'Facebook', href: 'https://www.facebook.com/VIERNULVIER.gent/', icon: siFacebook },
  { label: 'Instagram', href: 'https://www.instagram.com/viernulvier.gent/', icon: siInstagram },
  { label: 'TikTok', href: 'https://www.tiktok.com/@viernulvier.gent', icon: siTiktok },
  {
    label: 'YouTube',
    href: 'https://www.youtube.com/channel/UCdRYlqUQcIm6pbLgHHobQcQ',
    icon: siYoutube,
  },
  { label: 'LinkedIn', href: 'https://www.linkedin.com/company/viernulviergent', icon: null },
] as const

const BrandIcon = ({ icon, size = 18 }: { icon: SocialIcon | null; size?: number }) =>
  icon ? (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="currentColor"
      width={size}
      height={size}
      aria-hidden="true"
    >
      <path d={icon.path} />
    </svg>
  ) : (
    <Box component="span" sx={{ fontWeight: 700, fontSize: '0.82rem', lineHeight: 1 }}>
      in
    </Box>
  )

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
      }}
    >
      <Container maxWidth="xl" sx={{ px: { xs: 2, sm: 3, md: 20 }, py: { xs: 5, md: 6 } }}>
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: {
              xs: '1fr',
              sm: '1fr',
              md: 'repeat(3, minmax(0, 1fr))',
            },
            gap: { xs: 4, sm: 3, md: 4 },
            alignItems: 'start',
          }}
        >
          <Box
            sx={{
              width: '100%',
              display: 'flex',
              justifyContent: 'center',
            }}
          >
            <Stack
              spacing={0.25}
              component="address"
              sx={{
                fontStyle: 'normal',
                width: 'fit-content',
                textAlign: { xs: 'center', md: 'left' },
                alignItems: { xs: 'center', md: 'flex-start' },
              }}
            >
              <Typography variant="body1" sx={{ lineHeight: 1.7, whiteSpace: 'nowrap' }}>
                {t('footer.address.org')}
              </Typography>
              <Typography variant="body1" sx={{ lineHeight: 1.7, whiteSpace: 'nowrap' }}>
                {t('footer.address.street')}
              </Typography>
              <Typography variant="body1" sx={{ lineHeight: 1.7, whiteSpace: 'nowrap' }}>
                {t('footer.address.city')}
              </Typography>
              <MuiLink
                href={`tel:${phone.replace(/[^+\d]/g, '')}`}
                color="inherit"
                underline="none"
                sx={{
                  width: 'fit-content',
                  lineHeight: 1.7,
                  whiteSpace: 'nowrap',
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
                  width: 'fit-content',
                  lineHeight: 1.7,
                  whiteSpace: 'nowrap',
                  '&:hover': { opacity: 0.7 },
                }}
              >
                {email}
              </MuiLink>
              <Typography variant="body1" sx={{ lineHeight: 1.7, whiteSpace: 'nowrap' }}>
                {t('footer.address.vat')}
              </Typography>
            </Stack>
          </Box>

          <Box
            sx={{
              width: '100%',
              display: { xs: 'none', md: 'flex' },
              justifyContent: 'center',
            }}
            component="nav"
            aria-label={t('footer.nav.ariaLabel')}
          >
            <Stack
              component="ul"
              spacing={0.6}
              sx={{
                m: 0,
                p: 0,
                listStyle: 'none',
                width: '100%',
                maxWidth: '12rem',
                textAlign: { xs: 'center', md: 'left' },
                alignItems: { xs: 'center', md: 'flex-start' },
              }}
            >
              {FOOTER_NAV_LINKS.map(({ labelKey, to }) => (
                <Box component="li" key={to} sx={{ display: 'flex', justifyContent: 'center' }}>
                  <MuiLink
                    component={RouterLink}
                    to={to}
                    color="inherit"
                    underline="none"
                    sx={{
                      width: '100%',
                      lineHeight: 1.7,
                      whiteSpace: 'nowrap',
                      textAlign: 'center',
                      transition: 'opacity 0.15s ease',
                      '&:hover': { opacity: 0.65 },
                    }}
                  >
                    {t(labelKey)}
                  </MuiLink>
                </Box>
              ))}
            </Stack>
          </Box>

          <Box
            sx={{
              width: '100%',
              display: 'flex',
              justifyContent: 'center',
            }}
          >
            <Stack spacing={2} sx={{ alignItems: 'center' }}>
              <Stack direction="row" spacing={1} sx={{ flexWrap: 'nowrap' }}>
                {SOCIAL_LINKS.map(({ label, href, icon }) => (
                  <MuiLink
                    key={label}
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    aria-label={label}
                    underline="none"
                    sx={{
                      display: 'inline-flex',
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
                    <BrandIcon icon={icon} size={18} />
                  </MuiLink>
                ))}
              </Stack>

              <MuiLink
                href="https://www.viernulvier.gent/nl/newsletter-inschrijven-q1lr"
                target="_blank"
                rel="noopener noreferrer"
                underline="none"
                sx={{
                  display: 'inline-block',
                  px: 2.2,
                  py: 1.1,
                  mx: 'auto',
                  border: '1.5px solid #ffffff',
                  borderRadius: '999px',
                  color: '#ffffff',
                  fontSize: '0.8rem',
                  letterSpacing: '0.02em',
                  whiteSpace: 'nowrap',
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
          </Box>
        </Box>
      </Container>
    </Box>
  )
}

export default Footer
