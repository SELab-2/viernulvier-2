import React from 'react'
import { Box, FormControl, Select, MenuItem, useTheme } from '@mui/material'

// This represents a single option in a filter dropdown, e.g. "2020" in the "Period" filter.
interface FilterOption {
  name: string
  displayName: string
}

// This represents a single filter dropdown in the search bar, e.g. "Period: [All, 2020, 2021, ...]"
// It receives its configuration from the parent component (e.g. HomePage) via props.
export interface DropDownFilterProps {
  name: string
  displayName: string
  options: FilterOption[]
  value: string
  onChange: (value: string) => void
}

// This component renders a single filter dropdown based on the provided props.
const DropDownFilter: React.FC<DropDownFilterProps> = ({
  name,
  displayName,
  options,
  value,
  onChange,
}) => {
  const theme = useTheme()

  return (
    <Box key={name} sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 160 }}>
      <Box component="span" sx={{ whiteSpace: 'nowrap', fontSize: '0.85rem', fontWeight: 500 }}>
        {`${displayName}:`}
      </Box>
      <FormControl
        sx={{
          flex: 1,
          '& .MuiInputBase-root': { height: 40, backgroundColor: theme.palette.background.default },
        }}
        className="search-bar-select"
      >
        <Select
          value={value}
          onChange={(e) => onChange(String(e.target.value))}
          displayEmpty={false}
          sx={{ minWidth: 120 }}
        >
          {options.map((option) => (
            <MenuItem key={option.name} value={option.name}>
              {option.displayName}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    </Box>
  )
}

export default DropDownFilter
