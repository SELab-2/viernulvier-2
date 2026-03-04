import { AppBar, Toolbar, Typography, Button, Stack, Box } from '@mui/material'
import { Link as RouterLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

const Navbar = () => {
    const { t, i18n } = useTranslation()

    const switchLanguage = (language: 'en' | 'nl') => {
        i18n.changeLanguage(language)
    }

    return (
        <AppBar position="static">
            <Toolbar>
                <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                    Archive
                </Typography>
                <Stack direction="row" spacing={2} alignItems="center">
                    <Button color="inherit" component={RouterLink} to="/">
                        {t('nav.home')}
                    </Button>
                    <Button color="inherit" component={RouterLink} to="/events">
                        {t('nav.events')}
                    </Button>
                    <Button color="inherit" component={RouterLink} to="/productions">
                        {t('nav.productions')}
                    </Button>
                    <Box sx={{ borderLeft: '1px solid rgba(255,255,255,0.3)', pl: 2, ml: 1 }}>
                        <Button
                            size="small"
                            color="inherit"
                            onClick={() => switchLanguage('en')}
                            sx={{ minWidth: 'auto' }}
                        >
                            EN
                        </Button>
                        <Button
                            size="small"
                            color="inherit"
                            onClick={() => switchLanguage('nl')}
                            sx={{ minWidth: 'auto' }}
                        >
                            NL
                        </Button>
                    </Box>
                </Stack>
            </Toolbar>
        </AppBar>
    )
}

export default Navbar
