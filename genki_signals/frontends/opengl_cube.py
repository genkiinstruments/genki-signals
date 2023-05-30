import numpy as np
import pyqtgraph.opengl as gl


cube_vertices = np.array(
    [
        [-0.5, -0.5, -0.5],
        [-0.5, -0.5, 0.5],
        [-0.5, 0.5, -0.5],
        [-0.5, 0.5, 0.5],
        [0.5, -0.5, -0.5],
        [0.5, -0.5, 0.5],
        [0.5, 0.5, -0.5],
        [0.5, 0.5, 0.5],
    ]
)

cube_faces = np.array(
    [
        [0, 1, 2],
        [1, 2, 3],
        [0, 1, 4],
        [1, 4, 5],
        [1, 3, 5],
        [3, 5, 7],
        [4, 5, 6],
        [5, 6, 7],
        [0, 2, 4],
        [2, 4, 6],
        [2, 3, 6],
        [3, 6, 7],
    ]
)

cube_colors = np.array(
    [
        [0, 1, 1, 0.4],
        [0, 1, 1, 0.4],
        [1, 0, 0, 0.4],
        [1, 0, 0, 0.4],
        [0, 1, 0, 0.4],
        [0, 1, 0, 0.4],
        [0, 0, 1, 0.4],
        [0, 0, 1, 0.4],
        [1, 0, 1, 0.4],
        [1, 0, 1, 0.4],
        [1, 1, 0, 0.4],
        [1, 1, 0, 0.4],
    ]
)


def cube_mesh():
    return gl.GLMeshItem(vertexes=cube_vertices, faces=cube_faces, faceColors=cube_colors, smooth=False)
