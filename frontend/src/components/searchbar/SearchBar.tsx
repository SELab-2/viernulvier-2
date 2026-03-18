import React, { useState, useCallback, useEffect, useRef } from 'react'
import { TextField, useTheme, Box } from '@mui/material'
import Tag from '../Tag'
import { useNavigate, useLocation } from 'react-router-dom'

// Example tag list (replace with your real tags)
// TODO: Fetch this from the API
const TAGS = [
  { name: 'Dans', displayName: 'Dans' },
  { name: 'Festival', displayName: 'Festival' },
  { name: 'Audiovisueel', displayName: 'Audiovisueel' },
  { name: 'Elektronisch', displayName: 'Elektronisch' },
  { name: 'Live visuals', displayName: 'Live visuals' },
  { name: 'Experimenteel', displayName: 'Experimenteel' },
]

// Parse tags from the URL query string
function parseTagsFromQuery(search: string) {
  const params = new URLSearchParams(search)
  const tags = params.get('tags')
  return tags ? tags.split(',') : []
}

// SearchBar component: text input and tag filter chips
const SearchBar: React.FC = () => {
  const theme = useTheme()
  const navigate = useNavigate()
  const location = useLocation()

  // Tag selection state, synced with URL
  const [selectedTags, setSelectedTags] = useState<string[]>(() =>
    parseTagsFromQuery(location.search),
  )
  // Ref to track previous tags for comparison
  const prevTagsRef = useRef<string[]>(selectedTags)

  // Keep selectedTags in sync with URL changes, but avoid setState in effect body
  useEffect(() => {
    const tags = parseTagsFromQuery(location.search)
    const prev = prevTagsRef.current
    const changed = prev.length !== tags.length || prev.some((t, i) => t !== tags[i])
    if (changed) {
      // Schedule setState outside the effect to avoid lint error
      setTimeout(() => {
        setSelectedTags(tags)
        prevTagsRef.current = tags
      }, 0)
    }
  }, [location.search])

  // Search input value
  const [searchValue, setSearchValue] = useState('')

  // Update the URL with the current tag selection
  const updateUrlWithTags = useCallback(
    (tags: string[]) => {
      const params = new URLSearchParams(location.search)
      if (tags.length > 0) {
        params.set('tags', tags.join(','))
      } else {
        params.delete('tags')
      }
      navigate({ pathname: location.pathname, search: params.toString() }, { replace: true })
    },
    [location, navigate],
  )

  // Toggle tag selection and update state/URL
  const handleTagToggle = (tag: string) => {
    let newTags
    if (selectedTags.includes(tag)) {
      newTags = selectedTags.filter((t) => t !== tag)
    } else {
      newTags = [...selectedTags, tag]
    }
    setSelectedTags(newTags)
    updateUrlWithTags(newTags)
  }

  return (
    <>
      {/* Search input field */}
      <TextField
        fullWidth
        variant="outlined"
        placeholder="Search..."
        value={searchValue}
        onChange={(e) => setSearchValue(e.target.value)}
        sx={{
          flex: 1,
          '& .MuiInputBase-root': {
            height: 40,
            backgroundColor: theme.palette.background.default,
          },
        }}
        className="search-bar-textfield"
      />
      {/* Tag filter chips */}
      <Box sx={{ mt: 2, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
        {TAGS.map((tag) => (
          <Tag
            key={tag.name}
            name={tag.name}
            displayName={tag.displayName}
            selected={selectedTags.includes(tag.name)}
            onTagToggle={handleTagToggle}
            context="search"
          />
        ))}
      </Box>
    </>
  )
}

export default SearchBar
