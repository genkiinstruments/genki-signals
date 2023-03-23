import { Dashboard } from "./dashboard";

import { get, writable, type Writable } from 'svelte/store';

import { ELayoutMode } from "./layouts";

import type { BasePlot } from "./baseplot"
import type { SciChartSurface, TSciChart } from "scichart";

export class SvelteDashboard extends Dashboard {
    plot_store: Writable<BasePlot[]>;

    constructor(scichart_surface: SciChartSurface, wasm_context: TSciChart, layout_mode: ELayoutMode = ELayoutMode.DynamicGrid) {
        super(scichart_surface, wasm_context, layout_mode);

        this.plot_store = writable(this.plots);
    }

    public override add_plot(type: string, at?: number): void {
        this.plot_store.update((plots) => {
            super.add_plot(type, at);
            return this.plots
        });
    }

    public override remove_plot(at?: number): void {
        this.plot_store.update((plots) => {
            super.remove_plot(at);
            return this.plots
        });
    }
}