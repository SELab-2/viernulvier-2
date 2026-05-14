export const DarkMode = 'dark'
export const LightMode = 'light'

/**
 * Union type representing all supported theme modes.
 */
export type AppThemeMode = typeof DarkMode | typeof LightMode

/**
 * Props for a theme mode toggle component.
 */
export type ModeToggleProps = {
  /** Current active theme mode. */
  mode: AppThemeMode

  /** Callback triggered when the user toggles the theme mode. */
  onToggleMode: () => void
}