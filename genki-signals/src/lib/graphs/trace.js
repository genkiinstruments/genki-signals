import { margin } from '$lib/utils/constants.js';
import { data_buffer } from '$lib/stores/data_buffer.js';

import * as d3 from 'd3';

/**
* @param {HTMLDivElement} el - The div to append the SVG element to.
* @param {string} x_key - The key to access x from data.
* @param {string} y_key - The key to access y from data.
* @param {string} id - The id of the SVG element.
* @param {number} width - The width of the SVG element.
* @param {number} height - The height of the SVG element.
* @returns The d3 object for the trace with an update function.
*/
export function create_trace(el, x_key, y_key, id, width, height) {
    var xScale = d3.scaleLinear()
        .domain([0, 2560]) // Have a config for variables like domain and range?
        .range([0, width]);

    var yScale = d3.scaleLinear()
        .domain([0, 1440])
        .range([0, height]);

    var svg = d3.select(el)
        .append("svg")
        .attr("id", id)
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)

    var g = svg
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    // Add x-axis.
    g.append("g")
        .attr("transform", "translate(0," + height + ")")
        .call(d3.axisBottom(xScale));

    // Add y-axis.
    g.append("g")
        .call(d3.axisLeft(yScale));


    var trace = g.append("g")
        .append("path")
        .datum(data_buffer.view()) // Bind trace to the data buffer.
        .attr("class", "trace")

    var line = d3.line()
        .x(d => xScale(d[x_key]))
        .y(d => yScale(d[y_key]));

    // Subscribe to the data buffer with the update method for the trace.
    data_buffer.subscribe((/** @type {Array<Object>} */ buffer) => {
        trace = trace.attr("d", line);
    });

    return svg.node();
};