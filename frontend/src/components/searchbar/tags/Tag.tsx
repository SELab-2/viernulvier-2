import { Chip, useTheme } from '@mui/material'
import React from 'react'

// This represents a single tag chip in the search bar, e.g. "Theater", "Concert", etc.
interface TagProps {
  name: string
  displayName: string
  selected: boolean
  onTagToggle: (tag: string) => void
}

// This component renders a single tag chip based on the provided props.
const Tag: React.FC<TagProps> = ({ name, displayName, selected, onTagToggle }) => {
  const theme = useTheme()

  return (
    <Chip
      key={name}
      label={displayName}
      clickable
      onClick={() => onTagToggle(name)}
      sx={
        selected
          ? {
              backgroundColor: '#8224E3FF !important',
              color: 'white',
            }
          : {
              backgroundColor: theme.palette.background.default,
            }
      }
    />
  )
}

export default Tag
