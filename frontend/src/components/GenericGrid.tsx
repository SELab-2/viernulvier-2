import { Box, useTheme } from '@mui/material'

import { createCommonStyles } from '../theme/styles'

import type { Key, ReactNode } from 'react'

export interface GenericGridProps<T> {
  items: T[]
  getKey: (item: T) => Key
  renderItem: (item: T) => ReactNode
}

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
