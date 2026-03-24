import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  // Load env file based on `mode` in the current working directory.
  const env = loadEnv(mode, process.cwd(), '')
  const rawTarget = env.VITE_BACKEND_URL || 'http://127.0.0.1:8000'
  const proxyTarget = rawTarget.replace(/^http:\/\/localhost(?=[:/]|$)/, 'http://127.0.0.1')
  
  return {
    plugins: [react()],
    server: {
      port: 3000,
      proxy: {
        '/api': {
          target: proxyTarget,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, '')
        }
      }
    }
  }
})

