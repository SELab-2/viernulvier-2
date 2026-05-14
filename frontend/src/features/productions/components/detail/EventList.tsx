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

import { tokens } from '../../../../theme/tokens'
import { DarkMode } from '../../../../types/Theme'
import { formatDate, formatTime } from '../../../../utils/dateUtils'
import { getHallDisplayName } from '../../../../utils/hall'

import type { Event } from '../../../../types/Events'

interface EventsListProps {
  events: Event[]
}

/**
 * Renders the list of events for a production detail page.
 *
 * Design intent:
 * - Each event is displayed as a compact row with date, time, and venue
 * - Optional pricing information is hidden behind an expandable section
 * - Keeps the default UI minimal while still exposing detailed ticket info on demand
 *
 * Important behavior:
 * - Expand/collapse state is tracked per-event via a Set of event IDs
 * - Multiple events can be expanded at the same time
 */
export default function EventsList({ events }: EventsListProps) {
  const { t, i18n } = useTranslation()
  const lang = i18n.language

  // Tracks which event rows have their price table expanded
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set())

  // Empty-state handling: if no events exist, render a fallback message instead of table layout
  if (!events.length) {
    return (
      <Typography variant="body2" sx={(theme) => ({ color: theme.palette.text.primary })}>
        {t('productions.detail.noEvents', 'Geen geplande events.')}
      </Typography>
    )
  }

  /**
   * Toggles the expanded state for a given event.
   * Uses Set to avoid duplicates and allow efficient add/remove operations.
   */
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
            {/* Event row container: holds date/time/venue + optional expand button */}
            <Stack
              direction="row"
              sx={(theme) => ({
                alignItems: 'center',
                justifyContent: 'space-between',
                color: theme.palette.text.primary,
              })}
            >
              <Stack spacing={0.5} sx={{ flex: 1, minWidth: 0 }}>
                {/* Date + time block */}
                <Stack direction="row" spacing={2} sx={{ alignItems: 'center', flexWrap: 'wrap' }}>
                  {/* Event start date */}
                  <Stack direction="row" spacing={0.75} sx={{ alignItems: 'center' }}>
                    <CalendarTodayOutlinedIcon sx={{ fontSize: '0.95rem' }} />
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {event.starts_at ? formatDate(event.starts_at, lang) : '—'}
                    </Typography>
                  </Stack>

                  {/* Event time range (only shown if start exists) */}
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

                {/* Venue / hall display (only shown when available) */}
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

              {/* Right-side action area (expand prices if available) */}
              <Stack
                direction="row"
                spacing={1}
                sx={{ alignItems: 'center', flexShrink: 0, ml: 2 }}
              >
                {/* Only render toggle if price data exists */}
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
                    {/* Icon rotates to indicate expanded/collapsed state */}
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

            {/* Collapsible price table section */}
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
                    {/* Table header describing price structure */}
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

                    {/* Price rows per ticket type */}
                    <TableBody>
                      {event.prices.map((p) => (
                        <TableRow key={p.id} hover>
                          {/* Price category / description */}
                          <TableCell>{p.price?.description?.[lang] || p.price_display}</TableCell>

                          {/* Price value formatted as EUR */}
                          <TableCell align="right">
                            <Typography variant="body2">€{Number(p.amount).toFixed(2)}</Typography>
                          </TableCell>

                          {/* Availability indicator (can be null) */}
                          <TableCell align="right">
                            <Typography
                              variant="body2"
                              sx={(theme) => ({
                                color:
                                  theme.palette.mode === DarkMode
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
