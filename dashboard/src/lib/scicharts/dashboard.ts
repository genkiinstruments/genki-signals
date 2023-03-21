import { get, writable, type Writable } from 'svelte/store';

import { Line, get_default_line_plot_options } from "./line";
import { Trace, get_default_trace_plot_options } from "./trace";
import { Bar, get_default_bar_plot_options } from "./bar";
import { Spectrogram, get_default_spectrogram_plot_options } from "./spectrogram";
import { ELayoutMode, layout_factory } from "./layouts";

import type { Layout } from "./layouts";
import type { BasePlot } from "./baseplot"
import type { ArrayDict } from "./data";
import type { IUpdatable, IDeletable } from "./interfaces";


import type { SciChartSurface, TSciChart } from "scichart";
import { sub_surface_options } from "$lib/utils/helpers";

export class Dashboard implements IUpdatable, IDeletable, Iterable<BasePlot> {
    private scichart_surface: SciChartSurface | null = null;
    private wasm_context: TSciChart | null = null;

    private layout: Layout;
    public plot_store: Writable<BasePlot[]> = writable([]);

    constructor(scichart_surface: SciChartSurface, wasm_context: TSciChart, layout_mode: ELayoutMode = ELayoutMode.DynamicGrid) {
        this.scichart_surface = scichart_surface;
        this.wasm_context = wasm_context;
        this.layout = layout_factory(layout_mode);
    }

    /**
     * 
     * @param type - The type of plot to add.
     * @param at - The index to add the plot at. If -1, the plot is added at the end.
    */
    public add_plot(type: string, at: number = -1) {
        if (this.scichart_surface === null || this.wasm_context === null) {
            throw new Error("Not linked to SciChartSurface.");
        }
        
        let plot: BasePlot;
        const sub_surface = this.scichart_surface.addSubChart(sub_surface_options);
        switch (type) {
            case "line":
                plot = new Line(this.wasm_context, sub_surface, get_default_line_plot_options());
                break;
            case "trace":
                plot = new Trace(this.wasm_context, sub_surface, get_default_trace_plot_options());
                break;
            case "bar":
                plot = new Bar(this.wasm_context, sub_surface, get_default_bar_plot_options());
                break;
            case "spectrogram":
                plot = new Spectrogram(this.wasm_context, sub_surface, get_default_spectrogram_plot_options());
                break;
            default:
                throw new Error("Unknown plot type: " + type);
        }

        this.plot_store.update((plots) => {
            if (at === -1) {
                plots.push(plot);
            } else {
                plots.splice(at, 0, plot);
            }
            return plots;
        });

        this.update_layout();
    }

    /**
     * Change the layout of the dashboard which automatically updates.
     * @param mode - The layout mode to use.
     */
    public set_layout_mode(mode: ELayoutMode) {
        this.layout = layout_factory(mode);
        this.update_layout();
    }

    private update_layout() {
        this.layout.apply_layout(get(this.plot_store));
    }

    // TODO: Make this use id instead of index
    /**
     * @param at - The index of the plot to remove. If -1, the last plot is removed.
     */
    public remove_plot(at: number = -1) {
        this.plot_store.update((plots) => {
            if (at === -1) at = plots.length - 1;
            if (at < 0 || at >= plots.length) {
                throw new Error(`Index ${at} not in range [0, ${plots.length})`);
            }
            plots[at]?.delete();
            plots.splice(at, 1);
            return plots;
        });
        this.update_layout();
    }


    // ################################## Interface implementations ##################################


    public update(data: ArrayDict): void {
        get(this.plot_store).forEach((plot) => plot.update(data));
    }

    public delete(): void {
        get(this.plot_store).forEach((plot) => plot.delete());
        this.scichart_surface.delete();
    }

    [Symbol.iterator](): Iterator<BasePlot> {
        let index = 0;
        const plots = get(this.plot_store);

        return {
            next: function (): IteratorResult<BasePlot> {
                if (index < plots.length) {
                    return { value: plots[index++], done: false } as IteratorResult<BasePlot>;
                } else {
                    return { value: undefined as any, done: true };
                }
            },
        };
    }
}