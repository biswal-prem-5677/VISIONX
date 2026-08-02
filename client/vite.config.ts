import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Backend origin for the dev proxy. Override with VISIONX_API_ORIGIN when the
// API runs somewhere other than localhost:8000.
const API_ORIGIN = process.env.VISIONX_API_ORIGIN || 'http://localhost:8000';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Dev proxy: the app talks to same-origin /api and /ws paths in every
  // environment. Without this, `useVisionStream` dials ws://localhost:5173/ws/vision
  // (the Vite server) and the live feed silently never connects.
  // Mirrors the production routing in docker/nginx.conf.
  server: {
    proxy: {
      '/api': {
        target: API_ORIGIN,
        changeOrigin: true,
      },
      '/ws': {
        target: API_ORIGIN,
        ws: true,
        changeOrigin: true,
      },
    },
  },
  build: {
    chunkSizeWarningLimit: 800,
    rollupOptions: {
      output: {
        manualChunks(id: string) {
          if (id.includes('node_modules/three') || id.includes('@react-three')) {
            return 'vendor-three';
          }
          if (id.includes('framer-motion')) {
            return 'vendor-motion';
          }
          if (id.includes('node_modules/react')) {
            return 'vendor-react';
          }
        },
      },
    },
  },
})
