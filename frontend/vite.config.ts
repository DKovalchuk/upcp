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
      'cmdk': path.resolve(__dirname, './node_modules/cmdk/dist/index.mjs'),
    },
  },
  server: {
    port: 35173,
    host: '127.0.0.1',
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://127.0.0.1:38080',
        changeOrigin: true,
      },
      '/mcp': {
        target: process.env.VITE_API_URL || 'http://127.0.0.1:38080',
        changeOrigin: true,
      },
    },
  },
})
