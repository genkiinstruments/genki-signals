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
        .domain([0, 1])
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


    var hist = g.append("g")
        .append("path")
        .datum(data)
        .attr("class", "histogram");

    //     // Add the bars.
    // var bars = [];
    // for (var j = 0; j < col_names.length; j++) {
    //     svg.append("rect")
    //         .data(data)
    //         .enter()
    //         .attr("x",  xScale(col_names[j]))
    //         .attr("y", 0)
    //         .attr("width", xScale.bandwidth())
    //         .attr("height", (d) => height - yScale(d))
    //         .attr("fill", "#69b3a2")
    //         .x((d, i) => xScale(d[i]))
    //         .y((d) => yScale(d));
    // }

    // var bars = d3.selectAll("rect");



    return Object.assign(svg.node(), {
        update() {
            console.log("Updating histogram...")
            // Update the bars.
            // hist = hist.attr("d", bars);
        }
    }
    );

}