import { Box, Pagination as MuiPagination, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'

export interface PaginationProps {
  // The current page number (1-based index)
  page: number
  // The number of items per page (must be >= 1)
  pageSize: number
  // The total number of items across all pages (must be >= 0)
  totalItems: number
  // Callback function that receives the newly selected page number (1-based index)
  onPageChange: (page: number) => void
  // Optional: whether the pagination controls are disabled
  disabled?: boolean
  // Optional: number of sibling pages to show around the current page (default: 1)
  siblingCount?: number
  // Optional: number of boundary pages to show at the start and end (default: 1)
  boundaryCount?: number
  // Optional i18n key prefix (default: productions.pagination)
  i18nKeyPrefix?: string
}

/**
 * Controlled pagination component for paged API lists.
 *
 * It hides itself when there is 1 page or less and emits the newly selected
 * page number through `onPageChange`.
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
      justifyContent="space-between"
      gap={2}
      role="navigation"
      aria-label={t(`${i18nKeyPrefix}.navigationLabel`)}
    >
      <Typography variant="body2" color="text.secondary">
        {t(`${i18nKeyPrefix}.pageXofY`, { page: activePage, totalPages })}
      </Typography>

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
