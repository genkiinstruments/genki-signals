import { padding } from '$lib/utils/constants.js';
import { data_buffer } from '$lib/stores/data_buffer.js';
import '$lib/utils/dtypes.js';

import * as d3 from 'd3';

/**
* @param {HTMLDivElement} el - The div to append the SVG element to.
* @param {string} id - The id of the SVG element.
* @param {SignalID} sig_x - The attribute name of the x axis 
* @param {SignalID} sig_y - The attribute name of the y axis 
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
    x_domain={ min: 0, max: 1, auto: false },
    y_domain={ min: 0, max: 1, auto: false },
    svg_width=720,
    svg_height=480
) {
    var svg = d3.select(el).append("svg").attr("id", id)
    var g = svg
        .attr("width", svg_width)
        .attr("height", svg_height)
        .append("g")
        .attr("transform", "translate(" + padding.left + "," + padding.top + ")");

    
    const plot_width = svg_width - padding.left - padding.right;
    const plot_height = svg_height - padding.top - padding.bottom;

    var xScale = d3.scaleLinear()
        .domain([x_domain.min, x_domain.max])
        .range([0, plot_width]);

    var yScale = d3.scaleLinear()
        .domain([y_domain.min, y_domain.max])
        .range([0, plot_height]);

    // TODO: Add automatic range scaling.

    // add clip path
    const clip_id = id + "clip"
    g.append("defs")
          .append("clipPath")
                .attr("id", clip_id)
          .append("rect")
                .attr("width", plot_width)
                .attr("height", plot_height);

    // Add x-axis.
    g.append("g")
        .attr("transform", "translate(0," + yScale(0) + ")")
        .call(d3.axisBottom(xScale));

    // Add y-axis.
    g.append("g")
        .call(d3.axisLeft(yScale));

    var line = d3.line()
        .x(/** @param {Object.<String,number[]>} d */ d => xScale(d[sig_x.key][sig_x.index]))
        .y(/** @param {Object.<String,number[]>} d */ d => yScale(d[sig_y.key][sig_y.index]));

        
    var trace = g.append("g").attr("clip-path","url(#"+clip_id+")")
        .append("path")
        .datum(data_buffer.view())
        .attr("class","line")

    // Subscribe to the data buffer with the update method for the trace.
    data_buffer.subscribe((/** @type {Array<Object>} */ buffer) => {
        console.log(data_buffer.view())
        trace = trace.attr("d", line);
    });

    return svg.node();
}