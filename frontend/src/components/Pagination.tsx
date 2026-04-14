import { Box, Pagination as MuiPagination } from '@mui/material'
import { useTranslation } from 'react-i18next'

export interface PaginationProps {
  page: number
  pageSize: number
  totalItems: number
  onPageChange: (page: number) => void
  disabled?: boolean
  siblingCount?: number
  boundaryCount?: number
  i18nKeyPrefix?: string
}

/**
 * Controlled pagination component for paged API lists.
 *
 * It hides itself when there is 1 page or less and emits the newly selected
 * page number through `onPageChange`.
 *
 * @param props.page Current page number (1-based index).
 * @param props.pageSize Number of items per page (must be >= 1).
 * @param props.totalItems Total number of items across all pages (must be >= 0).
 * @param props.onPageChange Callback function that receives the newly selected page number (1-based index).
 * @param props.disabled Optional boolean to disable the pagination controls.
 * @param props.siblingCount Optional number of sibling pages to show around the current page (default: 1).
 * @param props.boundaryCount Optional number of boundary pages to show at the start and end (default: 1).
 * @param props.i18nKeyPrefix Optional prefix for internationalization keys used in the Pagination component (default: 'productions.pagination').
 * @returns A React component that renders pagination controls based on the provided props. *
 */
const Pagination = ({
  page,
  pageSize,
  totalItems,
  onPageChange,
  disabled = false,
  siblingCount = 1,
  boundaryCount = 1,
  i18nKeyPrefix = 'productions.pagination',
}: PaginationProps) => {
  const { t } = useTranslation()

  const safePageSize = Math.max(1, pageSize)
  const totalPages = Math.ceil(totalItems / safePageSize)

  if (totalPages <= 1) {
    return null
  }

  const activePage = Math.min(Math.max(page, 1), totalPages)

  return (
    <Box
      display="flex"
      flexDirection={{ xs: 'column', sm: 'row' }}
      alignItems="center"
      justifyContent="flex-end"
      gap={2}
      width="100%"
      pr={{ xs: 0, sm: 1 }}
      role="navigation"
      aria-label={t(`${i18nKeyPrefix}.navigationLabel`)}
    >
      <MuiPagination
        color="primary"
        shape="rounded"
        page={activePage}
        count={totalPages}
        disabled={disabled}
        siblingCount={siblingCount}
        boundaryCount={boundaryCount}
        onChange={(_event, value) => onPageChange(value)}
        getItemAriaLabel={(type, itemPage, selected) => {
          if (type === 'first') {
            return t(`${i18nKeyPrefix}.firstPage`)
          }
          if (type === 'last') {
            return t(`${i18nKeyPrefix}.lastPage`)
          }
          if (type === 'next') {
            return t(`${i18nKeyPrefix}.nextPage`)
          }
          if (type === 'previous') {
            return t(`${i18nKeyPrefix}.previousPage`)
          }
          return selected
            ? t(`${i18nKeyPrefix}.currentPage`, { page: itemPage })
            : t(`${i18nKeyPrefix}.goToPage`, { page: itemPage })
        }}
      />
    </Box>
  )
}

export default Pagination
