import GenericGrid from './GenericGrid'
import ProductionGridCard from './productions/ProductionGridCard'

import type { Production } from '../types/Productions'

export interface ProductionGridProps {
  productions: Production[]
  selectedGenreIds?: number[]
  selectedTagIds?: number[]
}

/**
 * Renders a responsive wrap-grid of {@link ProductionGridCard} items.
 *
 * Cards are laid out with `flex-wrap` so they reflow naturally across screen sizes.
 * Each card maintains its own fixed width (350 px) and the gap between cards is
 * uniform in both axes.
 *
 * @param props.productions List of productions to display.
 * @param props.selectedGenreIds Genre ids currently active in the parent filter state.
 * @returns The grid container element.
 */
const ProductionGrid = ({ productions, selectedGenreIds, selectedTagIds }: ProductionGridProps) => {
  return (
    <GenericGrid
      items={productions}
      getKey={(production) => production.id}
      renderItem={(production) => (
        <ProductionGridCard
          production={production}
          selectedGenreIds={selectedGenreIds}
          selectedTagIds={selectedTagIds}
        />
      )}
    />
  )
}

export default ProductionGrid
