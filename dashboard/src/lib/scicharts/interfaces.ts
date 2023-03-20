import type { ArrayDict } from './types';

export interface IUpdatable {
	/**
	 * Updates accordingly, given the data.
	 * @returns void
	 */
	update(data: ArrayDict): void;
}

export interface IDeletable {
	/**
	 * Deletes to free up web assembly memory.
	 * @returns void
	 */
	delete(): void;
}
