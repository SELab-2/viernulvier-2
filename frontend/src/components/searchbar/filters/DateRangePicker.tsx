import React, { useState } from 'react'
import { Box, TextField, Popover, useTheme, ButtonBase } from '@mui/material'
import { LocalizationProvider, DatePicker } from '@mui/x-date-pickers'
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs'
import dayjs, { Dayjs } from 'dayjs'
import { useTranslation } from 'react-i18next'

// This interface represents a date range with option from and to dates.
// When a date is null, it means there is no limit on that side of the range (e.g. fromDate=null means "up to toDate").
// When both dates are null, it means the entire range is selected (e.g. "All time").
export interface DateRange {
  fromDate: Date | null
  toDate: Date | null
}

// This interface represents the props for the DateRangePicker component, which allows users to select a date range for filtering search results.
interface DateRangePickerProps {
  period: DateRange
  setPeriod: (dateRange: DateRange) => void
}

// This component renders a button that shows the currently selected date range and opens a popover with two date pickers (from and to) when clicked.
// It uses the Material-UI library for styling and components, and dayjs for date manipulation.
const DateRangePicker: React.FC<DateRangePickerProps> = ({ period, setPeriod }) => {
  const theme = useTheme()
  const t = useTranslation().t
  const minDate = dayjs().year(2016).startOf('year')
  const maxDate = dayjs().year(dayjs().year()).endOf('year')

  const [fromDate, setFromDate] = useState<Dayjs | null>(
    period.fromDate ? dayjs(period.fromDate) : null,
  )
  const [toDate, setToDate] = useState<Dayjs | null>(period.toDate ? dayjs(period.toDate) : null)

  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null)

  const handleOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleClose = () => {
    setAnchorEl(null)
  }

  const open = Boolean(anchorEl)
  const id = open ? 'date-range-popover' : undefined

  const formatDisplay = () => {
    const from = fromDate?.isValid() ? fromDate : null
    const to = toDate?.isValid() ? toDate : null

    if (from && !to) {
      return `${t('searchbar.period.from_x', { date: from.format('DD/MM/YYYY') })}`
    }
    if (!from && to) {
      return `${t('searchbar.period.to_x', { date: to.format('DD/MM/YYYY') })}`
    }
    if (from && to) {
      return `${from.format('DD/MM/YYYY')} - ${to.format('DD/MM/YYYY')}`
    }
    return t('searchbar.period.all')
  }

  return (
    <>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <ButtonBase onClick={handleOpen} sx={{ width: 205 }}>
          <TextField
            label={t('searchbar.period.label')}
            value={formatDisplay()}
            size="small"
            sx={{ width: '100%' }}
            slotProps={{
              input: {
                readOnly: true,
                sx: {
                  backgroundColor: theme.palette.background.default,
                },
              },
            }}
          />
        </ButtonBase>
      </Box>

      <Popover
        id={id}
        open={open}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
        transformOrigin={{ vertical: 'top', horizontal: 'left' }}
      >
        <Box sx={{ p: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
          <LocalizationProvider dateAdapter={AdapterDayjs}>
            <DatePicker
              format="DD/MM/YYYY"
              label={t('searchbar.period.from_label')}
              value={fromDate}
              onChange={(newValue) => {
                setFromDate(newValue)
                if (newValue?.isValid()) {
                  setPeriod({
                    fromDate: newValue.toDate(),
                    toDate: toDate ? toDate.toDate() : null,
                  })
                }
              }}
              minDate={minDate}
              maxDate={maxDate}
              slotProps={{
                textField: { size: 'small' },
              }}
            />
            <DatePicker
              format="DD/MM/YYYY"
              label={t('searchbar.period.to_label')}
              value={toDate}
              onChange={(newValue) => {
                setToDate(newValue)
                if (newValue?.isValid()) {
                  setPeriod({
                    fromDate: fromDate ? fromDate.toDate() : null,
                    toDate: newValue.toDate(),
                  })
                }
              }}
              minDate={minDate}
              maxDate={maxDate}
              slotProps={{
                textField: { size: 'small' },
              }}
            />
          </LocalizationProvider>
        </Box>
      </Popover>
    </>
  )
}

export default DateRangePicker
