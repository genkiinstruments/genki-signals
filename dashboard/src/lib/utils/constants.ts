import { EAutoRange } from 'scichart/types/AutoRange';
import { ENumericFormat } from 'scichart/types/NumericFormat';
import type { INumericAxisOptions } from 'scichart/Charting/Visuals/Axis/NumericAxis';

export const MAX_BUFFER_SIZE: number = 10_000_000;

export const SCICHART_KEY: string =
	'+xBLVFvk8xvq9s8/GSQP+sq7H7vTmtiFq91ZdlSlFVS2RFKRXSLI5sUVm3jQ/q/XMd6F8xNW+if9tEP7PoIG3odXD+vyXOSidSeEZrlwoGBLZRZhImWrJn+3d0cDuuJrz97xZMRmZAyChZgj8Trt6tY9dDLY074klLPX8Zh+EHv29xxD/OkKHKXRDDIT0ui7AHIt1af/giN4YQ/EZ4rLDor9YhSgn597Au0HLiZnhvhiQqGhDmTRXXM3zrbmv/lvc2IL+15vWH5JfhRojS5UHnuGOkrqjZmnvUZkBPG23y9HcqO63pUAOGYIj1k6RHiksgVUG9g1Rh4gMgP2y7JDdDX6ffTJu/TIRLZnnp7qrcU1/3kYz5ZIfLayAB/dWNbTEdGxlIO219Bc4f1WMZAvYSkZpSBJVtIJPpkbudzfo70Jp3zq3M+wMXqj1yxbYRUnfVIYtk/qjTj/7phlXpzKbyQwylM5YepJtQDeKsrcFHGzkRAvcJ0CnUeTKznQ4ZvqZd5pftLnLS77t8VquKXgYND5rancB8OFfGxIhD+KqyrjA31O8AvjzS6CJN3dz+YzphY43eu0hm4+x8yV0js=';

export const default_axis_options: INumericAxisOptions = {
	useNativeText: true,
	isVisible: true,
	drawMajorBands: true,
	drawMinorGridLines: true,
	drawMinorTickLines: true,
	drawMajorTickLines: true,
	drawMajorGridLines: true,
	labelStyle: { fontSize: 8 },
	labelFormat: ENumericFormat.Decimal,
	labelPrecision: 0,
	autoRange: EAutoRange.Never
};
