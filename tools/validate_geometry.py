"""Create reproducible real-model geometry and timing observations.

Set PYTHONPATH and MESH_CORE_LIBRARY as for the test suite. Timings are local
observations, not performance guarantees or comparisons with the old program.
"""
import argparse
import json
import platform
from pathlib import Path
import random
from time import perf_counter
from mesh_testbed import Mesh, MeshError

def main():
    root=Path(__file__).resolve().parents[1]
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models",type=Path,default=root.parent/"MeshTestbed_C++"/"STLs")
    parser.add_argument("--output",type=Path,default=root/"geometry_validation.json")
    args=parser.parse_args()
    files=sorted(args.models.glob("*.stl"))
    if not files:parser.error("No STL models found")
    report={"platform":platform.platform(),"python":platform.python_version(),"models":[]}
    for path in files:
        with Mesh(path) as mesh:
            row={"file":path.name,"counts":mesh.counts,"metrics":mesh.metrics()}
            low,high=row["metrics"]["bounds"]
            center=tuple((a+b)/2 for a,b in zip(low,high))
            row["mass_properties"]=mesh.mass_properties()
            # Build the BVH separately; timing includes Python/native boundary.
            start=perf_counter();mesh.nearest_points([center]);row["bvh_first_query_seconds"]=perf_counter()-start
            rng=random.Random(192)
            points=[tuple(rng.uniform(low[k],high[k]) for k in range(3)) for _ in range(10000)]
            start=perf_counter();result=mesh.nearest_points(points);row["nearest_10000_seconds"]=perf_counter()-start
            row["nearest_distance_range"]=[min(result["distances"]),max(result["distances"])]
            sec=mesh.section(center)
            row["mid_z_section"]={"origin":center,"contours":len(sec.polylines),"closed":sec.closed,
                                  "branches":sec.branch_vertices,"perimeter":sec.perimeter}
            try:row["mid_z_section"]["area"]=sec.area
            except MeshError as e:row["mid_z_section"]["area_error"]=str(e)
            report["models"].append(row)
            print(path.name,"faces",mesh.counts[1],"10000 queries",round(row["nearest_10000_seconds"],4),"s")
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False),encoding="utf-8")
    print("Saved",args.output)

if __name__=="__main__":main()
