"""Zip the four already-built targets and write SHA256 checksums."""
from pathlib import Path
import hashlib
import zipfile

def main():
    root=Path(__file__).resolve().parents[1]/"dist"
    libraries={"windows-x86_64":"mesh_core.dll","linux-x86_64":"libmesh_core.so",
               "macos-arm64":"libmesh_core.dylib","macos-x86_64":"libmesh_core.dylib"}
    for label,library in libraries.items():
        folder=root/label
        for required in (folder/"mesh_testbed"/library,folder/"mesh_testbed"/"geometry.py",folder/"GEOMETRY.md"):
            if not required.is_file():raise FileNotFoundError(required)
    records=[]
    for label in libraries:
        folder=root/label;dest=root/f"mesh-testbed-v2.1.0-{label}.zip"
        with zipfile.ZipFile(dest,"w",zipfile.ZIP_DEFLATED) as z:
            for p in sorted(folder.rglob("*")):
                if (p.is_file() and "__pycache__" not in p.parts
                        and p.suffix not in (".pyc",".lib",".pdb",".obj",".o") and p.name!="analysis.json"):
                    z.write(p,str(Path(label)/p.relative_to(folder)))
        records.append(hashlib.sha256(dest.read_bytes()).hexdigest()+"  "+dest.name)
        print(dest.name,dest.stat().st_size,"bytes")
    (root/"SHA256SUMS-v2.1.0.txt").write_text("\n".join(records)+"\n",encoding="ascii")

if __name__=="__main__":main()
