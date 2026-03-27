import React from 'react'
import { Box } from '@mui/material'
import LayoutOption from './LayoutOption'

// This represents a layout option in the search bar, e.g. "Grid" or "List".
interface LayoutOptionListProps {
  layoutOptions: { name: string }[]
  selectedLayout: string
  onLayoutChange: (tag: string) => void
}

// This component renders the list of layout options as clickable chips.
// It receives the list of all layout options, the currently selected layout, and a callback function to toggle a layout's selection state.
const LayoutOptionList: React.FC<LayoutOptionListProps> = ({
  layoutOptions,
  selectedLayout,
  onLayoutChange,
}) => {
  return (
    <Box display="flex" gap={1} flexWrap="wrap">
      {layoutOptions.map((layout) => (
        <LayoutOption
          key={layout.name}
          name={layout.name}
          selected={selectedLayout === layout.name}
          onSelected={onLayoutChange}
        />
      ))}
    </Box>
  )
}

export default LayoutOptionList
