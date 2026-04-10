import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// 本地开发用 '/'，GitHub Pages 部署时用 '/仓库名/'
// deploy.sh 会通过环境变量 VITE_BASE_PATH 覆盖
const base = process.env.VITE_BASE_PATH ?? '/'

export default defineConfig({
  plugins: [react()],
  base,
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
