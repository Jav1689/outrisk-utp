import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const proxyTarget = env.OUTRISK_API_URL || 'http://127.0.0.1:8000'
  const proxy = {
    '/api': {
      target: proxyTarget,
      changeOrigin: true,
    },
  }

  return {
    plugins: [react(), tailwindcss()],
    server: {
      proxy,
      allowedHosts: [
        "chrome-broadways-send.ngrok-free.dev"
      ]
    },
    preview: { proxy },
  }
})
