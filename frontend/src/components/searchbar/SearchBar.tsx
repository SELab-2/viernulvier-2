import React from 'react'
import { TextField, useTheme } from '@mui/material'

// This represents the entire search bar component, which includes the search input, filter dropdowns, tag list, and layout options.
export interface SearchBarProps {
  placeholder: string
  searchValue: string
  onSearchChange: (value: string) => void
}

// This component renders the search bar with all its functionalities based on the provided props.
const SearchBar: React.FC<SearchBarProps> = ({ placeholder, searchValue, onSearchChange }) => {
  const theme = useTheme()
  return (
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
  )
}

export default SearchBar
