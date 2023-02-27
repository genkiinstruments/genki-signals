import { EAutoRange, EAxisAlignment, NumberRange, NumericAxis, Rect, SciChartSubSurface } from 'scichart';
import { XyDataSeries } from 'scichart/Charting/Model/XyDataSeries.js';
import { createSubSurfaceOptions } from '../utils/subchart_helpers';
export const defaultSubChartOptions = {
    x_domain_max: null,
    x_domain_min: null,
    y_domain_max: null,
    y_domain_min: null,
    n_visible_points: 1000,
    x_axis_align: 'bottom',
    y_axis_align: 'left',
    x_axis_flipped: false,
    y_axis_flipped: false,
    x_axis_visible: true,
    y_axis_visible: true,
    data_contains_nan: false,
    data_is_sorted: true
};
/**
 * An abstract base class for all subcharts.
 * @class
 * @param id - The id of the subchart.
 * @param parent_surface - The parent sciChartSurface.
 * @param wasm_context - The wasm context.
 * @param rect - The rect defining where to place the subchart on the parent surface.
 * @param options - Options describing the subcharts domain, axes etc.
 */
export class SubChart {
    constructor(id, parent_surface, wasm_context, rect, options = defaultSubChartOptions) {
        this.id = id;
        this.parent_surface = parent_surface;
        this.wasm_context = wasm_context;
        this.rect = rect;
        this.options = options;
        this.sub_chart_surface = this.parent_surface.addSubChart(createSubSurfaceOptions(this.id, this.rect));
        this.x_axes = [];
        this.y_axes = [];
        // All series should have the same x-values
        this.data_series_list = [];
    }
    create_data_series(n) {
        this.data_series_list = Array(n)
            .fill(null)
            .map(() => {
            const dataSeries = new XyDataSeries(this.wasm_context);
            dataSeries.containsNaN = this.options.data_contains_nan;
            dataSeries.isSorted = this.options.data_is_sorted;
            return dataSeries;
        });
    }
    delete_data_series() {
        this.data_series_list.forEach((dataSeries) => dataSeries.delete());
        this.data_series_list = [];
    }
    /**
     * Each dataSeries should contain the same x-values, so we use the first one.
     */
    _get_native_x(i) {
        if (i < 0) {
            const x_count = this.data_series_list[0].count();
            return this.data_series_list[0].getNativeXValues().get(x_count + i); // + (negative number)
        }
        return this.data_series_list[0].getNativeXValues().get(i);
    }
    update_axes_domains(x_axis, y_axis) {
        let x_max, x_min;
        if (this.options.x_domain_max === null) {
            x_max = this._get_native_x(-1);
        }
        if (this.options.x_domain_min === null) {
            x_min = this._get_native_x(-this.options.n_visible_points);
        }
        x_axis.visibleRange = new NumberRange(x_min, x_max);
        if (this.options.y_domain_max === null && this.options.y_domain_min === null) {
            y_axis.autoRange = EAutoRange.Always;
        }
        else if (this.options.y_domain_max !== null && this.options.y_domain_min !== null) {
            y_axis.autoRange = EAutoRange.Never;
            y_axis.visibleRange = new NumberRange(this.options.y_domain_min, this.options.y_domain_max);
        }
        else {
            throw new Error('Both y_max and y_min must be null or not null.');
        }
        // TODO: if not zoom / pan then update the visible range
    }
    update_axes_alignment(x_axis, y_axis) {
        switch (this.options.x_axis_align) {
            case 'top':
                x_axis.axisAlignment = EAxisAlignment.Top;
                break;
            case 'bottom':
                x_axis.axisAlignment = EAxisAlignment.Bottom;
                break;
            default:
                throw new Error(`Invalid x-axis alignment: ${this.options.x_axis_align}`);
        }
        switch (this.options.y_axis_align) {
            case 'left':
                y_axis.axisAlignment = EAxisAlignment.Left;
                break;
            case 'right':
                y_axis.axisAlignment = EAxisAlignment.Right;
                break;
            default:
                throw new Error(`Invalid y-axis alignment: ${this.options.y_axis_align}`);
        }
    }
    update_axes_flipping(x_axis, y_axis) {
        x_axis.flippedCoordinates = this.options.x_axis_flipped;
        y_axis.flippedCoordinates = this.options.y_axis_flipped;
    }
    update_position() {
        this.sub_chart_surface.subPosition = this.rect;
    }
    /**
     * Adds data to all the dataSeries in this subplot and updates the axes.
     */
    update_data_series(x_data, y_data_list) {
        if (y_data_list.length !== this.data_series_list.length) {
            throw new Error('The number of y_data_list arrays must match the number of dataSeries.');
        }
        this.data_series_list.forEach((series, index) => {
            series.appendRange(x_data, y_data_list[index]);
            // if (this.options.x_domain_max !== null && this.options.x_domain_min !== null) {
            //     if (series.count() > this.options.n_visible_points) {
            //         series.removeRange(0, series.count() - this.options.n_visible_points);
            //     }
            // }
        });
    }
    setAxesDomains(x_max, x_min, y_max, y_min) {
        this.options.x_domain_max = x_max;
        this.options.x_domain_min = x_min;
        this.options.y_domain_max = y_max;
        this.options.y_domain_min = y_min;
        for (let i = 0; i < this.x_axes.length; i++) {
            this.update_axes_domains(this.x_axes[i], this.y_axes[i]);
        }
    }
    setAxesAlignments(x_align, y_align) {
        this.options.x_axis_align = x_align;
        this.options.y_axis_align = y_align;
        for (let i = 0; i < this.x_axes.length; i++) {
            this.update_axes_alignment(this.x_axes[i], this.y_axes[i]);
        }
    }
    setAxesFlipped(x_axis_flipped, y_axis_flipped) {
        this.options.x_axis_flipped = x_axis_flipped;
        this.options.y_axis_flipped = y_axis_flipped;
        for (let i = 0; i < this.x_axes.length; i++) {
            this.update_axes_flipping(this.x_axes[i], this.y_axes[i]);
        }
    }
    setPosition(x, y, width, height) {
        this.rect = new Rect(x, y, width, height);
        this.update_position();
        // TODO: Finish this
    }
    update(x_data, y_data_list) {
        this.update_data_series(x_data, y_data_list);
        for (let i = 0; i < this.x_axes.length; i++) {
            this.update_axes_domains(this.x_axes[i], this.y_axes[i]);
        }
        // ...
    }
    delete() {
        this.delete_data_series();
        this.sub_chart_surface.delete();
        // ...
    }
}
//# sourceMappingURL=subchart.js.map