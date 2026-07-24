import path from 'path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 35173,
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://app:8080',
        changeOrigin: true,
      },
      '/mcp': {
        target: process.env.VITE_API_URL || 'http://app:8080',
        changeOrigin: true,
      },
    },
  },
})
