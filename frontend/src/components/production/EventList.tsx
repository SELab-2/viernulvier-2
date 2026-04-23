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

import { tokens } from '../../theme/tokens'
import { formatDate, formatTime } from '../../utils/dateUtils'
import { getHallDisplayName } from '../../utils/hall'

import type { Event } from '../../types/Events'

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
      <Typography variant="body2" sx={(theme) => ({ color: theme.palette.text.primary })}>
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
              sx={(theme) => ({
                alignItems: 'center',
                justifyContent: 'space-between',
                color: theme.palette.text.primary,
              })}
            >
              <Stack spacing={0.5} sx={{ flex: 1, minWidth: 0 }}>
                {/* Date + time */}
                <Stack direction="row" spacing={2} sx={{ alignItems: 'center', flexWrap: 'wrap' }}>
                  <Stack direction="row" spacing={0.75} sx={{ alignItems: 'center' }}>
                    <CalendarTodayOutlinedIcon sx={{ fontSize: '0.95rem' }} />
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {event.starts_at ? formatDate(event.starts_at, lang) : '—'}
                    </Typography>
                  </Stack>

                  {event.starts_at && (
                    <Stack direction="row" spacing={0.75} sx={{ alignItems: 'center' }}>
                      <ScheduleOutlinedIcon sx={{ fontSize: '0.95rem' }} />
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
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
                      <Stack direction="row" spacing={0.75} sx={{ alignItems: 'center' }}>
                        <RoomOutlinedIcon sx={{ fontSize: '0.9rem' }} />
                        <Typography variant="body2">{hallName}</Typography>
                      </Stack>
                    )
                  )
                })()}
              </Stack>

              {/* Expand prices toggle */}
              <Stack
                direction="row"
                spacing={1}
                sx={{ alignItems: 'center', flexShrink: 0, ml: 2 }}
              >
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
                      borderRadius: tokens.borderRadius.sm,
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
                    borderRadius: tokens.borderRadius.sm,
                    overflow: 'hidden',
                  })}
                >
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell sx={{ fontWeight: tokens.typography.weights.bold }}>
                          {t('events.priceType', 'Type')}
                        </TableCell>
                        <TableCell
                          align="right"
                          sx={{ fontWeight: tokens.typography.weights.bold }}
                        >
                          {t('events.price', 'Prijs')}
                        </TableCell>
                        <TableCell
                          align="right"
                          sx={{ fontWeight: tokens.typography.weights.bold }}
                        >
                          {t('events.available', 'Beschikbaar')}
                        </TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {event.prices.map((p) => (
                        <TableRow key={p.id} hover>
                          <TableCell>{p.price?.description?.[lang] || p.price_display}</TableCell>
                          <TableCell align="right">
                            <Typography variant="body2">€{Number(p.amount).toFixed(2)}</Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography
                              variant="body2"
                              sx={(theme) => ({
                                color:
                                  theme.palette.mode === 'dark'
                                    ? tokens.colors.dark.textMuted
                                    : tokens.colors.light.textMuted,
                              })}
                            >
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
