import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
    base: '/livekit/',
    plugins: [react()],
    server: {
        host: true, // Escucha en TODAS las interfaces (0.0.0.0) para la red local
        allowedHosts: true, // Permitir conexiones desde cloudflared
        proxy: {
            '/api': {
                target: 'http://127.0.0.1:8081',
                changeOrigin: true,
            }
        }
    }
})
