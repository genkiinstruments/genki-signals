import { padding } from '$lib/utils/constants.js';
import { data_buffer } from '$lib/stores/data_buffer.js';
import '$lib/utils/dtypes.js';

import * as d3 from 'd3';

/**
* @param {HTMLDivElement} el - The div to append the SVG element to.
* @param {string} id - The id of the SVG element.
* @param {SignalID} sig_x - The attribute name of the x axis 
* @param {SignalID} sig_y - The attribute name of the y axis 
* @param {RangeConfig} x_range - The range of the x axis
* @param {RangeConfig} y_range - The range of the y axis
* @param {DomainConfig} x_domain - The domain of the x axis
* @param {DomainConfig} y_domain - The domain of the y axis
* @param {number} svg_width - The width of the SVG element.
* @param {number} svg_height - The height of the SVG element.
* @returns The d3 object for the trace with an update function.
*/
export function create_trace(
    el,
    id,
    sig_x,
    sig_y,
    x_range={ min: 0, max: 1, auto: false },
    y_range={ min: 0, max: 1, auto: false },
    x_domain={ min: 0, max: 1 },
    y_domain={ min: 0, max: 1 },
    svg_width=720,
    svg_height=480
) {
    var svg = d3.select(el).append("svg").attr("id", id)
    var g = svg
        .attr("width", svg_width)
        .attr("height", svg_height)
        .append("g")
        .attr("transform", "translate(" + padding.left + "," + padding.top + ")");
    
    const plot_height = svg_height - padding.top - padding.bottom;

    var xScale = d3.scaleLinear()
        .domain([x_domain.min, x_domain.max])
        .range([x_range.min, x_range.max]);

    var yScale = d3.scaleLinear()
        .domain([y_domain.min, y_domain.max])
        .range([y_range.min, y_range.max]);

    // TODO: Add automatic range scaling.

    // Add x-axis.
    g.append("g")
        .attr("transform", "translate(0," + plot_height + ")")
        .call(d3.axisBottom(xScale));

    // Add y-axis.
    g.append("g")
        .call(d3.axisLeft(yScale));

    var line = d3.line()
        .x(d => xScale(d[sig_x.key][sig_x.index]))
        .y(d => yScale(d[sig_y.key][sig_y.index]));

        
    var trace = g.append("g")
        .append("path")
        .datum(data_buffer.view())
        .attr("class","line")

    // Subscribe to the data buffer with the update method for the trace.
    data_buffer.subscribe((/** @type {Array<Object>} */ buffer) => {
        trace = trace.attr("d", line);
    });

    return svg.node();
}