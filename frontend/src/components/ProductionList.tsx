import { Stack } from '@mui/material'
import type { Production } from '../types/Productions'
import ProductionListCard from './ProductionListCard'

export interface ProductionListProps {
  productions: Production[]
  selectedGenreIds?: number[]
}

/**
 * Renders a vertical stack of {@link ProductionListCard} items.
 *
 * Cards are laid out in a single column with a consistent gap between rows,
 * stretching to fill the available width.
 *
 * @param props.productions List of productions to display.
 * @param props.selectedGenreIds Genre ids currently active in the parent filter state.
 * @returns The list container element.
 */
const ProductionList = ({ productions, selectedGenreIds }: ProductionListProps) => {
  return (
    <Stack spacing={2}>
      {productions.map((production) => (
        <ProductionListCard
          key={production.id}
          production={production}
          selectedGenreIds={selectedGenreIds}
        />
      ))}
    </Stack>
  )
}

export default ProductionList
