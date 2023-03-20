import { get, writable, type Writable } from 'svelte/store';

import { SubChart } from '$lib/scicharts/subchart';

import type { TSciChart, SciChartSurface, Rect } from 'scichart';
import type { PlotOptions } from '$lib/scicharts/baseplot';

/**
 * Possibly stupid, what if we open and close the page a lot? (i.e. do we get a new sciChartSurface every time?)
 */
export class SubChartSingleton {
    private subchart_store: Writable<SubChart[]>;
    
    private wasm_context: TSciChart | undefined = undefined;
    private scichart_surface: SciChartSurface | undefined = undefined;

    constructor() {
        this.subchart_store = writable([]);
    }

    public link_to_scichart_surface(scichart_surface: SciChartSurface, wasm_context: TSciChart) {
        this.scichart_surface = scichart_surface;
        this.wasm_context = wasm_context;
    }

    public create_chart(id: string, rect: Rect, options: PlotOptions) {
        if (this.wasm_context === undefined || this.scichart_surface === undefined) {
            throw new Error('SubChartStore not linked to a SciChartSurface and a WasmContext');
        }

        const chart = new SubChart(id, this.scichart_surface, this.wasm_context, rect, options);
        this.subchart_store.update((subcharts) => {
            subcharts.push(chart);
            return subcharts;
        });
    }

    public remove_chart_at(idx: number) {
        this.subchart_store.update((subcharts) => {
            if (idx < 0 || idx >= subcharts.length) {
                throw new Error(`Index ${idx} out of range`);
            }
            subcharts.splice(idx, 1);
            return subcharts;
        });
    }

    public update_position_at(idx: number, rect: Rect) {
        if (idx < 0 || idx >= get(this.subchart_store).length) {
            throw new Error(`Index ${idx} out of range`);
        }
        get(this.subchart_store)[idx]?.set_position(rect);
    }

    public update_all_positions(rects: Rect[]) {
        if (rects.length !== get(this.subchart_store).length) {
            throw new Error('Number of rects does not match number of subcharts');
        }
        get(this.subchart_store).forEach((subchart, idx) => {
            const rect = rects[idx];
            if (rect === undefined) {
                throw new Error(`Rect at index ${idx} is undefined`);
            }
            subchart.set_position(rect);
        });
    }

    public get_subchart_at(idx: number) {
        if (idx < 0 || idx >= get(this.subchart_store).length) {
            throw new Error(`Index ${idx} out of range`);
        }
        return get(this.subchart_store)[idx];
    }

    public get_store() { return this.subchart_store; }
    public count() { return get(this.subchart_store).length; }
    public update_all_subscribers() { this.subchart_store.update((subcharts) => { return subcharts; }); }
}


export const subchart_store = new SubChartStore();

export const selected_subchart_store = writable(-1);
