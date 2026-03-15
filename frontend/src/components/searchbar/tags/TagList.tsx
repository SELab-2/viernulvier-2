import React from 'react'
import { Box } from '@mui/material'
import Tag from './Tag'

// This represents the list of tags in the search bar, e.g. "Theater", "Concert", etc.
interface TagListProps {
  tags: { name: string; displayName: string }[]
  selectedTags: string[]
  onTagToggle: (tag: string) => void
}

// This component renders the list of tags as clickable chips.
// It receives the list of all tags, the currently selected tags, and a callback function to toggle a tag's selection state.
const TagList: React.FC<TagListProps> = ({ tags, selectedTags, onTagToggle }) => {
  return (
    <Box display="flex" gap={1} flexWrap="wrap">
      {tags.map((tag) => (
        <Tag
          key={tag.name}
          name={tag.name}
          displayName={tag.displayName}
          selected={selectedTags.includes(tag.name)}
          onTagToggle={onTagToggle}
        />
      ))}
    </Box>
  )
}

export default TagList
