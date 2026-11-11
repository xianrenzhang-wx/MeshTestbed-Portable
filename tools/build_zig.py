"""Optional cross compiler build. Requires Zig 0.14.1 executable; no global install.

python tools/build_zig.py --zig /path/to/zig --target linux-x86_64
Cross compilation is not a substitute for running tests on the target OS.
"""
import argparse
from pathlib import Path
import shutil
import subprocess

TARGETS={
    "windows-x86_64":("x86_64-windows-gnu","mesh_core.dll",["-static"]),
    "linux-x86_64":("x86_64-linux-gnu.2.28","libmesh_core.so",["-fPIC"]),
    "macos-arm64":("aarch64-macos","libmesh_core.dylib",[]),
    "macos-x86_64":("x86_64-macos","libmesh_core.dylib",[]),
}
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zig",default="zig")
    parser.add_argument("--target",choices=TARGETS,required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    target,name,flags=TARGETS[args.target]
    out=root/"dist"/args.target; package=out/"mesh_testbed"
    package.mkdir(parents=True,exist_ok=True)
    subprocess.run([args.zig,"c++","-target",target,"-std=c++17","-O2","-shared",
                    *flags,"-I",str(root/"include"),str(root/"src"/"mesh_core.cpp"),str(root/"src"/"mesh_geometry.cpp"),str(root/"src"/"mesh_bezier.cpp"),str(root/"src"/"mesh_analysis.cpp"),
                    "-o",str(package/name)],check=True)
    for source in (root/"python"/"mesh_testbed").glob("*.py"):
        shutil.copy2(source,package)
    shutil.copy2(root/"examples"/"demo.py",out)
    shutil.copy2(root/"examples"/"manufacturing_demo.py",out)
    shutil.copy2(root/"examples"/"analysis_demo.py",out)
    for doc in ("README.md","VALIDATION.md","GEOMETRY.md","API.md","USAGE.md","CHANGELOG.md","API.md","USAGE.md","CHANGELOG.md","geometry_validation.json"):
        if (root/doc).exists():shutil.copy2(root/doc,out)
    shutil.copytree(root/"include",out/"include",dirs_exist_ok=True)
    shutil.copytree(root/"tests",out/"tests",dirs_exist_ok=True,ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(root/"third_party_notices",out/"third_party_notices",dirs_exist_ok=True)
    print(f"Built {out}; run python -m unittest discover -s tests -v on the target OS.")

if __name__=="__main__":main()
