export function create_line(data, divname, id, x, y, width, height, x_range, y_range){
      const margin = { top: 20, right: 20, bottom: 30, left: 40};
      width -= margin.left + margin.right
      height -= margin.top + margin.bottom


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
        

      const xScale = d3.scaleLinear()
        .domain(x_range)
        .range([0, width]);
  
      const yScale = d3.scaleLinear()
        .domain(y_range)
        .range([height, 0]);

      // Add x-axis.
      const xAxis = g.append("g")
            .attr("transform", "translate(0," + yScale(0) + ")")
            .call(d3.axisBottom(xScale));

      // Add y-axis.
      g.append("g")
            .call(d3.axisLeft(yScale));


      var pathG = g.append("g").attr("clip-path","url(#"+clip_id+")")
      var paths = []

      for(let i=0; i<y.length; i++){
            const line = d3.line()
                  .x(d => xScale(d[x[0]][x[1]]))
                  .y(d => yScale(d[y[i][0]][y[i][1]]))

            let path = pathG.append("path")
                  .datum(data)
                  .attr("class", "line")

            paths.push(Object.assign(path.node(), {
                  update(){
                        d3.select(this)
                              .attr("d", line)
                  }
            }));
      }

      return Object.assign(svg.node(),{
            update(){
                  if(x[0] == "timestamp_us"){xScale.domain([data[0].timestamp_us,data[data.length-1].timestamp_us])}
                  xAxis.attr("transform", "translate(0," + yScale(0) + ")")
                        .call(d3.axisBottom(xScale));
                  for(let path of paths){
                        path.update()
                  }
            }
      })
      
}