import { useMediaQuery, useTheme } from '@mui/material'
import type { Key, ReactNode } from 'react'
import type { SearchViewMode } from '../searchbar/types'
import EntityGrid from './EntityGrid'
import EntityList from './EntityList'

type EntityViewItemProps<T> = {
  getKey: (item: T) => Key
  renderListItem: (item: T) => ReactNode
  renderGridItem: (item: T) => ReactNode
  listSpacing?: number
}

type EntityViewProps<T> = {
  items: T[]
  layout?: SearchViewMode
} & EntityViewItemProps<T>

const EntityView = <T,>(props: EntityViewProps<T>) => {
  const { items, layout = 'list' } = props
  const theme = useTheme()
  const isSmall = useMediaQuery(theme.breakpoints.down('md'))

  // Narrow viewports always use the grid layout so cards stay readable.
  const activeLayout: SearchViewMode = isSmall ? 'grid' : layout

  // Render the shared list wrapper when list layout is active.
  if (activeLayout === 'list') {
    return (
      <EntityList
        items={items}
        getKey={props.getKey}
        renderItem={props.renderListItem}
        spacing={props.listSpacing}
      />
    )
  }

  // Render the shared grid wrapper otherwise.
  return (
    <EntityGrid
      items={items}
      getKey={props.getKey}
      renderItem={props.renderGridItem}
    />
  )
}

export default EntityView
