import { get, writable, type Writable } from 'svelte/store';

import type { PlotOptions } from '../scicharts/baseplot';


const option_store_inner: Writable<Writable<PlotOptions>[]> = writable([]);

export const option_store = Object.assign(option_store_inner, {
    add_option: ((option: PlotOptions) => {
        option_store_inner.update((option_store_list) => {
            option_store_list.push(writable(option));
            return option_store_list;
        });
    }),
    remove_option_at: ((idx: number) => {
        option_store_inner.update((option_store_list) => {
            if (idx < 0 || idx >= option_store_list.length) {
                throw new Error(`Index ${idx} out of range`);
            }
            option_store_list.splice(idx, 1);
            return option_store_list;
        });  
    }),
    update_option_at: ((idx: number, option: PlotOptions) => {
        option_store_inner.update((option_store_list) => {
            if (idx < 0 || idx >= option_store_list.length) {
                throw new Error(`Index ${idx} out of range`);
            }
            option_store_list[idx]?.set(option);
            return option_store_list;
        });
    }),
    count: (() => get(option_store_inner).length),
    get_store_at: ((idx: number) => {
        if (idx < 0 || idx >= get(option_store_inner).length) {
            throw new Error(`Index ${idx} out of range`);
        }
        return get(option_store_inner)[idx];
    }),
    /**
     * This is a hack to force all subscribers to update.
     */
    update_all_subscribers: (() => {
        option_store_inner.update((option_store_list) => {
            option_store_list.forEach((option_store) => {
                option_store.update((option) => option);
            });
            return option_store_list;
        });
    })
});


export const selected_index_store = writable(-1);