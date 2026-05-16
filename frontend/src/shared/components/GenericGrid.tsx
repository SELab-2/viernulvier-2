import { Box, useTheme } from '@mui/material'

import { createCommonStyles } from '../../theme/styles'

import type { Key, ReactNode } from 'react'

/**
 * Props for GenericGrid component.
 *
 * A reusable grid wrapper that renders a collection of items using
 * a shared grid layout defined in the app theme styles.
 */
export interface GenericGridProps<T> {
  /**
   * Array of items to render inside the grid.
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
}

/**
 * GenericGrid
 *
 * A reusable grid rendering component that:
 * - Uses shared `gridContainer` styles from theme
 * - Maps items into grid cells
 * - Delegates rendering via renderItem callback
 * - Ensures stable keys via getKey
 *
 * This is intended for collection pages where items should be displayed
 * in a responsive grid layout consistent with the app design system.
 *
 * @typeParam T - Type of items being rendered
 */
const GenericGrid = <T,>({ items, getKey, renderItem }: GenericGridProps<T>) => {
  const theme = useTheme()
  const commonStyles = createCommonStyles(theme)

  return (
    <Box sx={commonStyles.gridContainer}>
      {items.map((item) => (
        <Box key={getKey(item)} sx={{ display: 'flex' }}>
          {renderItem(item)}
        </Box>
      ))}
    </Box>
  )
}

export default GenericGrid
