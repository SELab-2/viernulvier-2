import { ThemeProvider, createTheme } from '@mui/material/styles'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'

import { NotificationProvider } from '../../contexts/NotificationContext'
import { useNotification } from '../../contexts/notificationContextShared'

const NotificationHarness = () => {
  const { showFloatingAlert } = useNotification()

  return (
    <div>
      <button onClick={() => showFloatingAlert({ message: 'First notice' })}>show-first</button>
      <button onClick={() => showFloatingAlert({ message: 'Second notice' })}>show-second</button>
    </div>
  )
}

const LocationStateProbe = () => {
  const location = useLocation()
  const hasFloatingAlert = Boolean(
    (location.state as { floatingAlert?: { message?: string } } | null)?.floatingAlert,
  )

  return <div data-testid="has-floating-alert-state">{String(hasFloatingAlert)}</div>
}

type InitialEntry = string | { pathname: string; state?: unknown }

const renderWithProvider = (initialEntry: InitialEntry = '/') =>
  render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <ThemeProvider theme={createTheme()}>
        <NotificationProvider>
          <Routes>
            <Route
              path="*"
              element={
                <>
                  <NotificationHarness />
                  <LocationStateProbe />
                </>
              }
            />
          </Routes>
        </NotificationProvider>
      </ThemeProvider>
    </MemoryRouter>,
  )

describe('NotificationProvider', () => {
  it('shows multiple floating alerts and closes a lower alert independently', async () => {
    renderWithProvider()

    fireEvent.click(screen.getByText('show-first'))
    fireEvent.click(screen.getByText('show-second'))

    expect(screen.getByText('First notice')).toBeInTheDocument()
    expect(screen.getByText('Second notice')).toBeInTheDocument()

    const secondAlert = screen.getByText('Second notice').closest('[data-testid="floating-alert"]')
    expect(secondAlert).not.toBeNull()

    fireEvent.click(within(secondAlert as HTMLElement).getByRole('button', { name: /close/i }))

    expect(screen.getByText('First notice')).toBeInTheDocument()
    expect(screen.queryByText('Second notice')).not.toBeInTheDocument()
  })

  it('consumes navigation state alerts through the shared provider', async () => {
    renderWithProvider({
      pathname: '/',
      state: {
        floatingAlert: {
          open: true,
          message: 'Navigation notice',
        },
      },
    })

    expect(await screen.findByText('Navigation notice')).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByTestId('has-floating-alert-state')).toHaveTextContent('false')
    })
  })
})
