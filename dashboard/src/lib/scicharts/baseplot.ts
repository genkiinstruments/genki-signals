import { BaseHeatmapDataSeries, EAxisAlignment, type NumberArray } from 'scichart';
import type {
	TSciChart,
	AxisBase2D,
	BaseRenderableSeries,
	SciChartSubSurface,
	BaseDataSeries
} from 'scichart';

import { Signal } from './data';
import type { SignalConfig, ArrayDict } from './data';
import type { IDeletable, IUpdatable } from './interfaces';

export interface PlotOptions {
	name: string;
	x_axis_align: 'top' | 'bottom' | 'left' | 'right';
	y_axis_align: 'left' | 'right' | 'top' | 'bottom';
	x_axis_flipped: boolean;
	y_axis_flipped: boolean;
	x_axis_visible: boolean;
	y_axis_visible: boolean;
	data_contains_nan: boolean;
	data_is_sorted: boolean;
}
export function get_default_plot_options(): PlotOptions {
	return {
		name: 'no_name',
		x_axis_align: 'bottom',
		y_axis_align: 'left',
		x_axis_flipped: false,
		y_axis_flipped: false,
		x_axis_visible: true,
		y_axis_visible: true,
		data_contains_nan: false,
		data_is_sorted: true
	};
}

export abstract class BasePlot implements IUpdatable, IDeletable {
	public readonly wasm_context: TSciChart;
	public readonly surface: SciChartSubSurface;

	protected abstract options: PlotOptions;

	protected abstract x_axis: AxisBase2D;
	protected abstract y_axis: AxisBase2D;

	// The x-values are the same for all data series.
	protected abstract sig_x: Signal;

	// ############################ The following are 1 to 1 mappings ########################################
	// Many y-values can be mapped to one x-value.
	protected abstract sig_y: Signal[];
	protected abstract renderable_series: BaseRenderableSeries[];
	protected abstract data_series: BaseDataSeries[] | BaseHeatmapDataSeries[];
	// #######################################################################################################


	constructor(wasm_context: TSciChart, surface: SciChartSubSurface) {
		this.wasm_context = wasm_context;
		this.surface = surface;
	}

	/**
	 * @param at - The index of the data series. If at is negative, then the index is counted from the end.
	 * @returns The x-value at index at.
	 */
	protected get_native_x(at: number): number {
		const data_series = this.data_series[0]; // All series have the same x-values

		if (data_series === undefined) throw new Error('Data series is undefined');

		const count = data_series.count();
		const x_values = data_series.getNativeXValues();

		if (at < 0) {
			return x_values.get(Math.max(count + at, 0));
		}
		if (at >= count) {
			throw new Error(`Index ${at} out of bounds`);
		}
		return x_values.get(at);
	}

	private axis_alignment(axis: AxisBase2D, axis_alignment: string): void {
		switch (axis_alignment) {
			case 'top':
				axis.axisAlignment = EAxisAlignment.Top;
				break;
			case 'bottom':
				axis.axisAlignment = EAxisAlignment.Bottom;
				break;
			case 'left':
				axis.axisAlignment = EAxisAlignment.Left;
				break;
			case 'right':
				axis.axisAlignment = EAxisAlignment.Right;
				break;
			default:
				throw new Error(`Invalid axis alignment: ${axis_alignment}`);
		}
	}

	protected update_axes_alignment(): void {
		const x_is_horiz = this.options.x_axis_align in ["top", "bottom"];
		const y_is_horiz = this.options.y_axis_align in ["top", "bottom"];
		if (x_is_horiz != y_is_horiz){
			this.axis_alignment(this.x_axis, this.options.x_axis_align);
			this.axis_alignment(this.y_axis, this.options.y_axis_align);
		}
	}

	protected update_axes_flipping(): void {
		this.x_axis.flippedCoordinates = this.options.x_axis_flipped;
		this.y_axis.flippedCoordinates = this.options.y_axis_flipped;
	}

	protected update_axes_visibility(): void {
		this.x_axis.isVisible = this.options.x_axis_visible;
		this.y_axis.isVisible = this.options.y_axis_visible;
	}

	protected update_data_optimizations(): void {
		this.data_series.forEach((ds) => {
			ds.containsNaN = this.options.data_contains_nan;
			ds.isSorted = this.options.data_is_sorted;
		});
	}

	/**
	 * Calls each update option functions.
	 * @param options - The new plot options
	 */
	protected abstract update_all_options(options: PlotOptions): void;

	public get_options(): PlotOptions {
		return this.options;
	}

	public set_options(options: PlotOptions): void {
		this.update_all_options(options);
	}

