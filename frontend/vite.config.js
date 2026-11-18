import { fileURLToPath, URL } from 'node:url'
import { resolve } from 'node:path'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import wasm from 'vite-plugin-wasm'

const root = fileURLToPath(new URL('.', import.meta.url))

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue({
      template: {
        compilerOptions: {
          compatConfig: {
            MODE: 2
          }
        }
      }
    }),
    vueDevTools(),
    wasm(),
  ],
  resolve: {
    alias: {
      vue: '@vue/compat',
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      // The protocol's browser client, used from the submodule as it stands.
      'viewcam-proto': fileURLToPath(new URL('../viewarr-workspace/viewcam-proto/js/viewcam_proto.js', import.meta.url)),
    },
  },
  build: {
    rollupOptions: {
      input: {
        main: resolve(root, 'index.html'),
        viewer: resolve(root, 'viewer.html'),
        camera: resolve(root, 'camera.html'),
      },
    },
  },
  optimizeDeps: {
    exclude: ['viewarr', 'viewcam', 'viewcam-codec'],
  },
  // viewcam-codec's decode worker is an ES module.
  worker: {
    format: 'es',
  },
  server: {
    allowedHosts: ["exao1.magao-x.org"],
    fs: {
      allow: ['..'],
    },
  }
})
