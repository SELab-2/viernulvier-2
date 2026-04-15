import GenericList from './GenericList'
import ProductionListCard from './productions/ProductionListCard'

import type { Production } from '../types/Productions'

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
    <GenericList
      items={productions}
      getKey={(production) => production.id}
      renderItem={(production) => (
        <ProductionListCard production={production} selectedGenreIds={selectedGenreIds} />
      )}
    />
  )
}

export default ProductionList
