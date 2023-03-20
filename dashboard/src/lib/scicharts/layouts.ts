import { Rect } from "scichart";

import { get_position_index } from "../utils/helpers";
import type { BasePlot } from "./baseplot";

export enum ELayoutMode {
    FixedGrid = "FixedGrid",
    DynamicGrid = "DynamicGrid",
    Custom = "Custom"
}

export abstract class Layout {
    public abstract apply_layout(plots: BasePlot[]): void;
}

class FixedGridLayout extends Layout {
    private rects: Rect[];

    constructor(n_columns: number, n_rows: number) {
        super();

        this.rects = Array(n_rows * n_columns).map((_, i) => {
            const { row_idx, col_idx } = get_position_index(n_columns, i);
            const top = row_idx / n_rows;
            const left = col_idx / n_columns;
            const width = 1 / n_columns;
            const height = 1 / n_rows;
            return new Rect(left, top, width, height);
        });
    }

    public apply_layout(plots: BasePlot[]): void {
        plots.forEach((plot, i) => {
            const rect = this.rects[i % this.rects.length];
            if (rect === undefined) { throw new Error(`Rect at index ${i} is undefined`); }
            plot.surface.subPosition = rect
        })
    }

}

class DynamicGridLayout extends Layout {
    public apply_layout(plots: BasePlot[]): void {
        const n_plots: number = plots.length;
        const n_columns = Math.ceil(Math.sqrt(n_plots));

        // coordinate system is [0, 1] x [0, 1]
        const width = 1 / n_columns; 
        const height = 1 / Math.ceil(n_plots / n_columns);

        plots.forEach((plot, i) => {
            const { row_idx, col_idx } = get_position_index(n_columns, i);
            const top = row_idx * height;
            const left = col_idx * width;
            const rect = new Rect(left, top, width, height);
            plot.surface.subPosition = rect;
        });
    }
}

/**
 * Works similarly to FixedGridLayout
 * but the rects are provided by the user.
 */
class CustomGridLayout extends Layout {
    private rects: Rect[];

    constructor(rects: Rect[]) {
        super();
        this.rects = rects;
    }

    public apply_layout(plots: BasePlot[]): void {
        throw new Error("Not implemented");
    }
}


export function layout_factory(mode: ELayoutMode): Layout {
    switch (mode) {
        case ELayoutMode.FixedGrid:
            return new FixedGridLayout(2, 2);
        case ELayoutMode.DynamicGrid:
            return new DynamicGridLayout();
        case ELayoutMode.Custom:
            throw new Error("Not implemented");
        default:
            throw new Error("Unknown layout mode: " + mode);
    }
}
