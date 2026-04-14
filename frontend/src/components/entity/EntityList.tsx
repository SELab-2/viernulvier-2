import { Stack } from '@mui/material'
import { Fragment } from 'react'
import type { Key, ReactNode } from 'react'

export interface EntityListProps<T> {
  items: T[]
  getKey: (item: T) => Key
  renderItem: (item: T) => ReactNode
  spacing?: number
}

const EntityList = <T,>({ items, getKey, renderItem, spacing = 2 }: EntityListProps<T>) => {
  return (
    // Preserve item order in a simple vertical stack.
    <Stack spacing={spacing}>
      {items.map((item) => (
        <Fragment key={getKey(item)}>{renderItem(item)}</Fragment>
      ))}
    </Stack>
  )
}

export default EntityList
