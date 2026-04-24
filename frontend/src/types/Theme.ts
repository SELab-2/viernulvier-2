export const DarkMode = 'dark'
export const LightMode = 'light'
export type AppThemeMode = typeof DarkMode | typeof LightMode

export type ModeToggleProps = {
  mode: AppThemeMode
  onToggleMode: () => void
}
