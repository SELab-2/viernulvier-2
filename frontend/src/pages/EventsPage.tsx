import { Container, Typography, Paper, Stack, Link as MuiLink } from '@mui/material'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

const EventsPage = () => {
    const { t } = useTranslation()

    return (
        <Container maxWidth="lg" sx={{ py: 4 }}>
            <Stack spacing={3}>
                <Typography variant="h4" component="h1">
                    {t('events.title')}
                </Typography>
                <Paper elevation={2} sx={{ p: 3 }}>
                    <Typography variant="body1" gutterBottom>
                        {t('events.listPlaceholder')}
                    </Typography>
                    <Typography variant="body2" sx={{ mt: 2 }}>
                        Example:{' '}
                        <MuiLink component={Link} to="/events/123" underline="hover">
                            View Event #123
                        </MuiLink>
                    </Typography>
                </Paper>
            </Stack>
        </Container>
    )
}

export default EventsPage
