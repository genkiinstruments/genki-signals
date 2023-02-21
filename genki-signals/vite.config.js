import path from 'path';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vitest/config';
import copy from 'rollup-plugin-copy';

export default defineConfig({
	plugins: [
		sveltekit(),
		copy({
			targets: [
				{ src: 'node_modules/scichart/_wasm/scichart2d.data', dest: '' },
				{ src: 'node_modules/scichart/_wasm/scichart2d.wasm', dest: '' },
			],
		}),
	],
	
	test: {
		include: ['src/**/*.{test,spec}.{js,ts}']
	},
	dev: {

	},
	build: {
		target: 'es2015',
		lib: {
			entry: path.resolve(__dirname, 'src/routes/scichart/scichart.js'),
			formats: ['es'],
			fileName: 'bundle',
		},
		outDir: path.resolve(__dirname, 'build'),
	},
	server: {
		fs: {
			allow: ['..'],
		},
	},
});