import { Container, Paper, Stack, Typography, Box } from '@mui/material'
import { useTranslation } from 'react-i18next'
import FilteredSearchBar from '../components/searchbar/FilteredSearchBar'
import Tag from '../components/Tag'
import { useLocation, useNavigate } from 'react-router-dom'
import { useCallback, useState } from 'react'

const TAGS = [
  { name: 'theater', displayName: 'Theater' },
  { name: 'concert', displayName: 'Concert' },
  { name: 'expo', displayName: 'Expo' },
  { name: 'film', displayName: 'Film' },
  { name: 'workshop', displayName: 'Workshop' },
  { name: 'music', displayName: 'Music' },
  { name: 'Festival', displayName: 'Festival' },
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
            tags={TAGS}
            selectedTags={selectedTags}
            onTagToggle={handleTagToggle}
            filters={filters}
            layoutOptions={layoutOptions}
            currentLayout={currentLayout}
            onLayoutChange={() => { }}
          />
        </Box>

        {/* Test tags for description and reeks context */}
        <Box sx={{ mt: 4, display: 'flex', gap: 2 }}>
          {/* Description tag example */}
          <Tag name="Festival" displayName="Festival" context="description" />
          {/* Reeks tag example */}
          <Tag name="VIDEODROOM" displayName="Reeks: VIDEODROOM" context="series" />
        </Box>
      </Paper>
    </Container>
  )
}

export default HomePage
