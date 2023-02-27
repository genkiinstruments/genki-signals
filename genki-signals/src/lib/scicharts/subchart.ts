import {
	EAutoRange,
	EAxisAlignment,
	NumberRange,
	NumericAxis,
	Rect,
	SciChartSubSurface
} from 'scichart';
import { XyDataSeries } from 'scichart/Charting/Model/XyDataSeries.js';
import type { TSciChart, SciChartSurface } from 'scichart';

import { createSubSurfaceOptions } from '../utils/subchart_helpers';

export type DefaultSubChartOptions = {
	x_domain_max: number | null;
	x_domain_min: number | null;
	y_domain_max: number | null;
	y_domain_min: number | null;
	n_visible_points: number;
	x_axis_align: 'top' | 'bottom';
	y_axis_align: 'left' | 'right';
	x_axis_flipped: boolean;
	y_axis_flipped: boolean;
	x_axis_visible: boolean; // TODO: implement
	y_axis_visible: boolean;
	data_contains_nan: boolean;
	data_is_sorted: boolean;
};

export const defaultSubChartOptions: DefaultSubChartOptions = {
	x_domain_max: null,
	x_domain_min: null,
	y_domain_max: null,
	y_domain_min: null,
	n_visible_points: 1_000,
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
export abstract class SubChart {
	id: string;
	parent_surface: SciChartSurface;
	wasm_context: TSciChart;
	rect: Rect;
	options: DefaultSubChartOptions;

	protected sub_chart_surface: SciChartSubSurface;
	protected x_axes: NumericAxis[];
	protected y_axes: NumericAxis[];
	protected data_series_list: XyDataSeries[];

	constructor(
		id: string,
		parent_surface: SciChartSurface,
		wasm_context: TSciChart,
		rect: Rect,
		options: DefaultSubChartOptions = defaultSubChartOptions
	) {
		this.id = id;
		this.parent_surface = parent_surface;
		this.wasm_context = wasm_context;
		this.rect = rect;
		this.options = options;

		this.sub_chart_surface = this.parent_surface.addSubChart(
			createSubSurfaceOptions(this.id, this.rect)
		);
		this.x_axes = [];
		this.y_axes = [];
		// All series should have the same x-values
		this.data_series_list = [];
	}

	protected create_data_series(n: number): void {
		this.data_series_list = Array(n)
			.fill(null)
			.map(() => {
				const dataSeries = new XyDataSeries(this.wasm_context);
				dataSeries.containsNaN = this.options.data_contains_nan;
				dataSeries.isSorted = this.options.data_is_sorted;
				return dataSeries;
			});
	}

	protected delete_data_series(): void {
		this.data_series_list.forEach((dataSeries) => dataSeries.delete());
		this.data_series_list = [];
	}

	/**
	 * Each dataSeries should contain the same x-values, so we use the first one.
	 */
	private _get_native_x(i: number): number {
		if (i < 0) {
			const x_count = this.data_series_list[0].count();
			return this.data_series_list[0].getNativeXValues().get(x_count + i); // + (negative number)
		}
		return this.data_series_list[0].getNativeXValues().get(i);
	}

	protected update_axes_domains(x_axis: NumericAxis, y_axis: NumericAxis): void {
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
		} else if (this.options.y_domain_max !== null && this.options.y_domain_min !== null) {
			y_axis.autoRange = EAutoRange.Never;
			y_axis.visibleRange = new NumberRange(this.options.y_domain_min, this.options.y_domain_max);
		} else {
			throw new Error('Both y_max and y_min must be null or not null.');
		}
		// TODO: if not zoom / pan then update the visible range
	}

	protected update_axes_alignment(x_axis: NumericAxis, y_axis: NumericAxis): void {
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

	protected update_axes_flipping(x_axis: NumericAxis, y_axis: NumericAxis): void {
		x_axis.flippedCoordinates = this.options.x_axis_flipped;
		y_axis.flippedCoordinates = this.options.y_axis_flipped;
	}

	protected update_position(): void {
		this.sub_chart_surface.subPosition = this.rect;
	}

	/**
	 * Adds data to all the dataSeries in this subplot and updates the axes.
	 */
	protected update_data_series(x_data: Array<number>, y_data_list: Array<number>[]): void {
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

	public setAxesDomains(x_max: number, x_min: number, y_max: number, y_min: number): void {
		this.options.x_domain_max = x_max;
		this.options.x_domain_min = x_min;
		this.options.y_domain_max = y_max;
		this.options.y_domain_min = y_min;

		for (let i = 0; i < this.x_axes.length; i++) {
			this.update_axes_domains(this.x_axes[i], this.y_axes[i]);
		}
	}

	public setAxesAlignments(x_align: 'top' | 'bottom', y_align: 'left' | 'right'): void {
		this.options.x_axis_align = x_align;
		this.options.y_axis_align = y_align;

		for (let i = 0; i < this.x_axes.length; i++) {
			this.update_axes_alignment(this.x_axes[i], this.y_axes[i]);
		}
	}

	public setAxesFlipped(x_axis_flipped: boolean, y_axis_flipped: boolean): void {
		this.options.x_axis_flipped = x_axis_flipped;
		this.options.y_axis_flipped = y_axis_flipped;

		for (let i = 0; i < this.x_axes.length; i++) {
			this.update_axes_flipping(this.x_axes[i], this.y_axes[i]);
		}
	}

	public setPosition(x: number, y: number, width: number, height: number): void {
		this.rect = new Rect(x, y, width, height);

		this.update_position();
		// TODO: Finish this
	}

	public update(x_data: Array<number>, y_data_list: Array<number>[]): void {
		this.update_data_series(x_data, y_data_list);

		for (let i = 0; i < this.x_axes.length; i++) {
			this.update_axes_domains(this.x_axes[i], this.y_axes[i]);
		}
		// ...
	}

	public delete(): void {
		this.delete_data_series();
		this.sub_chart_surface.delete();
		// ...
	}

	public abstract create(n_lines: number): void;
}
