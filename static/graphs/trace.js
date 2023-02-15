/**
* @param {Array} data - The data to bind to the plot.
* @param {string} divname - The name of the div to append the SVG element to.
* @param {string} id - The id of the SVG element.
* @param {string} x - The attribute name of the x axis 
* @param {string} y - The attribute name of the y axis 
* @param {number} width - The width of the SVG element.
* @param {number} height - The height of the SVG element.
* @returns The d3 object for the trace with an update function.
*/

export function create_trace(data, divname, id, x, y, width, height) {
    const margin = { top: 20, right: 20, bottom: 30, left: 40 };
    width -= margin.left + margin.right;
    height -= margin.top + margin.bottom;
    
    if(typeof x === "string" || x instanceof String){x = [x,0]}
    if(typeof y === "string" || y instanceof String){y = [y,0]}

    var xScale = d3.scaleLinear()
        .domain([0, 2560]) // Have a config for variables like domain and range?
        .range([0, width]);

    var yScale = d3.scaleLinear()
        .domain([0, 1440])
        .range([0, height]);

    var svg = d3.select(divname).append("svg").attr("id", id)

    var g = svg
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    const clip_id = id + "clip"

    g.append("defs")
        .append("clipPath")
              .attr("id", clip_id)
        .append("rect")
              .attr("width", width)
              .attr("height", height);

    // Add x-axis.
    g.append("g")
        .attr("transform", "translate(0," + height + ")")
        .call(d3.axisBottom(xScale));

    // Add y-axis.
    g.append("g")
        .call(d3.axisLeft(yScale));

    var line = d3.line()
        .x(d => xScale(d[x[0]][x[1]]))
        .y(d => yScale(d[y[0]][y[1]]));

        
    var trace = g.append("g")
        .attr("clip-path","url(#"+clip_id+")")
        .append("path")
        .datum(data)
        .attr("class","line")

    return Object.assign(svg.node(), {
        update() {
            trace.attr("d",line)
        }
    })
}