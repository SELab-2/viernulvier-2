import { Container, Paper, Stack, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'

const HomePage = () => {
    const { t } = useTranslation()

    return (
        <Container maxWidth="md" sx={{ py: 6 }}>
            <Paper elevation={3} sx={{ p: 4 }}>
                <Stack spacing={3}>
                    <Typography variant="h3" component="h1">
                        {t('title')}
                    </Typography>
                    <Typography variant="subtitle1">{t('subtitle')}</Typography>
                </Stack>
            </Paper>
        </Container>
    )
}

export default HomePage
