const padding = 0.1;
/*
* @param {number} width - The width of the SVG element.
* @param {number} height - The height of the SVG element.
* @param {string[]} col_names - The names of the columns to be used.
* @returns The d3 object for the histogram.
*/
function create_histogram(data, divname, id, width, height, col_names) {
    var xScale = d3.scaleBand()
        .domain(col_names) // Have a config for variables like domain and range?
        .range([0, width])
        .padding(padding);

    var yScale = d3.scaleLinear()
        .domain([0, 3000])
        .range([0, height]);

    // Create the SVG element.
    var svg = d3.select(divname)
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
        .call(d3.axisBottom(xScale))
        .selectAll("text")
        .attr("transform", "translate(-10,0)rotate(-45)")
        .style("text-anchor", "end");

    // Add y-axis.
    svg.append("g")
        .call(d3.axisLeft(yScale));

    return Object.assign(svg.node(), {
        update() {
            const bars = svg.selectAll("rect")
                .data(data)

            bars
                .enter()
                .append("rect")
                .merge(bars)
                .attr("x", (d) => { xScale(d.Country); })
                .attr("y", (d) => { yScale(d.Value); })
                .attr("width", xScale.bandwidth())
                .attr("height", (d) => { height - yScale(d.Value); })
                .attr("fill", "#69b3a2")

            bars.exit().remove()
        }
    }
    );

}