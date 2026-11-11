"""Run without optional dependencies: python analysis_demo.py"""
from mesh_testbed import Mesh
from mesh_testbed.analysis import tetrahedron
from mesh_testbed.bezier import curve, surface

v = [(0,0,0),(1,0,0),(0,1,0),(0,0,1)]
f = [(0,2,1),(0,1,3),(0,3,2),(1,2,3)]
result = tetrahedron([(0.2,0.2,0.2),(0,0,0),(2,2,2)], v)
assert result['states'] == [-1,0,1]
print('Tetrahedron:', result)
with Mesh.from_arrays(v, f) as mesh:
    properties = mesh.local_properties()
    assert abs(sum(properties['vertex_barycentric_areas'])-mesh.area()) < 1e-12
    assert len(mesh.unique_edges()['indices']) == 6
    print('Local properties:', properties)
    print('Unique edges:', mesh.unique_edges())
print('Bezier curve:', curve([(0,0,0),(1,0,0),(2,0,0),(3,0,0)], 3))
grid = [[(i,j,0) for j in range(4)] for i in range(4)]
vertices, faces = surface(grid, 2, 2)
assert len(vertices) == 9 and len(faces) == 8
print('Bezier surface:', len(vertices), 'vertices,', len(faces), 'triangles')
