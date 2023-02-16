import { padding } from '$lib/utils/constants.js';
import { data_buffer } from '$lib/stores/data_buffer.js';
import '$lib/utils/dtypes.js';

import * as d3 from 'd3';

// NOTE: The type of sig_y is not strictly true, if it is not an array, it will be converted to one.

/**
* @param {HTMLDivElement} el - The div to append the SVG element to.
* @param {string} id - The id of the SVG element.
* @param {SignalID} sig_x - The attribute name of the x axis 
* @param {SignalID[]} sig_y - The attribute name of the y axis 
* @param {DomainConfig} x_domain - The domain of the x axis
* @param {DomainConfig} y_domain - The domain of the y axis
* @param {number} svg_width - The width of the SVG element.
* @param {number} svg_height - The height of the SVG element.
* @returns The d3 object for the trace with an update function.
*/
export function create_line(
      el,
      id,
      sig_x,
      sig_y,
      x_domain = { min: 0, max: 1, auto: false },
      y_domain = { min: 0, max: 1, auto: false },
      svg_width = 720,
      svg_height = 480
) {   
      svg_width -= padding.left + padding.right
      svg_height -= padding.top + padding.bottom


      var svg = d3.select(el).append('svg').attr('id', id)

      var g = svg
            .attr('width', svg_width + padding.left + padding.right)
            .attr('height', svg_height + padding.top + padding.bottom)
            .append('g')
            .attr('transform', 'translate(' + padding.left + ',' + padding.top + ')');

      const clip_id = id + 'clip'

      g.append('defs')
            .append('clipPath')
            .attr('id', clip_id)
            .append('rect')
            .attr('width', svg_width)
            .attr('height', svg_height);


      const xScale = d3.scaleLinear()
            .domain([x_domain.min, x_domain.max])
            .range([0, svg_width]); 

      const yScale = d3.scaleLinear()
            .domain([y_domain.min, y_domain.max])
            .range([0, svg_height]);

      const n_ticks = 5;      
      const xAxis = g.append('g')
            .attr('transform', 'translate(0,' + yScale(0) + ')')
            .call(d3.axisBottom(xScale).ticks(n_ticks));

      // Add y-axis.
      g.append('g')
            .call(d3.axisLeft(yScale));


      var pathG = g.append('g').attr('clip-path', 'url(#' + clip_id + ')')
      /**
       * @type {Object[]}
       */
      var paths = []

      for (let i = 0; i < sig_y.length; i++) {
            const line = d3.line()
                  .x(/** @param {Object.<String,number[]>} d */ d => xScale(d[sig_x.key][sig_x.index]))
                  .y(/** @param {Object.<String,number[]>} d */ d => yScale(d[sig_y[i].key][sig_y[i].index]))

            let path = pathG.append('path')
                  .datum(data_buffer.view())
                  .attr('class', 'line')

            paths.push(Object.assign(path.node(), {
                  update() {
                        d3.select(this)
                              .attr('d', line)
                  }
            }));
      }

      return Object.assign(svg.node(), {
            update() {
                  if (sig_x.key == 'timestamp_us') {
                        const timestamp_domain = data_buffer.timestamp_range();
                        xScale.domain([timestamp_domain.min, timestamp_domain.max])
                  }

                  xAxis.attr('transform', 'translate(0,' + yScale(0) + ')')
                        .call(d3.axisBottom(xScale).tickFormat("").ticks(10));

                  for (let path of paths) { path.update() }
            }
      })

}