import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

export default ({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return defineConfig({
    plugins: [react()],
    define: {
      'process.env.VITE_PUBLIC_API_KEY': JSON.stringify(env.VITE_PUBLIC_API_KEY ?? ''),
    },
    // server: {
    //   proxy: {
    //     '/api': {
    //       target: 'http://localhost:8000',
    //       changeOrigin: true,
    //     },
    //     '/admin': {
    //       target: 'http://localhost:8000',
    //       changeOrigin: true,
    //     },
    //     '/static': {
    //       target: 'http://localhost:8000',
    //       changeOrigin: true,
    //     },
    //     '/media': {
    //       target: 'http://localhost:8000',
    //       changeOrigin: true,
    //     },
    //   },
    // },
    server: {
      proxy: {
        '/api': {
          target: 'https://sel2-2.ugent.be',
          changeOrigin: true,
          secure: true,
        },
        '/media': {
          target: 'https://sel2-2.ugent.be',
          changeOrigin: true,
          secure: true,
        },
        '/static': {
          target: 'https://sel2-2.ugent.be',
          changeOrigin: true,
          secure: true,
        },
      },
    },
  })
}
