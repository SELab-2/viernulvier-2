import React from 'react'
import { Box, TextField, useTheme } from '@mui/material'
import DropDownFilter, { DropDownFilterProps } from './filters/DropDownFilter'
import TagList from './tags/TagList'
import LayoutOptionList from './layout_options/LayoutOptionList'

// This represents the entire search bar component, which includes the search input, filter dropdowns, tag list, and layout options.
export interface SearchBarProps {
  placeholder: string
  searchValue: string
  onSearchChange: (value: string) => void
  filters: DropDownFilterProps[]
  tags: { name: string; displayName: string }[]
  selectedTags: string[]
  onTagToggle: (tag: string) => void
  layoutOptions: { name: string; displayName: string }[]
  currentLayout: string
  onLayoutChange: (layout: string) => void
}

// This component renders the search bar with all its functionalities based on the provided props.
const SearchBar: React.FC<SearchBarProps> = ({
  placeholder,
  searchValue,
  onSearchChange,
  filters,
  tags,
  selectedTags,
  onTagToggle,
  layoutOptions: layoutOptions,
  currentLayout: currentLayout,
  onLayoutChange: onLayoutChange,
}) => {
  const theme = useTheme()
  return (
    <Box>
      <Box display="flex" gap={2} alignItems="center">
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
        {filters.map((filter) => (
          <DropDownFilter key={filter.name} {...filter} />
        ))}
      </Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mt={2}>
        <TagList tags={tags} selectedTags={selectedTags} onTagToggle={onTagToggle} />
        <LayoutOptionList
          layout_options={layoutOptions}
          selected_layout={currentLayout}
          onLayoutChange={onLayoutChange}
        />
      </Box>
    </Box>
  )
}

export default SearchBar
