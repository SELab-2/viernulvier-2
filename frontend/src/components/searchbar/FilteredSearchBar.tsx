import React from 'react'
import { Box, Button } from '@mui/material'
import DropDownFilter, { DropDownFilterProps } from './filters/DropDownFilter'
import TagList from './tags/TagList'
import LayoutOptionList from './layout_options/LayoutOptionList'
import SearchBar from './SearchBar'
import { useTranslation } from 'react-i18next'
import DateRangePicker, { DateRange } from './filters/DateRangePicker'

// This represents the entire search bar component, which includes the search input, filter dropdowns, tag list, and layout options.
export interface FilteredSearchBarProps {
  placeholder: string
  searchValue: string
  onSearchChange: (value: string) => void
  filters: DropDownFilterProps[]
  period?: DateRange
  setPeriod?: (period: DateRange) => void
  tags: { name: string; displayName: string }[]
  selectedTags: string[]
  onTagToggle: (tag: string) => void
  layoutOptions: { name: string }[]
  currentLayout: string
  onLayoutChange: (layout: string) => void
  onSearchSubmit?: () => void
}

// This component renders the search bar with all its functionalities based on the provided props.
const FilteredSearchBar: React.FC<FilteredSearchBarProps> = ({
  placeholder,
  searchValue,
  onSearchChange,
  filters,
  period,
  setPeriod,
  tags,
  selectedTags,
  onTagToggle,
  layoutOptions: layoutOptions,
  currentLayout: currentLayout,
  onLayoutChange: onLayoutChange,
}) => {
  const t = useTranslation().t

  return (
    <Box>
      <Box
        display="flex"
        flexWrap="wrap"
        gap={2}
        alignItems="center"
        sx={{ '& > *': { minWidth: 0 } }} // allow children to shrink
      >
        <Box
          sx={{
            flex: '1 1 240px', // grow, shrink, min-width
            minWidth: 160,
          }}
        >
          <SearchBar
            placeholder={placeholder}
            searchValue={searchValue}
            onSearchChange={onSearchChange}
          />
        </Box>

        {period && setPeriod && <DateRangePicker period={period} setPeriod={setPeriod} />}

        <Box
          display="flex"
          flexWrap="wrap"
          gap={1}
          alignItems="center"
          sx={{
            flex: '0 1 auto',
            '> *': { flexShrink: 0 },
          }}
        >
          {filters.map((filter) => (
            <DropDownFilter key={filter.name} {...filter} />
          ))}
          <Button
            variant="contained"
            sx={{
              backgroundColor: '#8224E3FF',
              height: 40,
              whiteSpace: 'nowrap',
            }}
          >
            {t('searchbar.search')}
          </Button>
        </Box>
      </Box>

      <Box
        display="flex"
        flexWrap="wrap"
        justifyContent="space-between"
        alignItems="center"
        mt={2}
        gap={1}
      >
        <Box sx={{ flex: '1 1 200px', minWidth: 120 }}>
          <TagList tags={tags} selectedTags={selectedTags} onTagToggle={onTagToggle} />
        </Box>

        {layoutOptions.length > 1 && (
          <Box sx={{ flex: '0 0 auto', mt: { xs: 1, sm: 0 } }}>
            <LayoutOptionList
              layout_options={layoutOptions}
              selected_layout={currentLayout}
              onLayoutChange={onLayoutChange}
            />
          </Box>
        )}
      </Box>
    </Box>
  )
}

export default FilteredSearchBar
