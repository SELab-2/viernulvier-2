import react from '@vitejs/plugin-react'
import path from 'path'
import { defineConfig, loadEnv } from 'vite'

export default ({ mode }) => {
  const envDir = path.resolve(import.meta.dirname, '../infrastructure')
  const env = loadEnv(mode, envDir, 'PUBLIC_')

  return defineConfig({
    plugins: [react()],
    envDir: envDir,
    envPrefix: 'PUBLIC_',
    define: {
      'process.env.PUBLIC_API_KEY': JSON.stringify(env.PUBLIC_API_KEY),
    },
    server: {
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
        '/admin': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
        '/static': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
        '^/media/.*': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
  })
}
