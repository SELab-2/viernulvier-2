import React from 'react'
import { TextField, useTheme } from '@mui/material'

/**
 * Props for the SearchBar component.
 * - tags: list of available tags
 * - selectedTags: currently selected tag names
 * - onTagToggle: callback to toggle tag selection
 * - searchValue: search input value
 * - onSearchChange: callback for search input changes
 * - placeholder: input placeholder text
 */
interface SearchBarProps {
  placeholder?: string
  searchValue: string
  onSearchChange: (value: string) => void
}

/**
 * SearchBar component: renders a search input and tag chips.
 * - Tag selection is controlled via props.
 * - Tag chips call onTagToggle when clicked.
 */
const SearchBar: React.FC<SearchBarProps> = ({
  placeholder = 'Search...',
  searchValue,
  onSearchChange,
}) => {
  const theme = useTheme()
  return (
    <>
      {/* Search input field */}
      <TextField
        fullWidth
        variant="outlined"
        placeholder={placeholder}
        value={searchValue}
        onChange={(e) => onSearchChange(e.target.value)}
        sx={{
          flex: 1,
          '& .MuiInputBase-root': {
            height: 40,
            backgroundColor: theme.palette.background.default,
          },
        }}
        className="search-bar-textfield"
      />
    </>
  )
}

export default SearchBar
