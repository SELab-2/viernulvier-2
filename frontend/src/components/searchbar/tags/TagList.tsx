import React from 'react'
import { Box } from '@mui/material'
import Tag from '../../Tag'

// This represents the list of tags in the search bar, e.g. "Theater", "Concert", etc.
interface TagListProps {
  tags: { display_name: string; name: Record<string, string> }[]
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
          key={tag.display_name}
          tagName={tag.display_name}
          labels={tag.name}
          selected={selectedTags.includes(tag.display_name)}
          onTagToggle={onTagToggle}
        />
      ))}
    </Box>
  )
}

export default TagList
