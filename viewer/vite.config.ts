import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [vue()],
  test: {
    coverage: {
      exclude: ['src/main.ts', 'src/vite-env.d.ts'],
      include: ['src/**/*.{ts,vue}'],
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      thresholds: {
        branches: 85,
        functions: 85,
        lines: 85,
        statements: 85,
      },
    },
    environment: 'jsdom',
    globals: true,
  },
})
