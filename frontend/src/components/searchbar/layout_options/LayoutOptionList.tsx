import React from 'react'
import { Box } from '@mui/material'
import LayoutOption from './LayoutOption'

// This represents a layout option in the search bar, e.g. "Grid" or "List".
interface LayoutOptionListProps {
  layout_options: { name: string; displayName: string }[]
  selected_layout: string
  onLayoutChange: (tag: string) => void
}

// This component renders the list of layout options as clickable chips.
// It receives the list of all layout options, the currently selected layout, and a callback function to toggle a layout's selection state.
const LayoutOptionList: React.FC<LayoutOptionListProps> = ({
  layout_options,
  selected_layout,
  onLayoutChange: onLayoutChange,
}) => {
  return (
    <Box display="flex" gap={1} flexWrap="wrap">
      {layout_options.map((layout) => (
        <LayoutOption
          key={layout.name}
          name={layout.name}
          displayName={layout.displayName}
          selected={selected_layout === layout.name}
          onSelected={onLayoutChange}
        />
      ))}
    </Box>
  )
}

export default LayoutOptionList
