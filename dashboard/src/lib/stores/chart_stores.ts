import { writable } from 'svelte/store';

import type { PlotOptions } from '../scicharts/baseplot';
import { get_default_line_plot_options, type LinePlotOptions } from '../scicharts/line';
// import { get_default_trace_plot_options, type TracePlotOptions } from '../scicharts/trace';

// export interface OptionStore {
//     [id: string]: PlotOptions;
// }

// export const option_store = writable<OptionStore>();

export const option_store = writable<PlotOptions[]>([]);


export const selected_chart_store = writable<number>(0);