import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { copyFileSync } from 'node:fs'
import { resolve } from 'node:path'

const syncLegacyWidget = () => ({
  name: 'sync-legacy-widget',
  closeBundle() {
    copyFileSync(
      resolve('dist/widget.js'),
      resolve('../public/service-rag-widget.js'),
    )
  },
})

// Builds the embeddable <script src="widget.js"> bundle, separate
// from the normal `vite build` (which builds the standalone
// dist/index.html app). Run AFTER the normal build so widget.js
// lands alongside it in the same dist/ folder without wiping it
// (emptyOutDir stays false here on purpose).
export default defineConfig({
  plugins: [react(), syncLegacyWidget()],
  build: {
    outDir: 'dist',
    emptyOutDir: false,
    cssCodeSplit: false,
    lib: {
      entry: 'src/widget-entry.tsx',
      name: 'RAGWidget',
      formats: ['iife'],
      fileName: () => 'widget.js',
    },
    rollupOptions: {
      output: {
        inlineDynamicImports: true,
        // Injected before any bundled code runs, so libraries that
        // check `process.env.NODE_ENV` (React, etc.) don't crash
        // with "process is not defined" in the browser.
        banner: 'var process = { env: { NODE_ENV: "production" } };',
      },
    },
  },
  define: {
    'process.env.NODE_ENV': JSON.stringify('production'),
  },
})
