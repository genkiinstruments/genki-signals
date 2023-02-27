import type { Rect, SciChartSubSurface, TSciChart, SciChartSurface } from 'scichart';

import { createSubSurfaceOptions } from '../utils/subchart_helpers';
import type { BasePlot } from './baseplot';
import { Line } from './line';



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
	id: string;
	parent_surface: SciChartSurface;
	wasm_context: TSciChart;
	rect: Rect;
	sub_chart_surface: SciChartSubSurface;
	plot: BasePlot; // TODO: Array of BasePlot

	constructor(
		id: string,
		parent_surface: SciChartSurface,
		wasm_context: TSciChart,
		rect: Rect,
		// type: 'line' | 'trace'
	) {
		this.id = id;
		this.parent_surface = parent_surface;
		this.wasm_context = wasm_context;
		this.rect = rect;
		
		this.sub_chart_surface = this.parent_surface.addSubChart(
			createSubSurfaceOptions(this.id, this.rect)
		);

		// if (type === 'line') {
		// } else if (type === 'trace') {
		// }
		this.plot = new Line(this.wasm_context, this.sub_chart_surface);
	}

	public set_position(rect: Rect): void {
		this.rect = rect;
		this.sub_chart_surface.subPosition = this.rect;
	}

	public update(x_data: Array<number>, y_data_list: Array<number>[]): void {
		// Update each plot
	}

	public delete(): void {
		// call delete on each plot
		this.parent_surface.delete();
	}
}
