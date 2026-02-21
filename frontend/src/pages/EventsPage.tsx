import { Container, Typography, Paper, Stack } from '@mui/material'
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
                    <Typography variant="body1">{t('events.listPlaceholder')}</Typography>
                </Paper>
            </Stack>
        </Container>
    )
}

export default EventsPage
