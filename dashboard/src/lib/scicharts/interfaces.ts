export interface IArrayDict {
	[key: string]: number[][];
}

export interface IUpdatable {
	/**
	 * Updates accordingly, given the data.
	 * @returns void
	 */
	update(data: IArrayDict): void;
}

export interface IDeletable {
	/**
	 * Deletes to free up web assembly memory.
	 * @returns void
	 */
	delete(): void;
}