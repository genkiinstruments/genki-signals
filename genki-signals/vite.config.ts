import path from 'path';
import vue from '@vitejs/plugin-vue';
import { sveltekit } from '@sveltejs/kit/vite';
// import autoPreprocess from 'svelte-preprocess';
import { defineConfig } from 'vitest/config';

export default defineConfig({
	plugins: [sveltekit(), vue()],

	test: {
		include: ['src/**/*.{test,spec}.{js,ts}']
	},
	// build: {
	// 	target: 'es2015',
	// 	lib: {
	// 		entry: path.resolve(__dirname, 'src/routes/scichart/scichart.js'),
	// 		formats: ['es'],
	// 		fileName: 'bundle'
	// 	},
	// 	outDir: path.resolve(__dirname, 'build')
	// },
	server: {
		fs: {
			allow: ['..']
		}
	}
});
