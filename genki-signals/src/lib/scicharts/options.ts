export interface PlotOptions {
	x_axis_align: 'top' | 'bottom';
	y_axis_align: 'left' | 'right';
	x_axis_flipped: boolean;
	y_axis_flipped: boolean;
	x_axis_visible: boolean; // TODO: implement
	y_axis_visible: boolean;
	data_contains_nan: boolean;
	data_is_sorted: boolean;
};

export interface LinePlotOptions extends PlotOptions {
    /** If auto range is true, then y_domain_max and y_domain_min are not used */
    auto_range: boolean;
    y_domain_max: number;
    y_domain_min: number;
    n_visible_points: number;
}

export interface TracePlotOptions extends PlotOptions {
    /** If auto_range_x is true, then x_domain_max and x_domain_min are not used */
    auto_range_x: boolean;
    /** If auto_range_y is true, then y_domain_max and y_domain_min are not used */
    auto_range_y: boolean;
    x_domain_max: number;
    x_domain_min: number;
    y_domain_max: number;
    y_domain_min: number;
    buffer_size: number;
}

export const default_plot_options: PlotOptions = {
	x_axis_align: 'bottom',
	y_axis_align: 'left',
	x_axis_flipped: false,
	y_axis_flipped: false,
	x_axis_visible: true,
	y_axis_visible: true,
	data_contains_nan: false,
	data_is_sorted: false
};

export const default_line_plot_options: LinePlotOptions = {
    auto_range: false,
    y_domain_max: 1,
    y_domain_min: 0,
    n_visible_points: 100,
    ...default_plot_options
};

export const default_trace_plot_options: TracePlotOptions = {
    auto_range_x: false,
    auto_range_y: false,
    x_domain_max: 2560,
    x_domain_min: 0,
    y_domain_max: 1440,
    y_domain_min: 0,
    buffer_size: 1000,
    ...default_plot_options
};