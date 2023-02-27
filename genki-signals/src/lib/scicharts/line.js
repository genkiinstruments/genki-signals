import { SubChart } from './subchart';
import { FastLineRenderableSeries } from 'scichart/Charting/Visuals/RenderableSeries/FastLineRenderableSeries';
import { defaultAxisOptions } from '../utils/constants';
import { NumericAxis } from 'scichart';
/**
 * Line chart that extends {@inheritdoc SubChart}
 */
export class Line extends SubChart {
    constructor() {
        super(...arguments);
        this.lines = [];
    }
    create(n_lines) {
        this.delete_data_series();
        this.create_data_series(n_lines);
        for (let i = 0; i < n_lines; i++) {
            const line = new FastLineRenderableSeries(this.wasm_context);
            const xAxis = new NumericAxis(this.wasm_context, defaultAxisOptions);
            const yAxis = new NumericAxis(this.wasm_context, defaultAxisOptions);
            this.x_axes.push(xAxis);
            this.y_axes.push(yAxis);
            this.sub_chart_surface.xAxes.add(xAxis);
            this.sub_chart_surface.yAxes.add(yAxis);
            line.dataSeries = this.data_series_list[i];
            this.lines.push(line);
            this.sub_chart_surface.renderableSeries.add(line);
        }
        for (let i = 0; i < n_lines; i++) {
            this.update_axes_alignment(this.x_axes[i], this.y_axes[i]);
            this.update_axes_flipping(this.x_axes[i], this.y_axes[i]);
            this.update_axes_domains(this.x_axes[i], this.y_axes[i]);
        }
        this.update_position();
    }
}
//# sourceMappingURL=line.js.map