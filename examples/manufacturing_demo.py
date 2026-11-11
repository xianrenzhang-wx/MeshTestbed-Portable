"""Run: python manufacturing_demo.py [model.stl] --layers 5 --output analysis.json

No optional Python packages needed. Output includes 3D section polylines, ready
for plotting or downstream processing. It is not a machine toolpath.
"""
import argparse
import json
from mesh_testbed import Mesh, MeshError

V=[(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1)]
F=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),
   (1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stl",nargs="?")
    parser.add_argument("--layers",type=int,default=5)
    parser.add_argument("--density",type=float,default=1)
    parser.add_argument("--output",help="Optional JSON output file")
    args=parser.parse_args()
    if args.layers<1:parser.error("--layers must be positive")
    with (Mesh(args.stl) if args.stl else Mesh.from_arrays(V,F)) as mesh:
        report={"counts":mesh.counts,"metrics":mesh.metrics(),"sections":[]}
        try:report["mass_properties"]=mesh.mass_properties(args.density)
        except MeshError as e:report["mass_error"]=str(e)
        low,high=report["metrics"]["bounds"]
        center=tuple((a+b)*.5 for a,b in zip(low,high))
        report["nearest_to_bounds_center"]=mesh.nearest_points([center])
        heights=[low[2]+(high[2]-low[2])*(i+.5)/args.layers for i in range(args.layers)]
        for sec in mesh.slices(heights):
            row={"z":sec.origin[2],"perimeter":sec.perimeter,"closed":sec.closed,
                 "branch_vertices":sec.branch_vertices,"polylines":sec.polylines}
            try:row["area"]=sec.area
            except MeshError as e:row["area_error"]=str(e)
            report["sections"].append(row)
    text=json.dumps(report,indent=2,allow_nan=False)
    if args.output:
        from pathlib import Path
        Path(args.output).write_text(text,encoding="utf-8")
        print(f"Saved {args.output}")
    else:print(text)

if __name__=="__main__":main()
