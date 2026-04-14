import { Box } from '@mui/material'
import { Fragment } from 'react'
import type { Key, ReactNode } from 'react'

export interface EntityGridProps<T> {
  items: T[]
  getKey: (item: T) => Key
  renderItem: (item: T) => ReactNode
}

const EntityGrid = <T,>({ items, getKey, renderItem }: EntityGridProps<T>) => {
  return (
    // Let cards wrap naturally while keeping the grid centered.
    <Box display="flex" flexWrap="wrap" gap={3} justifyContent="center">
      {items.map((item) => (
        <Fragment key={getKey(item)}>{renderItem(item)}</Fragment>
      ))}
    </Box>
  )
}

export default EntityGrid
