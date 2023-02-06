const arrayColumn = (arr, n) => arr.map(x => x[n]);

function make_chart(svg, y, x_range, y_range){

    margin = { top: 20, right: 20, bottom: 20, left: 40 }

    width = +svg.attr("width") - margin.left - margin.right
    height = +svg.attr("height") - margin.top - margin.bottom

    g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    const t = d3.scaleLinear()
        .domain(x_range)
        .range([ 0, width ]);
    g.append("g")
        .attr("transform", "translate(0," + height/2 + ")")
        .call(d3.axisBottom(t));

    const yWalk = d3.scaleLinear()
        .domain(y_range)
        .range([ 0, height ]);
    y_axis = g.append("g")
        .call(d3.axisLeft(yWalk)); 

    
    let paths = {}
    for(let key in y){
      paths[key] = new Array(y[key].length)
      for(let j=0; j<y[key].length; j++){
        let col = y[key][j]
        const line = d3.line()
        .x((d, i) => t(i))
        .y((d, i) => yWalk(d[col]));

        let path_element = g.append("g")

        let path = path_element
            .append("path")
            .datum(data[key])
            .attr("class", "line")
            .attr("d", line)
          

        paths[key][j] = Object.assign(path_element.node(), {
          update(){
            path = path
                .attr("d", line)
                .attr("transform", null)
          }
        })
      }
    }

    return Object.assign(svg.node(), {
        update(data) {
            y_range = [Number.INFINITY, Number.NEGATIVE_INFINITY]
            for(key in y){
              for(let col of y[key]){
                y_range[0] = d3.min([d3.min(arrayColumn(data[key],col)), y_range[0]])
                y_range[1] = d3.max([d3.max(arrayColumn(data[key],col)), y_range[1]])
              }
            }
            yWalk.domain(y_range)
            y_axis.call(d3.axisLeft(yWalk))
            for(key in paths){
              for(const path of paths[key]){
                path.update()
              }
            }
        }
    });
  }