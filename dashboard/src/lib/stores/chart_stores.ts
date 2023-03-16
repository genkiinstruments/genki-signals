import { get, writable, type Writable } from 'svelte/store';

import type { SubChart } from '$lib/scicharts/subchart';


const inner_subchart_store: Writable<SubChart[]> = writable([]);

export const chart_store = Object.assign(inner_subchart_store, {
    add_chart: ((chart: SubChart) => {
        inner_subchart_store.update((subcharts) => {
            subcharts.push(chart);
            return subcharts;
        });
    }),
    remove_chart: ((chart: SubChart) => {
        inner_subchart_store.update((subcharts) => {
            const idx = subcharts.indexOf(chart);
            if (idx < 0) {
                throw new Error(`Chart not found`);
            }
            subcharts.splice(idx, 1);
            return subcharts;
        });
    }), 
    remove_chart_at: ((idx: number) => {
        inner_subchart_store.update((subcharts) => {
            if (idx < 0 || idx >= subcharts.length) {
                throw new Error(`Index ${idx} out of range`);
            }
            subcharts.splice(idx, 1);
            return subcharts;
        });  
    }),
    count: (() => get(inner_subchart_store).length),
    get_subchart_at: ((idx: number) => {
        if (idx < 0 || idx >= get(inner_subchart_store).length) {
            throw new Error(`Index ${idx} out of range`);
        }
        return get(inner_subchart_store)[idx];
    }),
    /**
     * This is a hack to force all subscribers to update.
     */
    update_all_subscribers: (() => {
        inner_subchart_store.update((subcharts) => {
            subcharts.forEach((option_store) => {
                option_store.update((option) => option);
            });
            return subcharts;
        });
    })
});


export const selected_subchart_store = writable(-1);