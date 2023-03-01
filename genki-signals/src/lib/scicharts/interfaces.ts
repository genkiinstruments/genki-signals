import type { ArrayDict } from './types';

export interface Updatable {
	/**
	 * Updates accordingly, given the data.
	 * @returns void
	 */
	update(data: ArrayDict): void;
};

export interface Deletable {
	/**
	 * Deletes to free up web assembly memory.
	 * @returns void
	 */
	delete(): void;
};