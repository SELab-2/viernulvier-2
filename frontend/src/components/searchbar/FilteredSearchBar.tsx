import React from 'react'
import { Box } from '@mui/material'
import DropDownFilter, { DropDownFilterProps } from './filters/DropDownFilter'
import TagList from './tags/TagList'
import LayoutOptionList from './layout_options/LayoutOptionList'
import SearchBar from './SearchBar'

// This represents the entire search bar component, which includes the search input, filter dropdowns, tag list, and layout options.
export interface FilteredSearchBarProps {
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
const FilteredSearchBar: React.FC<FilteredSearchBarProps> = ({
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
  return (
    <Box>
      <Box display="flex" gap={2} alignItems="center">
        <SearchBar
          placeholder={placeholder}
          searchValue={searchValue}
          onSearchChange={onSearchChange}
          tags={tags}
          selectedTags={selectedTags}
          onTagToggle={onTagToggle}
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

export default FilteredSearchBar
