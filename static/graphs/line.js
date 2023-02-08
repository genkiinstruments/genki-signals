const arrayColumn = (arr, n) => arr.map(x => x[n]);

function make_chart(svg, x, y, x_range, y_range, row_based) {

  margin = { top: 20, right: 20, bottom: 20, left: 40 }

  width = +svg.attr("width") - margin.left - margin.right
  height = +svg.attr("height") - margin.top - margin.bottom

  g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");


  g.append("defs").append("clipPath")
    .attr("id", "clip")
  .append("rect")
    .attr("width", width)
    .attr("height", height);

  const xWalk = d3.scaleLinear()
    .domain(x_range)
    .range([0, width]);

  const yWalk = d3.scaleLinear()
    .domain(y_range)
    .range([0, height]);

  xAxis = g.append("g")
    .attr("class", "axis axis--x")  
    .attr("transform", "translate(0," + height / 2 + ")")
    .call(d3.axisBottom(xWalk));

  y_axis = g.append("g")
    .attr("class", "axis axis--y")
    .call(d3.axisLeft(yWalk));


  const line_row = d3.line()
    // .curve(d3.curveBasis)
    .x((d, i) => xWalk(i))
    .y((d, i) => yWalk(d));

  function trans(){return d3.transition().duration(1000).ease(d3.easeLinear, 2)}

  let paths = {}
  for (let key in y) {
    paths[key] = new Array(y[key].length)
    for (let j = 0; j < y[key].length; j++) {
      let col = y[key][j]

      // path_element = g.append("g").attr("clip-path", "url(#clip)")

      if(row_based){
        let path = g.append("g")
          .attr("clip-path", "url(#clip)")
          .append("path")
            .datum(data[key][col])
            .attr('class', 'line')
          .transition()
            .duration(1000)
            .ease(d3.easeLinear)
        

        paths[key][j] = Object.assign(path.node(), {
            update(data) {  
              d3.select(this)
                // .attr("transform", null)
                .attr("d", line_row)
                .attr("transform", null)
                .transition()
                .duration(990)
                .ease(d3.easeLinear)
                .attr("transform", "translate(" + xWalk(d3.min([xWalk.domain()[1] - data.length + 1, 0])) + ")")

              
              console.log(xWalk(d3.min([xWalk.domain()[1] - data.length + 1, 0])))
              // d3.active(this)
              //     .transition()
              //     .duration(990)
              //     .ease(d3.easeLinear)
              //     .attr("transform", "translate(" + xWalk(d3.min([xWalk.domain()[1] - data.length + 1, 0])) + ")")
                  
                // .transition()
                //   .duration(990)
                //   .ease(d3.easeLinear)
                //   .attr("transform", "translate(" + xWalk(-1) + ")")

              console.log(d3.select(this).data())
              
              console.log(d3.active(this))
              console.log(path)
              console.log(path.node())
              // d3.active(this)
              //     .attr("transform", "translate(" + xWalk(-1) + ",0)")
              //     .transition()
              //     .on("start",function(){console.log("transition")})

            }
        })
      }
      // else{
      //   const line = d3.line()
      //     .x((d, i) => t(i))
      //     .y((d, i) => yWalk(d[col]));

      //   let path = g.append("g")
      //     .append("path")
      //     .datum(data[key])
      //     .attr("class", "line")
      //     .attr("d", line)
      //     .transition(trans())
        
      //   paths[key][j] = Object.assign(path.node(), {
      //       update() {
      //         d3.select(this)
      //           .attr("d", line)
      //           .attr("transform", null)
      //           .transition(trans())
      //       }
      //   })
      // }
    }
  }

  return Object.assign(svg.node(), {
    update(data) {
      // y_range = [Number.INFINITY, Number.NEGATIVE_INFINITY]
      // for (key in y) {
      //   for (let col of y[key]) {
      //     y_range[0] = d3.min([d3.min(arrayColumn(data[key], col)), y_range[0]])
      //     y_range[1] = d3.max([d3.max(arrayColumn(data[key], col)), y_range[1]])
      //   }
      // }
      // yWalk.domain(y_range)
      // y_axis.call(d3.axisLeft(yWalk))
      // timestamp_us_min = data[x[0]][x[1]][0]
      // timestamp_us_max = data[x[0]][x[1]][data[x[0]][x[1]].length - 1]
      // xWalk.domain([timestamp_us_min ,timestamp_us_max])
      // xAxis.call(d3.axisBottom(xWalk));
      for (key in y) {
        for (let col of y[key]) {
          paths[key][col].update(data[key][col])
        }
      }
    }
  });
}