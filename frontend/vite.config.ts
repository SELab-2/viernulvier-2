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
          target: 'https://sel2-2.ugent.be',
          changeOrigin: true,
        },
        '/admin': {
          target: 'https://sel2-2.ugent.be',
          changeOrigin: true,
        },
        '/static': {
          target: 'https://sel2-2.ugent.be',
          changeOrigin: true,
        },
        '/media': {
          target: 'https://sel2-2.ugent.be',
          changeOrigin: true,
        },
      },
    },
  })
}
