import type { Rect, SciChartSubSurface, TSciChart, SciChartSurface } from 'scichart';

import { createSubSurfaceOptions } from '../utils/subchart_helpers';

import { Line, type LinePlotOptions } from './line';
import { Trace, type TracePlotOptions } from './trace';
import type { ArrayDict, SignalConfig } from './types';
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
export class SubChart implements Updatable, Deletable {
	id: string;
	wasm_context: TSciChart;
	rect: Rect;
	sub_chart_surface: SciChartSubSurface;
	plot: BasePlot; // TODO: Array of BasePlot

	constructor(
		id: string,
		parent_surface: SciChartSurface,
		wasm_context: TSciChart,
		rect: Rect,
		options: PlotOptions
	) {
		this.id = id;
		this.wasm_context = wasm_context;
		this.rect = rect;

		this.sub_chart_surface = parent_surface.addSubChart(
			createSubSurfaceOptions(this.id, this.rect) // TODO: Improve this
		);

		this.plot = this.create_plot(options);
	}

	private create_plot(plot_options: PlotOptions): BasePlot {
		switch (plot_options.type) {
			case 'line':
				return new Line(this.wasm_context, this.sub_chart_surface, plot_options as LinePlotOptions);
			case 'trace':
				return new Trace(this.wasm_context, this.sub_chart_surface, plot_options as TracePlotOptions);
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

	public update(data: ArrayDict): void {
		this.plot.update(data);
	}

	public delete(): void {
		// call delete on each plot
		this.sub_chart_surface.delete();
		this.plot.delete();
	}
}
