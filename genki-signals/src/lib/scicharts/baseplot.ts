import { type NumberArray, type TSciChart, type AxisBase2D, type BaseRenderableSeries, type SciChartSubSurface, type SciChartSurface, type XyDataSeries, EAxisAlignment } from 'scichart';

import type { Deletable, Updatable, PlotOptions } from './interfaces';


export abstract class BasePlot implements Updatable, Deletable {
    protected wasm_context: TSciChart;
    protected surface: SciChartSubSurface | SciChartSurface;
    
    protected abstract renderable_series: BaseRenderableSeries;
    protected abstract x_axis: AxisBase2D;
    protected abstract y_axis: AxisBase2D;
    protected abstract data_series: XyDataSeries;
    public abstract options: PlotOptions;

    constructor(wasm_context: TSciChart, surface: SciChartSubSurface | SciChartSurface) {
        this.wasm_context = wasm_context;
        this.surface = surface;
    }

    /**
	 * @param i - The index of the data series. If i is negative, then the index is counted from the end.
	 * @returns The x-value at index i.
	*/
	protected _get_native_x(i: number): number {
		const x_values = this.data_series.getNativeXValues();
        
		if (i < 0) {
            const x_count = this.data_series.count();
			return x_values.get(x_count + i); // + (negative number)
		}
		return x_values.get(i);
	}

    protected update_axes_alignment(): void {
		switch (this.options.x_axis_align) {
			case 'top':
				this.x_axis.axisAlignment = EAxisAlignment.Top;
				break;
			case 'bottom':
				this.x_axis.axisAlignment = EAxisAlignment.Bottom;
				break;
			default:
				throw new Error(`Invalid x-axis alignment: ${this.options.x_axis_align}`);
		}
		switch (this.options.y_axis_align) {
			case 'left':
				this.y_axis.axisAlignment = EAxisAlignment.Left;
				break;
			case 'right':
				this.y_axis.axisAlignment = EAxisAlignment.Right;
				break;
			default:
				throw new Error(`Invalid y-axis alignment: ${this.options.y_axis_align}`);
		}
	}

    protected update_axes_flipping(): void {
		this.x_axis.flippedCoordinates = this.options.x_axis_flipped;
		this.y_axis.flippedCoordinates = this.options.y_axis_flipped;
	}

    // TODO: abstract set_options instead?
    public set_axis_alignment(x_align: 'top' | 'bottom', y_align: 'left' | 'right'): void {
		this.options.x_axis_align = x_align;
		this.options.y_axis_align = y_align;
        this.update_axes_alignment();
	}

	public set_axis_flipped(x_axis_flipped: boolean, y_axis_flipped: boolean): void {
		this.options.x_axis_flipped = x_axis_flipped;
		this.options.y_axis_flipped = y_axis_flipped;
        this.update_axes_flipping();
	}

    public abstract update(x: NumberArray, y: NumberArray): void;

    public delete(): void {
        this.surface.xAxes.remove(this.x_axis);
        this.surface.yAxes.remove(this.y_axis);
        this.surface.renderableSeries.remove(this.renderable_series);
        this.renderable_series.delete();
        this.x_axis.delete();
        this.y_axis.delete();
        this.data_series.delete();
    }
}
