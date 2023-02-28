import type { Rect, SciChartSubSurface, TSciChart, SciChartSurface } from 'scichart';

import { createSubSurfaceOptions } from '../utils/subchart_helpers';

import { Line, type LinePlotOptions } from './line';
// import { Trace, type TracePlotOptions } from './trace';
import type { Deletable, Updatable } from './interfaces';
import type { BasePlot, PlotOptions } from './baseplot';

/**
 * An abstract base class for all subcharts.
 * @class
 * @param id - The id of the subchart.
 * @param parent_surface - The parent sciChartSurface.
 * @param wasm_context - The wasm context.
 * @param rect - The rect defining where to place the subchart on the parent surface.
 * @param options - Options describing the subcharts domain, axes etc.
 */
export class SubChart implements Deletable, Updatable {
	id: string;
	wasm_context: TSciChart;
	rect: Rect;
	sub_chart_surface: SciChartSubSurface;
	plots: BasePlot[]; // TODO: Array of BasePlot

	constructor(
		id: string,
		parent_surface: SciChartSurface,
		wasm_context: TSciChart,
		rect: Rect,
		options: PlotOptions[]
	) {
		this.id = id;
		this.wasm_context = wasm_context;
		this.rect = rect;

		this.sub_chart_surface = parent_surface.addSubChart(
			createSubSurfaceOptions(this.id, this.rect)
		);

		this.plots = options.map((plot_options) => this.create_plot(plot_options));
	}

	public add_plot(plot_options: PlotOptions): void {
		this.plots.push(this.create_plot(plot_options));
	}

	// TODO: Insufficient implementation
	public remove_plot(plot_idx: number): void {
		if (plot_idx < 0 || plot_idx >= this.plots.length)
			throw new Error(`Invalid plot index: ${plot_idx}`);

		const plot = this.plots[plot_idx];
		if (plot) plot.delete();

		this.plots.splice(plot_idx, 1);
	}

	private create_plot(plot_options: PlotOptions): BasePlot {
		switch (plot_options.type) {
			case 'line':
				return new Line(this.wasm_context, this.sub_chart_surface, plot_options as LinePlotOptions);
			case 'trace':
			// return new Trace(this.wasm_context, this.sub_chart_surface, plot_options as TracePlotOptions);
			case 'no_type':
				throw new Error('No plot type specified');
			default:
				throw new Error(`Unknown plot type: ${plot_options.type}`);
		}
	}

	public set_position(rect: Rect): void {
		this.rect = rect;
		this.sub_chart_surface.subPosition = this.rect;
	}

	public update(x_data: Array<number>, y_data_list: Array<number>[]): void {
		// Update each plot
		if (y_data_list.length !== this.plots.length)
			throw new Error('Number of plots does not match number of y data arrays');

		this.plots.map((plot, idx) => plot.update(x_data, y_data_list[idx]));
	}

	public delete(): void {
		// call delete on each plot
		this.sub_chart_surface.delete();
		this.plots.map((plot) => plot.delete());
		this.plots = [];
	}
}
