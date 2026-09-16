import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  base: 'https://aminoy77.github.io/HelloChusquis/',
  plugins: [react()],
  build: { outDir: 'dist', emptyOutDir: true }
});
