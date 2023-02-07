const margin = { top: 20, right: 20, bottom: 30, left: 40 };

/*
* @param {Array} data - The data to bind to the plot.
* @param {string} divname - The name of the div to append the SVG element to.
* @param {string} id - The id of the SVG element.
* @param {number} width - The width of the SVG element.
* @param {number} height - The height of the SVG element.
* @returns The d3 object for the trace with an update function.
*/
function create_trace(data, divname, id, width, height) {
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

    // Add x-axis.
    g.append("g")
        .attr("transform", "translate(0," + height + ")")
        .call(d3.axisBottom(xScale));

    // Add y-axis.
    g.append("g")
        .call(d3.axisLeft(yScale));

        
    var trace = g.append("g")
        .append("path")
        .datum(data) // Bind data to the line.
        .attr("class", "line")
    
    var line = d3.line()
        .x(d => xScale(d.mouse_pos[0]))
        .y(d => yScale(d.mouse_pos[1]));

    return Object.assign(svg.node(), {
        update() {
            trace = trace.attr("d", line);
        }
    })
};