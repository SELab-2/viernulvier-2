import CalendarTodayOutlinedIcon from '@mui/icons-material/CalendarTodayOutlined'
import EuroOutlinedIcon from '@mui/icons-material/EuroOutlined'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import RoomOutlinedIcon from '@mui/icons-material/RoomOutlined'
import ScheduleOutlinedIcon from '@mui/icons-material/ScheduleOutlined'
import {
  Box,
  Chip,
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

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleDateString(lang === 'nl' ? 'nl-BE' : 'en-GB', {
      weekday: 'short',
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    })

  const formatTime = (iso: string) =>
    new Date(iso).toLocaleTimeString(lang === 'nl' ? 'nl-BE' : 'en-GB', {
      hour: '2-digit',
      minute: '2-digit',
    })

  return (
    <Stack spacing={0} divider={<Divider />}>
      {events.map((event) => {
        const expanded = expandedIds.has(event.id)
        const hasPrices = event.prices?.length > 0

        return (
          <Box key={event.id}>
            {/* ── Event row ── */}
            <Stack
              direction="row"
              alignItems="center"
              justifyContent="space-between"
              sx={{ py: 1.5, px: 0 }}
            >
              <Stack spacing={0.5} sx={{ flex: 1, minWidth: 0 }}>
                {/* Date + time */}
                <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap">
                  <Stack direction="row" spacing={0.75} alignItems="center">
                    <CalendarTodayOutlinedIcon
                      sx={{ fontSize: '0.9rem', color: 'text.primary' }}
                    />
                    <Typography variant="body2" fontWeight={600} color="text.primary">
                      {event.starts_at ? formatDate(event.starts_at) : '—'}
                    </Typography>
                  </Stack>

                  {event.starts_at && (
                    <Stack direction="row" spacing={0.75} alignItems="center">
                      <ScheduleOutlinedIcon sx={{ fontSize: '0.9rem', color: 'text.primary' }} />
                      <Typography variant="body2" color="text.primary">
                        {formatTime(event.starts_at)}
                        {event.ends_at ? ` – ${formatTime(event.ends_at)}` : ''}
                      </Typography>
                    </Stack>
                  )}
                </Stack>

                {/* Venue */}
                {event.hall_display && (
                  <Stack direction="row" spacing={0.75} alignItems="center">
                    <RoomOutlinedIcon sx={{ fontSize: '0.9rem', color: 'text.primary' }} />
                    <Typography variant="body2" color="text.primary">
                      {event.hall_display}
                    </Typography>
                  </Stack>
                )}
              </Stack>

              {/* Prices summary chips + expand toggle */}
              <Stack
                direction="row"
                spacing={1}
                alignItems="center"
                sx={{ flexShrink: 0, ml: 2, minWidth: 0, maxWidth: { xs: '140px', sm: '220px', md: '280px' } }}
              >
                {hasPrices && (
                  <Stack
                    direction="row"
                    spacing={0.5}
                    flexWrap="nowrap"
                    sx={{
                      display: { xs: 'none', sm: 'flex' },
                      width: '100%',
                      overflowX: 'auto',
                      pr: 0.5,
                      '&::-webkit-scrollbar': { height: 4 },
                      '&::-webkit-scrollbar-thumb': {
                        backgroundColor: 'rgba(0,0,0,0.2)',
                        borderRadius: '2px',
                      },
                    }}
                  >
                    {event.prices.map((p) => (
                      <Chip
                        key={p.id}
                        icon={<EuroOutlinedIcon sx={{ fontSize: '0.75rem !important' }} />}
                        label={`${Number(p.amount).toFixed(2)}`}
                        size="small"
                        variant="outlined"
                        sx={{ fontSize: '0.75rem', height: 24, whiteSpace: 'nowrap' }}
                      />
                    ))}
                  </Stack>
                )}

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
                      transition: 'transform 200ms ease',
                      transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
                    })}
                  >
                    <ExpandMoreIcon fontSize="small" />
                  </IconButton>
                )}
              </Stack>
            </Stack>

            {/* ── Prices panel ── */}
            {hasPrices && (
              <Collapse in={expanded} unmountOnExit>
                <Box
                  sx={(theme) => ({
                    mb: 1.5,
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
                          <TableCell>{p.price_display}</TableCell>
                          <TableCell align="right">
                            <Typography variant="body2" fontWeight={600}>
                              €{Number(p.amount).toFixed(2)}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2" color="text.secondary">
                              {p.available ?? '—'}
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