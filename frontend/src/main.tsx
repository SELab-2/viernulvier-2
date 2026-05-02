import React from 'react'
import ReactDOM from 'react-dom/client'

import App from './App'
import './i18n'
// defer loading of the global CSS to avoid render-blocking
// use import.meta.url so the URL resolves correctly in dev and build
function loadIndexCssDeferred() {
  const { href } = new URL('./index.css', import.meta.url)
  const link = document.createElement('link')
  // preload first, then switch to stylesheet on load to apply styles
  link.rel = 'preload'
  ;(link as any).as = 'style'
  link.href = href
  link.onload = () => {
    link.rel = 'stylesheet'
    // clear the onload handler
    link.onload = null
  }
  document.head.appendChild(link)
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

// load CSS after initial render to defer blocking
loadIndexCssDeferred()
