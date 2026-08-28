import react, {reactCompilerPreset} from '@vitejs/plugin-react'
import inertia from '@inertiajs/vite'
import babel from '@rolldown/plugin-babel'
import {defineConfig} from 'vite'
import {resolve} from "path";
import tailwindcss from "@tailwindcss/vite";

// https://vite.dev/config/
export default defineConfig({
    base: "/static/",
    plugins: [
        react(),
        inertia(),
        tailwindcss(),
        babel({presets: [reactCompilerPreset()]}),
    ],
    build: {
        manifest: "manifest.json",
        outDir: resolve("../assets"),
        rollupOptions: {
            input: {
                'main': './src/main.tsx'
            }
        },
    },
    resolve: {
        alias: {
            '@': resolve(__dirname, './src'),
        },
    },
})
