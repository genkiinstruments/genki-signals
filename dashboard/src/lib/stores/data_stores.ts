import { writable, type Writable } from 'svelte/store';


export type IndexRanges = {
    [key: string]: number
}

export const data_keys_store: Writable<string[]> = writable([]);

export const data_idxs_store: Writable<IndexRanges> = writable({} as IndexRanges);