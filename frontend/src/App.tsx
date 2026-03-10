import { useMemo, useState } from 'react'
import { CssBaseline, ThemeProvider, createTheme } from '@mui/material'
import Router from './router'

const STORAGE_KEY = 'vnv-theme-mode'

// Restore the last selected mode on reload; default to light when unset.
const getInitialMode = (): 'light' | 'dark' => {
  const saved = window.localStorage.getItem(STORAGE_KEY)
  return saved === 'dark' ? 'dark' : 'light'
}

const App = () => {
  const [mode, setMode] = useState<'light' | 'dark'>(getInitialMode)

  // Recreate the MUI theme only when mode changes.
  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode,
        },
      }),
    [mode],
  )

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
