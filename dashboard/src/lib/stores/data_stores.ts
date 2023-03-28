import { writable, type Writable } from 'svelte/store';


export type IndexRanges = {
    [key: string]: number
}

export type Argument = {
    name: string,
    type: string,
    value: any,
    sig_idx?: string,
}

export type DerivedSignal = {
    sig_name: string,
    args: Argument[],
}

export const data_keys_store: Writable<string[]> = writable([]);

export const data_idxs_store: Writable<IndexRanges> = writable({} as IndexRanges);

export const derived_signal_store: Writable<DerivedSignal[]> = writable([])