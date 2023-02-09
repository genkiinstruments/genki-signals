function quaternion_multiplication(r,s){
    return [
        r[0]*s[0] - r[1]*s[1] - r[2]*s[2] - r[3]*s[3],
        r[0]*s[1] + r[1]*s[0] + r[2]*s[3] - r[3]*s[2],
        r[0]*s[2] - r[1]*s[3] + r[2]*s[0] + r[3]*s[1],
        r[0]*s[3] + r[1]*s[2] - r[2]*s[1] + r[3]*s[0],
    ]
}

function rotate(p, q){
    let q_inv = [q[0], -q[1], -q[2], -q[3]]
    let q_invp = quaternion_multiplication(q_inv,p)
    let q_invpq = quaternion_multiplication(q_invp, q)
    return [0, ...q_invpq.slice(1,4)]
}

// camera 
//cube position is translated by (0,0,cube)
//screen is at (0,0,0)
//camera is at (0,0,camera_z)
//translate by cube position on screen with cube_center
function project(p, camera_z, cube_center, width, height){
    let lower_dim = d3.min([width, height])
    return [
        (p[1])/(p[3] - camera_z) * lower_dim/2 + cube_center[0],
        (p[2])/(p[3] - camera_z) * lower_dim/2 + cube_center[1],
    ] 
}

export function create_cube(data, divname, id, width, height){
    
    let margin = { top: 20, right: 20, bottom: 30, left: 40 };
    var svg = d3.select(divname)
        .append("svg")
            .attr("id", id)
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)

    var g = svg
        .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    let cr = d3.min([width,height]) / 4
    let cc = [width/2, height/2]


    let vertices = [
        [0, -cr, -cr, +cr],
        [0, -cr, -cr, -cr],
        [0, +cr, -cr, -cr],
        [0, +cr, -cr, +cr],
        [0, +cr, +cr, +cr],
        [0, +cr, +cr, -cr],
        [0, -cr, +cr, -cr],
        [0, -cr, +cr, +cr],
    ]

    var vertices_2d = []

    for(let vertice of vertices){
        vertices_2d.push(project(vertice, -4*cr, cc, width, height))
    }

    let vertices_to_faces = [
        [0, 1, 2, 3, 0],
        [3, 2, 5, 4, 3],
        [4, 5, 6, 7, 4],
        [7, 6, 1, 0, 7],
        [7, 0, 3, 4, 7],
        [1, 6, 5, 2, 1],
    ]

    var faces_2d = vertices_to_faces.map(vtf => vtf.map(x => vertices_2d[x]))   

    var line = d3.line()
        .x(d => d[0])
        .y(d => d[1]);

    let facesG = []

    for(let face of faces_2d){
        facesG.push(
            g.append("g")
                .append("path")
                .datum(face)
                .style("fill", "#0073e5")
                .style("fill-opacity", "0.3")
                .attr("stroke", "black")
                .attr("d", line)
        )
    }
    

    return Object.assign(svg.node(), {
        update(data) {
            for(let i = 0; i < vertices.length; i++){
                let vr = rotate(vertices[i], data)
                vertices_2d[i] = project(vr, -4*cr, cc, width, height)
            }
            d3.range(6).map(i => {d3.range(5).map(j => {faces_2d[i][j] = vertices_2d[vertices_to_faces[i][j]]})})
            for(let face of facesG){
                face = face.attr("d",line)
            }
        }
    })

}