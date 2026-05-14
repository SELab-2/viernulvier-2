import { Box, Stack } from '@mui/material'

import type { Key, ReactNode } from 'react'

/**
 * Props for GenericList component.
 *
 * A strongly-typed utility list renderer that maps over an array of items
 * and delegates rendering of each item via a render function.
 */
export interface GenericListProps<T> {
  /**
   * Array of items to render.
   */
  items: T[]

  /**
   * Function that returns a stable React key for each item.
   * Must be unique within the list.
   */
  getKey: (item: T) => Key

  /**
   * Render function for each item.
   */
  renderItem: (item: T) => ReactNode

  /**
   * Vertical spacing between items.
   * @default 2
   */
  spacing?: number
}

/**
 * GenericList
 *
 * A reusable typed list component that:
 * - Renders arbitrary item arrays
 * - Ensures stable keys via getKey
 * - Delegates rendering logic via renderItem
 * - Uses MUI Stack for consistent vertical spacing
 *
 * Useful for keeping list rendering logic clean and reusable across pages.
 *
 * @typeParam T - Type of items in the list
 */
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
