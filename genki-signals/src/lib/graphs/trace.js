import { margin } from '$lib/utils/constants.js';
import * as d3 from 'd3';

/**
* @param {HTMLDivElement} el - The div to append the SVG element to.
* @param {Object[]} data - The data to bind to the trace.
* @param {string} data_key - The key to use to access the data.
* @param {string} id - The id of the SVG element.
* @param {number} width - The width of the SVG element.
* @param {number} height - The height of the SVG element.
* @returns The d3 object for the trace with an update function.
*/
export function create_trace(el, data, data_key, id, width, height) {
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
        .datum(data)
        .attr("class", "trace")
    
    var line = d3.line()
        .x(d => xScale(d[data_key][0]))
        .y(d => yScale(d[data_key][1]));

    return Object.assign(svg.node(), {
        update() {
            trace = trace.attr("d", line); 
        },
    })
};