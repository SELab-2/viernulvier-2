import { Chip, useTheme } from '@mui/material'
import React from 'react'

// This represents a single tag chip in the search bar, e.g. "Theater", "Concert", etc.
interface LayoutOptionProps {
  name: string
  displayName: string
  selected: boolean
  onSelected: (tag: string) => void
}

// This component renders a single tag chip based on the provided props.
const LayoutOption: React.FC<LayoutOptionProps> = ({ name, displayName, selected, onSelected }) => {
  const theme = useTheme()

  return (
    <Chip
      key={name}
      label={displayName}
      clickable
      onClick={() => onSelected(name)}
      sx={
        selected
          ? {
              backgroundColor: `${theme.palette.mode === 'light' ? 'black' : 'white'} !important`,
              color: theme.palette.mode === 'light' ? 'white' : 'black',
              border: `1px solid transparent`,
              borderRadius: '5px',
            }
          : {
              backgroundColor: theme.palette.background.default,
              color: theme.palette.mode === 'light' ? 'black' : 'white',
              border: `1px solid ${theme.palette.divider}`,
              borderRadius: '5px',
            }
      }
    />
  )
}

export default LayoutOption