	public get_signal_configs() {
		return {'sig_x': this.sig_x.get_config(), 'sig_y': this.sig_y.map((sig) => sig.get_config())};
	}

	public set_signals(sig_x: SignalConfig, sig_y: SignalConfig[]): void {
		this.change_sig_x(sig_x);
		this.change_sig_y(sig_y);
	}

	/**
	 * Updates the signal config for the x-axis. If the new signal config is different from the old one,
	 * then all data series are cleared.
	 * @param sig_x - The new signal config for the x-axis.
	 */
	protected change_sig_x(config: SignalConfig): void {
		if (!(this.sig_x.compare_to(config))) {
			this.data_series.forEach((ds) => ds.clear());
			this.sig_x.set_config(config);
		}
	}

	/**
	 * Updates the signal configs for the y-axis.
	 * If old signals are no longer present in the new list, then the corresponding plots are removed.
	 * If new signals are present in the new list, then new plots are created.
	 * @param sig_y - The new signal configs for the y-axis.
	 */
	protected change_sig_y(sig_y: SignalConfig[]): void {
		const new_signals = sig_y.map((config) => Signal.from_config(config));
		const new_set = new Set(new_signals.map((sig) => sig.get_id()));
		const old_set = new Set(this.sig_y.map((sig) => sig.get_id()));

		// Removes duplicates
		const new_set_copy = new Set(new_set);
		const new_list = new_signals.filter((sig) => {
			const id = sig.get_id();
			if (new_set_copy.has(id)) {
				new_set_copy.delete(id);
				return true;
			}
			return false;
		});
		const old_set_copy = new Set(old_set);
		const old_list = this.sig_y.filter((sig) => {
			const id = sig.get_id();
			if (old_set_copy.has(id)) {
				old_set_copy.delete(id);
				return true;
			}
			return false;
		});

		let removed_indexes: number[] = [];

		old_list.forEach((sig, at) => {
			if (!new_set.has(sig.get_id())) {
				console.log('removing at: ', at)
;				this.remove_renderable(at);
				removed_indexes.push(at);
			}
		});

		// -1 signifies appending for the add_renderable function, so filling the removed_indexes array with -1s
		// ensures that we replace any removed signals with new ones and then start appending new signals.
		removed_indexes = [... removed_indexes, ... Array(new_list.length).fill(-1)]

		let add_count = 0;
		new_list.forEach((sig) => {
			if (!old_set.has(sig.get_id())) {
				const idx = removed_indexes[add_count];
				if (idx === undefined) throw new Error("Unexpected undefined index");
				console.log('adding at: ', idx);
				this.add_renderable(idx);
				add_count += 1;
			}
		});

		// TODO: Check this, set should preserve insertion order but there may be some unforeseen edge cases
		this.sig_y = new_list;
    }

	/**
	 * Access the data with the given signal config and throws errors.
	 * @param data - The data to access
	 * @param sig - The signal config to access
	 * @returns data[sig.sig_key][sig.sig_idx]
	 */
	protected check_and_fetch(data: ArrayDict, sig: Signal | undefined): NumberArray {
		if (sig === undefined) return [];
		if (!(sig.key in data)) return []; //throw new Error(`sig_key ${sig_key} not in data`);
		if (sig.idx >= data[sig.key].length) return []; //throw new Error(`sig_idx ${sig_idx} out of bounds`);

		return data[sig.key][sig.idx] as NumberArray;
	}

	/**
	 * A function that specifies how to create the renderable series, dataseries etc. for each subclass.
	 * @ param at - The index of the renderable series to add, -1 for last.
	 */
	protected abstract add_renderable(at: number): void;

	/**
	 * A function that specifies how to remove the renderable series, dataseries etc.
	 * @param at - The index of the renderable series to remove, -1 for last.
	 */
	protected remove_renderable(at: number): void {
		if (at === -1) at = this.renderable_series.length - 1;
		if (at >= this.renderable_series.length) return;

		this.surface.renderableSeries.remove(this.renderable_series[at]);
		this.renderable_series[at]?.delete();
		this.renderable_series.splice(at, 1);

		// this.data_series[at]?.clear();
		this.data_series[at]?.delete();
		this.data_series.splice(at, 1);
	}


	// ################################## Interface implementations ##################################

	public abstract update(data: ArrayDict): void;

	public delete(): void {
		this.surface.xAxes.remove(this.x_axis);
		this.surface.yAxes.remove(this.y_axis);
		this.x_axis.delete();
		this.y_axis.delete();

		this.renderable_series.forEach((rs) => rs.delete());
		this.data_series.forEach((ds) => ds.delete());
		
		this.surface.delete();
	}

}
