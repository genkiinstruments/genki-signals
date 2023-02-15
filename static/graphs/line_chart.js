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



// var data = [];
// const buffer_len = 400;
// var visible_signal = "random";

// for (var i = 0; i < buffer_len; i++) {
//     data.push({
//         timestamp_us: i * 10000,
//         [visible_signal]: 0,
//         sampling_Rate: 0
//     });
// }

// const width = 640,
//       height = 400,
//       margin = { top: 20, right: 30, bottom: 30, left: 40};

// const x = d3.scaleLinear()
//       .domain([0, buffer_len])
//       .range([margin.left, width - margin.right]);

// const y = d3.scaleLinear()
//       .domain([-1, 1])
//       .range([height - margin.bottom, margin.top]);

// const xAxis = d3.axisBottom(x).ticks(width / 80).tickSizeOuter(0);
// const yAxis = d3.axisLeft(y).ticks(height / 40, ".2f");

// const line = d3.line()
//       .curve(d3.curveLinear)
//       .x((d, i) => x(i))
//       .y(d => y(d[visible_signal]));

// const svg = d3.select("svg")
//       .attr("width", width)
//       .attr("height", height)
//       .attr("viewBox", [0, 0, width, height])
//       .attr("style", "max-width: 100%; height: auto; height: intrinsic;");

// svg.append("g")
//     .attr("transform", `translate(0,${height - margin.bottom})`)
//     .call(xAxis);

// const yAx = svg.append("g")
//       .attr("transform", `translate(${margin.left},0)`)
//       .call(yAxis);

// const path = svg.append("path")
//       .attr("fill", "none")
//       .attr("stroke", "black")
//       .attr("stroke-width", 1.5)
//       .attr("stroke-opacity", 1)
//       .attr("d", line(data));


// var socket = io();
// socket.on('data', function(new_points) {
//     new_points.forEach(d => data.push(d));
//     while (data.length > buffer_len) {
//         data.shift();
//     }

//     y.domain(d3.extent(data, d => d[visible_signal]));
//     yAx.call(yAxis);

//     path.attr("d", line(data));
// });



