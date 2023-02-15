function quaternion_to_mat4(m, q){
    let x = q[1]
    let y = q[2]
    let z = q[3]
    let s = q[0]

    let x2  = x + x;
    let y2  = y + y;
    let z2  = z + z;
    let xx2 = x * x2;
    let xy2 = x * y2;
    let xz2 = x * z2;
    let yy2 = y * y2;
    let yz2 = y * z2;
    let zz2 = z * z2;
    let sx2 = s * x2;
    let sy2 = s * y2;
    let sz2 = s * z2;

    // build 4x4 matrix (column-major) and return
    m[0] = 1 - (yy2 + zz2)
    m[1] = xy2 + sz2
    m[2] = xz2 - sy2
    m[3] = 0 // column 0
    m[4] = xy2 - sz2 
    m[5] = 1 - (xx2 + zz2)
    m[6] = yz2 + sx2
    m[7] = 0 // column 1
    m[8] = xz2 + sy2
    m[9] = yz2 - sx2     
    m[10] = 1 - (xx2 + yy2)
    m[11] = 0 // column 2
    m[12] = 0
    m[13] = 0
    m[14] = 0
    m[15] = 1 // column 3
}

export function create_cube(data, divname, id, width, height){
    let margin = { top: 20, right: 20, bottom: 30, left: 40 };


    d3.select(divname)
        .append("canvas")
            .attr("id", id)
            .attr("width", width)
            .attr("height", height)

    var canvas = document.getElementById(id);

    let gl = canvas.getContext('webgl');

    var vertices = [
        -1,-1,-1, 1,-1,-1, 1, 1,-1, -1, 1,-1,
        -1,-1, 1, 1,-1, 1, 1, 1, 1, -1, 1, 1,
        -1,-1,-1, -1, 1,-1, -1, 1, 1, -1,-1, 1,
        1,-1,-1, 1, 1,-1, 1, 1, 1, 1,-1, 1,
        -1,-1,-1, -1,-1, 1, 1,-1, 1, 1,-1,-1,
        -1, 1,-1, -1, 1, 1, 1, 1, 1, 1, 1,-1, 
    ];

    let face_colors = [[1,0,0],[0,1,0],[0,0,1],[1,1,0],[1,0,1],[0,1,1]]

    var colors = []
    for(let c of face_colors){
        colors = colors.concat(c,c,c,c)
    }

    var indices = [
        0,1,2, 0,2,3, 4,5,6, 4,6,7,
        8,9,10, 8,10,11, 12,13,14, 12,14,15,
        16,17,18, 16,18,19, 20,21,22, 20,22,23 
    ];

    // Create and store data into vertex buffer
    var vertex_buffer = gl.createBuffer ();
    gl.bindBuffer(gl.ARRAY_BUFFER, vertex_buffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(vertices), gl.STATIC_DRAW);

    // Create and store data into color buffer
    var color_buffer = gl.createBuffer ();
    gl.bindBuffer(gl.ARRAY_BUFFER, color_buffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(colors), gl.STATIC_DRAW);

    // Create and store data into index buffer
    var index_buffer = gl.createBuffer ();
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, index_buffer);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, new Uint16Array(indices), gl.STATIC_DRAW);

    /*=================== SHADERS =================== */

    var vertCode = 'attribute vec3 position;'+
    'uniform mat4 Pmatrix;'+
    'uniform mat4 Vmatrix;'+
    'uniform mat4 Mmatrix;'+
    'attribute vec3 color;'+//the color of the point
    'varying vec3 vColor;'+
    'void main(void) { '+//pre-built function
        'gl_Position = Pmatrix*Vmatrix*Mmatrix*vec4(position, 1.);'+
        'vColor = color;'+
    '}';

    var fragCode = 'precision mediump float;'+
    'varying vec3 vColor;'+
    'void main(void) {'+
        'gl_FragColor = vec4(vColor, 1.);'+
    '}';

    var vertShader = gl.createShader(gl.VERTEX_SHADER);
    gl.shaderSource(vertShader, vertCode);
    gl.compileShader(vertShader);

    var fragShader = gl.createShader(gl.FRAGMENT_SHADER);
    gl.shaderSource(fragShader, fragCode);
    gl.compileShader(fragShader);

    var shaderprogram = gl.createProgram();
    gl.attachShader(shaderprogram, vertShader);
    gl.attachShader(shaderprogram, fragShader);
    gl.linkProgram(shaderprogram);

    /*======== Associating attributes to vertex shader =====*/
    var _Pmatrix = gl.getUniformLocation(shaderprogram, "Pmatrix");
    var _Vmatrix = gl.getUniformLocation(shaderprogram, "Vmatrix");
    var _Mmatrix = gl.getUniformLocation(shaderprogram, "Mmatrix");

    gl.bindBuffer(gl.ARRAY_BUFFER, vertex_buffer);
    var _position = gl.getAttribLocation(shaderprogram, "position");
    gl.vertexAttribPointer(_position, 3, gl.FLOAT, false,0,0);
    gl.enableVertexAttribArray(_position);

    gl.bindBuffer(gl.ARRAY_BUFFER, color_buffer);
    var _color = gl.getAttribLocation(shaderprogram, "color");
    gl.vertexAttribPointer(_color, 3, gl.FLOAT, false,0,0) ;
    gl.enableVertexAttribArray(_color);
    gl.useProgram(shaderprogram);

    /*==================== MATRIX ====================== */

    function get_projection(angle, a, zMin, zMax) {
    var ang = Math.tan((angle*.5)*Math.PI/180);//angle*.5
    return [
        0.5/ang, 0 , 0, 0,
        0, 0.5*a/ang, 0, 0,
        0, 0, -(zMax+zMin)/(zMax-zMin), -1,
        0, 0, (-2*zMax*zMin)/(zMax-zMin), 0 
        ];
    }

    var proj_matrix = get_projection(40, canvas.width/canvas.height, 1, 100);
    var mo_matrix = [ 1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1 ];
    var view_matrix = [ 1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1 ];

    view_matrix[14] = view_matrix[14]-6;

    return Object.assign(canvas, {
        // expects a single quaternion
        update(data){
            let rotation = data[data.length-1]["current_pose"]
            quaternion_to_mat4(mo_matrix, rotation)
            gl.enable(gl.DEPTH_TEST);

            gl.depthFunc(gl.LEQUAL);

            gl.clearColor(1, 1, 1, 1);
            gl.clearDepth(1.0);
            gl.viewport(0.0, 0.0, canvas.width, canvas.height);
            gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

            gl.uniformMatrix4fv(_Pmatrix, false, proj_matrix);
            gl.uniformMatrix4fv(_Vmatrix, false, view_matrix);
            gl.uniformMatrix4fv(_Mmatrix, false, mo_matrix);

            gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, index_buffer);
            gl.drawElements(gl.TRIANGLES, indices.length, gl.UNSIGNED_SHORT, 0);
        }
    });
}