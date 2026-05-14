import { useMediaQuery, useTheme } from '@mui/material'
import { useMemo, type Key, type ReactNode } from 'react'

import GenericGrid from './GenericGrid'
import GenericList from './GenericList'

import type { SearchViewMode } from './search/types'

type CollectionViewItemProps<T> = {
  getKey: (item: T) => Key
  renderListItem: (item: T) => ReactNode
  renderGridItem: (item: T) => ReactNode
  listSpacing?: number
  transformItems?: (items: T[]) => T[]
  sortItems?: (items: T[]) => T[]
}

export type CollectionViewProps<T> = {
  items: T[]
  layout?: SearchViewMode
} & CollectionViewItemProps<T>

const CollectionView = <T,>(props: CollectionViewProps<T>) => {
  const { items, layout = 'list', transformItems, sortItems } = props
  const theme = useTheme()
  const isSmall = useMediaQuery(theme.breakpoints.down('md'))
  const activeLayout: SearchViewMode = isSmall ? 'grid' : layout

  const viewItems = useMemo(() => {
    let result = transformItems ? transformItems(items) : items
    if (sortItems) {
      result = sortItems(result)
    }
    return result
  }, [items, transformItems, sortItems])

  if (activeLayout === 'list') {
    return (
      <GenericList
        items={viewItems}
        getKey={props.getKey}
        renderItem={props.renderListItem}
        spacing={props.listSpacing}
      />
    )
  }

  return <GenericGrid items={viewItems} getKey={props.getKey} renderItem={props.renderGridItem} />
}

export default CollectionView
