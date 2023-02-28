import type { NumberArray } from 'scichart';

export interface Updatable {
	/**
	 * Updates the plots.
	 * @param x - The x values.
	 * @param y - The y values.
	 * @returns void
	 */
	update(x: NumberArray, y: NumberArray | NumberArray[]): void;
}

export interface Deletable {
	/**
	 * Deletes to free up web assembly memory.
	 * @returns void
	 */
	delete(): void;
}
