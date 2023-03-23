import { Thickness } from 'scichart/Core/Thickness';
import { ECoordinateMode } from 'scichart/Charting/Visuals/Annotations/AnnotationBase';
import type { I2DSubSurfaceOptions } from 'scichart';

/**
 * @param idx
 * @param n_cols
 * @returns Object with row_idx and col_idx properties.
 */
export function get_position_index(idx: number, n_cols: number) {
	const row_idx = Math.floor(idx / n_cols);
	const col_idx = idx % n_cols;
	return { row_idx, col_idx };
}

// TODO: Here we can add Id / divId to the subchart options
export const sub_surface_options: I2DSubSurfaceOptions = {
	coordinateMode: ECoordinateMode.Relative,
	subChartPadding: Thickness.fromNumber(3),
	viewportBorder: {
		color: 'rgba(150, 74, 148, 0.51)',
		border: 2
	}
};

