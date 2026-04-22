import { useState, useEffect, useRef } from 'react'
import { Box, IconButton, OutlinedInput, Typography } from '@mui/material'
import {
  FirstPage as FirstPageIcon,
  LastPage as LastPageIcon,
  NavigateBefore as PrevIcon,
  NavigateNext as NextIcon,
} from '@mui/icons-material'
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
  const hasPagination = totalPages > 1
  const activePage = hasPagination ? Math.min(Math.max(page, 1), totalPages) : 1

  // Local input state so user can type freely before change
  const [inputValue, setInputValue] = useState(String(activePage))
  const inputRef = useRef<HTMLInputElement>(null)

  // Keep input in sync with active page changes
  useEffect(() => {
    setInputValue(String(activePage))
  }, [activePage])

  if (!hasPagination) {
    return null
  }

  const commitPage = (raw: string) => {
    const parsed = parseInt(raw, 10)
    if (!isNaN(parsed)) {
      const clamped = Math.min(Math.max(parsed, 1), totalPages)
      setInputValue(String(clamped))
      if (clamped !== activePage) {
        onPageChange(clamped)
      }
    } else {
      // Reset to current page if input is invalid
      setInputValue(String(activePage))
    }
  }

  const handleInputBlur = () => {
    commitPage(inputRef.current?.value ?? inputValue)
  }

  const navButtonSx = {
    borderRadius: 1,
    border: '1px solid',
    borderColor: 'divider',
    width: 32,
    height: 32,
    color: disabled ? 'action.disabled' : 'action.secondary',
    '&:hover:not(:disabled)': {
      backgroundColor: 'action.hover',
      borderColor: 'primary.main',
      color: 'primary.main',
    },
    '&.Mui-disabled': {
      borderColor: 'divider',
    },
    transition: 'border-color 0.15s, color 0.15s, background-color 0.15s',
  }

  return (
    <Box
      role="navigation"
      aria-label={t(`${i18nKeyPrefix}.navigationLabel`)}
      sx={{
        display: 'flex',
        flexDirection: 'row',
        flexWrap: { xs: 'wrap', sm: 'nowrap' },
        alignItems: 'center',
        justifyContent: { xs: 'center', sm: 'flex-end' },
        columnGap: 1,
        rowGap: 0.75,
      }}
    >
      {/* First Page Button */}
      <IconButton
        size="small"
        disabled={disabled || activePage === 1}
        onClick={() => onPageChange(1)}
        aria-label={t(`${i18nKeyPrefix}.firstPage`)}
        sx={navButtonSx}
      >
        <FirstPageIcon fontSize="small" />
      </IconButton>

      {/* Previous Page Button */}
      <IconButton
        size="small"
        disabled={disabled || activePage === 1}
        onClick={() => onPageChange(activePage - 1)}
        aria-label={t(`${i18nKeyPrefix}.previousPage`)}
        sx={navButtonSx}
      >
        <PrevIcon fontSize="small" />
      </IconButton>

      {/* Page Input */}
      <OutlinedInput
        inputRef={inputRef}
        size="small"
        disabled={disabled}
        value={inputValue}
        aria-label={t(`${i18nKeyPrefix}.currentPage`, { page: activePage })}
        onChange={(e) => setInputValue(e.target.value)}
        onBlur={handleInputBlur}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            commitPage(e.currentTarget.value)
            inputRef.current?.blur()
          }
          if (e.key === 'ArrowUp' || e.key === 'ArrowRight') {
            e.preventDefault()
            const nextPage = Math.min(activePage + 1, totalPages)
            setInputValue(String(nextPage))
            onPageChange(nextPage)
          }
          if (e.key === 'ArrowDown' || e.key === 'ArrowLeft') {
            e.preventDefault()
            const prevPage = Math.max(activePage - 1, 1)
            setInputValue(String(prevPage))
            onPageChange(prevPage)
          }
        }}
        inputProps={{
          'aria-label': t(`${i18nKeyPrefix}.currentPage`, { page: activePage }),
          style: { textAlign: 'center', padding: '4px 0' },
        }}
        sx={{
          width: `${Math.max(String(totalPages).length, 2) + 2}ch`,
          minWidth: 40,
          height: 32,
          borderRadius: '8px',
          fontSize: '0.875rem',
          fontWeight: 500,
          '& .MuiOutlinedInput-notchedOutline': {
            borderColor: 'divider',
          },
          '&:hover .MuiOutlinedInput-notchedOutline': {
            borderColor: 'primary.main',
          },
          '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
            borderColor: 'primary.main',
            borderWidth: 2,
          },
        }}
      />

      {/* Of N label */}
      <Typography
        variant="body2"
        color="text.secondary"
        sx={{ userSelect: 'none', whiteSpace: 'nowrap' }}
        aria-live="polite"
        aria-atomic="true"
      >
        {t(`${i18nKeyPrefix}.ofPages`, { count: totalPages })}
      </Typography>

      {/* Next Page Button */}
      <IconButton
        size="small"
        disabled={disabled || activePage === totalPages}
        onClick={() => onPageChange(activePage + 1)}
        aria-label={t(`${i18nKeyPrefix}.nextPage`)}
        sx={navButtonSx}
      >
        <NextIcon fontSize="small" />
      </IconButton>

      {/* Last Page Button */}
      <IconButton
        size="small"
        disabled={disabled || activePage === totalPages}
        onClick={() => onPageChange(totalPages)}
        aria-label={t(`${i18nKeyPrefix}.lastPage`)}
        sx={navButtonSx}
      >
        <LastPageIcon fontSize="small" />
      </IconButton>
    </Box>
  )
}

export default Pagination
