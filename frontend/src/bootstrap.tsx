import React from 'react'
import ReactDOM from 'react-dom/client'

// Minimal bootstrap: render a lightweight root and then dynamically import the
// full application entry (main.tsx) during an idle window / after first paint.
// This avoids downloading and parsing large app bundles before the page is
// visible and reduces bytes consumed during the initial navigation.

function mountShell() {
  const rootEl = document.getElementById('root')!
  // Render an empty StrictMode shell so the page can paint quickly.
  ReactDOM.createRoot(rootEl).render(
    <React.StrictMode>
      {/* intentionally empty; main.tsx will re-render the real App */}
    </React.StrictMode>,
  )
}

mountShell()

function scheduleAppLoad(cb: () => void) {
  if ('requestIdleCallback' in window) {
    ;(window as any).requestIdleCallback(cb, { timeout: 1500 })
  } else if ('requestAnimationFrame' in window) {
    requestAnimationFrame(() => setTimeout(cb, 0))
  } else {
    setTimeout(cb, 0)
  }
}

scheduleAppLoad(() => {
  // Dynamically import the existing main entry. When imported it will run the
  // existing logic (load CSS deferred and render <App />). This delays network
  // fetch and execution of the main bundle until the browser is idle.
  void import('./main')
})
