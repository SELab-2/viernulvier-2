import CalendarTodayOutlinedIcon from '@mui/icons-material/CalendarTodayOutlined'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import RoomOutlinedIcon from '@mui/icons-material/RoomOutlined'
import ScheduleOutlinedIcon from '@mui/icons-material/ScheduleOutlined'
import {
  Box,
  Collapse,
  Divider,
  IconButton,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { Event } from '../../types/Events'
import { formatDate, formatTime } from '../../utils/formatDate'
import { getHallDisplayName } from '../../utils/hall'

interface EventsListProps {
  events: Event[]
}

/**
 * Renders the list of events for a production detail page.
 *
 * Each event row shows date, time, and venue. When the event has prices,
 * a chevron button expands an inline price table below that row.
 */
export default function EventsList({ events }: EventsListProps) {
  const { t, i18n } = useTranslation()
  const lang = i18n.language
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set())

  if (!events.length) {
    return (
      <Typography variant="body2" color="text.secondary">
        {t('productions.detail.noEvents', 'Geen geplande events.')}
      </Typography>
    )
  }

  const toggle = (id: number) =>
    setExpandedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })

  return (
    <Stack spacing={0} divider={<Divider sx={{ my: 1.5 }} />}>
      {events.map((event) => {
        const expanded = expandedIds.has(event.id)
        const hasPrices = event.prices?.length > 0

        return (
          <Box key={event.id}>
            {/* -- Event row -- */}
            <Stack
              direction="row"
              alignItems="center"
              justifyContent="space-between"
            >
              <Stack spacing={0.5} sx={{ flex: 1, minWidth: 0 }}>
                {/* Date + time */}
                <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap">
                  <Stack direction="row" spacing={0.75} alignItems="center">
                    <CalendarTodayOutlinedIcon
                      sx={{ fontSize: '0.95rem', color: 'text.primary' }}
                    />
                    <Typography variant="body2" fontWeight={600} color="text.primary">
                      {event.starts_at ? formatDate(event.starts_at, lang) : '—'}
                    </Typography>
                  </Stack>

                  {event.starts_at && (
                    <Stack direction="row" spacing={0.75} alignItems="center">
                      <ScheduleOutlinedIcon sx={{ fontSize: '0.95rem', color: 'text.primary' }} />
                      <Typography variant="body2" color="text.primary" fontWeight={500}>
                        {formatTime(event.starts_at, lang)}
                        {event.ends_at ? ` - ${formatTime(event.ends_at, lang)}` : ''}
                      </Typography>
                    </Stack>
                  )}
                </Stack>

                {/* Venue */}
                {(() => {
                  const hallName = getHallDisplayName(event, lang)
                  return (
                    hallName && (
                      <Stack direction="row" spacing={0.75} alignItems="center">
                        <RoomOutlinedIcon sx={{ fontSize: '0.9rem', color: 'text.primary' }} />
                        <Typography variant="body2" color="text.primary">
                          {hallName}
                        </Typography>
                      </Stack>
                    )
                  )
                })()}
              </Stack>

              {/* Expand prices toggle */}
              <Stack direction="row" spacing={1} alignItems="center" sx={{ flexShrink: 0, ml: 2 }}>
                {hasPrices && (
                  <IconButton
                    size="small"
                    onClick={() => toggle(event.id)}
                    aria-expanded={expanded}
                    aria-label={
                      expanded
                        ? t('events.collapsePrices', 'Prijzen verbergen')
                        : t('events.expandPrices', 'Prijzen tonen')
                    }
                    sx={(theme) => ({
                      border: `1px solid ${theme.palette.divider}`,
                      borderRadius: '4px',
                    })}
                  >
                    <ExpandMoreIcon
                      fontSize="small"
                      sx={{
                        transition: 'transform 200ms ease',
                        transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
                      }}
                    />
                  </IconButton>
                )}
              </Stack>
            </Stack>

            {/* -- Prices panel -- */}
            {hasPrices && (
              <Collapse in={expanded} unmountOnExit>
                <Box
                  sx={(theme) => ({
                    mt: 1.5,
                    border: `1px solid ${theme.palette.divider}`,
                    borderRadius: '4px',
                    overflow: 'hidden',
                  })}
                >
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 600 }}>
                          {t('events.priceType', 'Type')}
                        </TableCell>
                        <TableCell align="right" sx={{ fontWeight: 600 }}>
                          {t('events.price', 'Prijs')}
                        </TableCell>
                        <TableCell align="right" sx={{ fontWeight: 600 }}>
                          {t('events.available', 'Beschikbaar')}
                        </TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {event.prices.map((p) => (
                        <TableRow key={p.id} hover>
                          <TableCell>{p.price?.description?.[lang] || p.price_display}</TableCell>
                          <TableCell align="right">
                            <Typography variant="body2">
                              €{Number(p.amount).toFixed(2)}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2" color="text.secondary">
                              {p.available ?? '-'}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </Box>
              </Collapse>
            )}
          </Box>
        )
      })}
    </Stack>
  )
}
