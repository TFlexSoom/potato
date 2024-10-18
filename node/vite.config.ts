// vite.config.ts
import { resolve } from 'path'
import { defineConfig } from 'vite'
import nodePolyfills from '@emreerdogan/vite-plugin-node-stdlib-browser';

export default defineConfig
({
 build: {
   outDir: "live",
   lib: {
     // Could also be a dictionary or array of multiple entry points
     entry: resolve(__dirname, 'src/main.ts'),
     name: 'PotatoLib',
     // the proper extensions will be added
     fileName: 'potato',
   },
   rollupOptions: {
     output: {
       // Provide global variables to use in the UMD build
       // for externalized deps
       dir: "live",
       assetFileNames: "potato[extname]",
     },
   },
   
 },
 plugins: [
  nodePolyfills(),
 ]
})