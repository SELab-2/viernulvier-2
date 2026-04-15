import { useMediaQuery, useTheme } from '@mui/material'

import ProductionGrid from './ProductionGrid'
import ProductionList from './ProductionList'

import type { Production } from '../types/Productions'

export type LayoutMode = 'grid' | 'list'

export interface ProductionViewProps {
  productions: Production[]
  layout?: LayoutMode
  selectedGenreIds?: number[]
}

/**
 * Renders either a {@link ProductionGrid} or a {@link ProductionList} based on
 * the requested {@link LayoutMode}.
 *
 * On viewports narrower than the `md` breakpoint the list card's fixed horizontal
 * layout is too cramped, so the component always falls back to grid regardless of
 * the `layout` prop. Layout toggle controls should live in the parent and pass the
 * chosen mode down via `layout`.
 *
 * @param props.productions List of productions to display.
 * @param props.selectedGenreIds Genre ids currently active in the parent filter state.
 * @param props.layout Requested layout mode; defaults to 'list'.
 * @returns The production view element.
 */
const ProductionView = ({
  productions,
  layout = 'list',
  selectedGenreIds,
}: ProductionViewProps) => {
  const theme = useTheme()
  const isSmall = useMediaQuery(theme.breakpoints.down('md'))

  const activeLayout: LayoutMode = isSmall ? 'grid' : layout

  if (activeLayout === 'list') {
    return <ProductionList productions={productions} selectedGenreIds={selectedGenreIds} />
  }
  if (activeLayout === 'grid') {
    return <ProductionGrid productions={productions} selectedGenreIds={selectedGenreIds} />
  }
}

export default ProductionView
