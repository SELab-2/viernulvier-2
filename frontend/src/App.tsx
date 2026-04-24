import { CssBaseline, ThemeProvider } from '@mui/material'
import { useMemo, useState } from 'react'

import Router from './router'
import { createAppTheme } from './theme/muiPalette'

import type { AppThemeMode } from './types/Theme'

const STORAGE_KEY = 'vnv-theme-mode'

// Restore the last selected mode on reload; default to light when unset.
const getInitialMode = (): AppThemeMode => {
  const saved = window.localStorage.getItem(STORAGE_KEY)
  return saved === 'dark' ? 'dark' : 'light'
}

const App = () => {
  const [mode, setMode] = useState<AppThemeMode>(getInitialMode)

  // Recreate the MUI theme only when mode changes.
  const theme = useMemo(() => createAppTheme(mode), [mode])

  // Update UI mode and persist it for future visits.
  const toggleMode = () => {
    setMode((previousMode) => {
      const nextMode = previousMode === 'light' ? 'dark' : 'light'
      window.localStorage.setItem(STORAGE_KEY, nextMode)
      return nextMode
    })
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router mode={mode} onToggleMode={toggleMode} />
    </ThemeProvider>
  )
}

export default App
