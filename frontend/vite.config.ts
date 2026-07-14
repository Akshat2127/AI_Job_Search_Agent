import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: { port: 3000, proxy: { '/jobs': 'http://localhost:8000', '/analytics': 'http://localhost:8000' } },
  test: { environment: 'jsdom', setupFiles: './src/test-setup.ts', restoreMocks: true },
})
