import { Rect } from 'scichart/Core/Rect.js';
import { Thickness } from 'scichart/Core/Thickness.js';
import { ECoordinateMode } from 'scichart/Charting/Visuals/Annotations/AnnotationBase';
/**
 * @param chartIndex
 * @param columnNumber
 * @returns Object with rowIndex and columnIndex properties.
 */
function getSubChartPositionIndexes(chartIndex, columnNumber) {
    const rowIndex = Math.floor(chartIndex / columnNumber);
    const columnIndex = chartIndex % columnNumber;
    return { rowIndex, columnIndex };
}
/**
 * @param num_subcharts - Number of subcharts.
 * @param subchart_height - Height of each subchart.
 * @param subchart_width - Width of each subchart.
 * @param column_number - Number of columns.
 * @returns - Array of Rect objects which describe where each subchart will be placed.
 */
export function getSubChartRects(num_subcharts, subchart_height, subchart_width, column_number) {
    const rects = [];
    for (let i = 0; i < num_subcharts; i++) {
        const { rowIndex, columnIndex } = getSubChartPositionIndexes(i, column_number);
        const top = rowIndex * subchart_height;
        const left = columnIndex * subchart_width;
        const rect = new Rect(left, top, subchart_width, subchart_height);
        rects.push(rect);
    }
    return rects;
}
const _subChartPositioningCoordinateMode = ECoordinateMode.Relative;
const _subChartPadding = Thickness.fromNumber(3);
export function createSubSurfaceOptions(id, position) {
    console.log('createSubSurfaceOptions', id, position);
    return {
        id,
        position,
        coordinateMode: _subChartPositioningCoordinateMode,
        subChartPadding: _subChartPadding,
        viewportBorder: {
            color: 'rgba(150, 74, 148, 0.51)',
            border: 2
        }
    };
}
//# sourceMappingURL=subchart_helpers.js.map