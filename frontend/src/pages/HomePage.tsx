import { Box, Container, Paper, Stack, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { useTheme, useMediaQuery } from '@mui/material'
import SearchControlsBar from '../components/searchbar/SearchControlsBar'
import { useSearchBarUrlState } from '../components/searchbar/useSearchBarUrlState'

// TODO: use the floatingAlerts when needed

const HomePage = () => {
  const { t } = useTranslation()
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const {
    searchValue,
    sortTarget,
    sortDirection,
    viewMode,
    setSearchValue,
    setSortTarget,
    setSortDirection,
    setViewMode,
  } = useSearchBarUrlState({ isMobile })

  return (
    <Box>
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
      <Box
        sx={{
          backgroundColor: theme.palette.mode === 'light' ? '#f8f8f8' : '#1e1e1e',
          pt: 4,
          pb: 6,
          borderBottom: `1px solid ${theme.palette.divider}`,
        }}
      >
        <Box sx={{ width: '75%', mx: 'auto' }}>
          <SearchControlsBar
            placeholder={
              isMobile ? t('searchbar.searchPlaceholderMobile') : t('searchbar.searchPlaceholder')
            }
            searchValue={searchValue}
            onSearchChange={setSearchValue}
            onSearchSubmit={setSearchValue}
            sortTarget={sortTarget}
            onSortTargetChange={setSortTarget}
            sortDirection={sortDirection}
            onSortDirectionChange={setSortDirection}
            viewMode={viewMode}
            onViewModeChange={setViewMode}
            showViewModeToggle={!isMobile}
          />
        </Box>
      </Box>
    </Box>
  )
}

export default HomePage
