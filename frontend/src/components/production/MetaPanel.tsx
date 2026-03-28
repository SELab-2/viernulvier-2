import { useTheme } from '@mui/material'
import { useTranslation } from 'react-i18next'
import Tag from '../Tag'

import type { CSSProperties } from 'react'

interface MetaPanelProps {
  title: string
  tagline: string
  artistName: string
  dateRange: string
  venues: string
  genres: string
  typeName: string
  performerType: 'group' | 'solo' | ''
  attendanceMode: 'offline' | 'online' | ''
  allTags: string[]
  style?: CSSProperties
}

function MetaRow({ label, value }: { label: string; value: string }) {
  const theme = useTheme()
  if (!value) return null
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '140px 1fr',
        gap: '8px',
        padding: '14px 0',
        borderBottom: `1px solid ${theme.palette.divider}`,
        alignItems: 'start',
      }}
    >
      <span
        style={{
          color: theme.palette.text.secondary,
          fontSize: '0.95rem',
          paddingTop: '2px',
          fontWeight: 600,
        }}
      >
        {label}
      </span>
      <span style={{ fontSize: '0.92rem', color: theme.palette.text.primary, fontWeight: 500 }}>
        {value}
      </span>
    </div>
  )
}

export default function MetaPanel({
  title,
  tagline,
  artistName,
  dateRange,
  venues,
  genres,
  typeName,
  performerType,
  attendanceMode,
  allTags,
  style,
}: MetaPanelProps) {
  const theme = useTheme()
  const { t } = useTranslation()

  return (
    <div
      className="meta-panel"
      style={{
        paddingTop: '32px',
        background: theme.palette.background.paper,
        color: theme.palette.text.primary,
        ...style,
      }}
    >
      <h1
        style={{
          fontSize: '2rem',
          fontWeight: 700,
          lineHeight: 1.15,
          margin: '0 0 8px',
          letterSpacing: '-0.02em',
        }}
      >
        {title}
      </h1>

      {(tagline || artistName) && (
        <p
          style={{
            fontSize: '0.95rem',
            color: theme.palette.text.secondary,
            margin: '0 0 24px',
            fontStyle: 'italic',
          }}
        >
          {tagline || artistName}
        </p>
      )}

      <div style={{ borderTop: '1px solid #ebebeb', marginBottom: '4px' }} />

      <div style={{ fontFamily: "'Helvetica Neue', Arial, sans-serif" }}>
        {dateRange && (
          <MetaRow label={t('productions.detail.meta.period', 'Periode')} value={dateRange} />
        )}
        {venues && (
          <MetaRow label={t('productions.detail.meta.venues', 'Locaties')} value={venues} />
        )}
        {genres && <MetaRow label={t('productions.detail.meta.genre', 'Genre')} value={genres} />}
        {typeName && <MetaRow label={t('productions.detail.meta.type', 'Type')} value={typeName} />}
        <MetaRow
          label={t('productions.detail.meta.performerType', 'Uitvoering')}
          value={
            performerType === 'group'
              ? t('productions.detail.meta.group', 'Groep')
              : performerType === 'solo'
                ? t('productions.detail.meta.solo', 'Solo')
                : ''
          }
        />
        <MetaRow
          label={t('productions.detail.meta.attendance', 'Aanwezigheid')}
          value={
            attendanceMode === 'offline'
              ? t('productions.detail.meta.offline', 'Fysiek')
              : attendanceMode === 'online'
                ? t('productions.detail.meta.online', 'Online')
                : ''
          }
        />
      </div>

      {allTags.length > 0 && (
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '8px',
            marginTop: '28px',
          }}
        >
          {allTags.map((tag, i) => (
            <Tag key={i} tagName={tag} context="description" />
          ))}
        </div>
      )}
    </div>
  )
}
