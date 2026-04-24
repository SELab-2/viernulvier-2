export type AppThemeMode = 'light' | 'dark'

export type ModeToggleProps = {
  mode: AppThemeMode
  onToggleMode: () => void
}
