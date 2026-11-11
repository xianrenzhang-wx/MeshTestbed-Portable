import argparse
from mesh_testbed import Mesh

parser=argparse.ArgumentParser(description="Compute STL mesh metrics using the portable C++ library")
parser.add_argument("stl", nargs="?", help="Optional STL file; otherwise use a unit tetrahedron")
parser.add_argument("--show",action="store_true",help="Display with optional numpy + polyscope")
args=parser.parse_args()
mesh=Mesh(args.stl) if args.stl else Mesh.from_arrays(
    [(0,0,0),(1,0,0),(0,1,0),(0,0,1)],[(0,2,1),(0,1,3),(0,3,2),(1,2,3)])
with mesh:
    print("Vertices, triangles:",mesh.counts)
    print("Metrics:",mesh.metrics())
    if args.show:
        mesh.show()
