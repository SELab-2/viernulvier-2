import { Box, Stack } from '@mui/material'

import type { Key, ReactNode } from 'react'

export interface GenericListProps<T> {
  items: T[]
  getKey: (item: T) => Key
  renderItem: (item: T) => ReactNode
  spacing?: number
}

const GenericList = <T,>({ items, getKey, renderItem, spacing = 2 }: GenericListProps<T>) => {
  return (
    <Stack spacing={spacing}>
      {items.map((item) => (
        <Box key={getKey(item)}>{renderItem(item)}</Box>
      ))}
    </Stack>
  )
}

export default GenericList
