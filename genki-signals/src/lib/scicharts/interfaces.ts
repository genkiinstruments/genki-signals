import type { NumberArray } from "scichart";

export interface Updatable {
    /**
     * Updates the plots.
     * @param x - The x values.
     * @param y - The y values.
     * @returns void
     * 
     * @remarks
     * This method is called by the {@link SubChart} class to update the plots.
     */
    update(x: NumberArray, y: NumberArray): void;
}

export interface Deletable {
    /**
     * Deletes to free up web assembly memory.
     * @returns void
     * 
     * @remarks
     * This method is called by the {@link SubChart} class to delete the plots and free memory.
     */
    delete(): void;
}



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