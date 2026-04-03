import { Box, Container, Paper, Stack, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'
import FilteredSearchBar from '../components/searchbar/FilteredSearchBar'
import Tag from '../components/Tag'
import FloatingAlert from '../components/FloatingAlert'
import { useLocation, useNavigate } from 'react-router-dom'
import { useCallback, useEffect, useState } from 'react'

const TAGS = [
  { display_name: 'theater', name: { nl: 'Theater', en: 'THEATER' } },
  { display_name: 'concert', name: { nl: 'Concert', en: 'CONCERT' } },
  { display_name: 'expo', name: { nl: 'Expo', en: 'EXPO' } },
  { display_name: 'film', name: { nl: 'Film', en: 'FILM' } },
  { display_name: 'workshop', name: { nl: 'Workshop', en: 'WORKSHOP' } },
  { display_name: 'music', name: { nl: 'Muziek', en: 'MUSIC' } },
  { display_name: 'Festival', name: { nl: 'Festival', en: 'FESTIVAL' } },
]

// TODO: Fetch tags from API in the future

/**
 * Parse selected tags from the URL query string.
 * @param search - The URL search string (e.g. '?tags=theater,concert')
 * @returns Array of tag names
 */
function parseTagsFromQuery(search: string): string[] {
  const params = new URLSearchParams(search)
  const tags = params.get('tags')
  return tags ? tags.split(',').filter(Boolean) : []
}

const HomePage = () => {
  const { t } = useTranslation()
  const location = useLocation()
  const navigate = useNavigate()
  const selectedTags = parseTagsFromQuery(location.search)

  const locationState = location.state as
    | {
        floatingAlert?: {
          open: boolean
          message: string
          severity: 'error' | 'warning' | 'info' | 'success'
        }
      }
    | null
    | undefined

  // toast message when redirected from detail error
  const [toastOpen, setToastOpen] = useState(locationState?.floatingAlert?.open ?? false)
  const [toastMessage] = useState(locationState?.floatingAlert?.message ?? '')
  const [toastSeverity] = useState<'error' | 'warning' | 'info' | 'success'>(
    locationState?.floatingAlert?.severity ?? 'info',
  )

  // Local state for search input
  const [searchValue, setSearchValue] = useState('')
  // Demo: no filters or layout options
  const filters: import('../components/searchbar/filters/DropDownFilter').DropDownFilterProps[] = []
  const layoutOptions: { name: string; displayName: string }[] = []
  const currentLayout = ''

  /**
   * Toggle a tag's selection and update the URL.
   * @param tag - The tag name to toggle
   */
  useEffect(() => {
    if (locationState?.floatingAlert?.open) {
      navigate(location.pathname, { replace: true, state: {} })
    }
  }, [location.pathname, locationState, navigate])

  const handleTagToggle = useCallback(
    (tag: string) => {
      // Get current tags from URL and toggle the clicked tag
      const tags = parseTagsFromQuery(location.search)
      let newTags
      if (tags.includes(tag)) {
        newTags = tags.filter((t) => t !== tag)
      } else {
        newTags = [...tags, tag]
      }
      // Update URL with new tags
      const params = new URLSearchParams(location.search)
      if (newTags.length > 0) {
        params.set('tags', newTags.join(','))
      } else {
        params.delete('tags')
      }
      navigate({ search: params.toString() }, { replace: false })
    },
    [location.search, navigate],
  )

  return (
    <Container maxWidth="md" sx={{ py: 6 }}>
      <FloatingAlert
        open={toastOpen}
        onClose={() => setToastOpen(false)}
        message={toastMessage}
        severity={toastSeverity}
      />
      <Paper elevation={3} sx={{ p: 4 }}>
        <Stack spacing={3}>
          <Typography variant="h3" component="h1">
            {t('title')}
          </Typography>
          <Typography variant="subtitle1">{t('subtitle')}</Typography>
        </Stack>
        <Box sx={{ mt: 4 }}>
          <FilteredSearchBar
            placeholder="Search..."
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
