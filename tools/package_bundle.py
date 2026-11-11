"""Assemble and smoke-test the complete portable runtime bundle."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NAME = "MeshTestbed-Portable-2.1.0-All-Platforms"
TARGETS = {
    "windows-x86_64": "mesh_core.dll",
    "linux-x86_64": "libmesh_core.so",
    "macos-arm64": "libmesh_core.dylib",
    "macos-x86_64": "libmesh_core.dylib",
}

QUICKSTART = (ROOT / 'USAGE.md').read_text(encoding='utf-8')


def main():
    entries = {}
    audit = json.loads((ROOT / "reports/release-2.1.0/packages.json").read_text(encoding="utf-8"))
    records = {r["target"]: r for r in audit["packages"]}
    for target, binary in TARGETS.items():
        folder = ROOT / "dist" / target
        for name in ("__init__.py", "geometry.py", "bezier.py", "analysis.py", binary):
            path = folder / "mesh_testbed" / name
            entries[f"{target}/mesh_testbed/{name}"] = path.read_bytes()
        digest = hashlib.sha256(entries[f"{target}/mesh_testbed/{binary}"]).hexdigest()
        assert digest == records[target]["binary_sha256"], target
        for name in ("demo.py", "manufacturing_demo.py", "analysis_demo.py"):
            entries[f"{target}/{name}"] = (ROOT / "examples" / name).read_bytes()
        for name in ("README.md", "GEOMETRY.md", "VALIDATION.md", "API.md", "USAGE.md", "CHANGELOG.md"):
            entries[f"{target}/{name}"] = (ROOT / name).read_bytes()
        for subdir in ("tests", "third_party_notices", "include"):
            for path in sorted((folder / subdir).rglob("*")):
                if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                    entries[f"{target}/{path.relative_to(folder).as_posix()}"] = path.read_bytes()
        entries[f"{target}/requirements-display.txt"] = b"# Optional visualization; versions tested on Windows Python 3.12.\nnumpy==2.3.5\npolyscope==2.6.1\n"
    entries["START_HERE.md"] = QUICKSTART.encode("utf-8")
    entries["BINARY_DEPENDENCIES.json"] = json.dumps([
        {key: r[key] for key in ("target", "architecture", "dependencies", "binary_sha256")}
        for r in audit["packages"]
    ], indent=2).encode("utf-8")
    entries["docs/MeshTestbed Portable.md"] = (ROOT / "MeshTestbed Portable.md").read_bytes()
    for path in (ROOT / "reports/release-2.1.0").glob("*"):
        if path.is_file(): entries[f"docs/release-2.1.0/{path.name}"] = path.read_bytes()
    entries["SHA256SUMS.txt"] = "".join(
        f"{hashlib.sha256(data).hexdigest()}  {name}\n" for name, data in sorted(entries.items())
    ).encode("utf-8")
    output = ROOT / "dist" / f"{NAME}.zip"
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(entries.items()):
            archive.writestr(f"{NAME}/{name}", data)
    results = []
    with tempfile.TemporaryDirectory(prefix="mesh-runtime-bundle-") as temp:
        with zipfile.ZipFile(output) as archive:
            assert archive.testzip() is None
            archive.extractall(temp)
        extracted = Path(temp) / NAME
        for name, data in entries.items():
            assert (extracted / name).read_bytes() == data, name
        env = dict(os.environ)
        env.pop("PYTHONPATH", None)
        env.pop("MESH_CORE_LIBRARY", None)
        for arguments in (["analysis_demo.py"], ["demo.py"], ["manufacturing_demo.py", "--layers", "3", "--output", "analysis.json"], ["-m", "unittest", "discover", "-s", "tests", "-v"]):
            run = subprocess.run([sys.executable, "-S", *arguments], cwd=extracted / "windows-x86_64", env=env, capture_output=True, text=True)
            results.append({"arguments": arguments, "returncode": run.returncode, "stdout": run.stdout, "stderr": run.stderr})
            if run.returncode:
                raise RuntimeError(run.stdout + run.stderr)
        analysis = json.loads((extracted / "windows-x86_64/analysis.json").read_text())
        assert abs(analysis["mass_properties"]["mass"] - 1.0) < 1e-10
        assert len(analysis["sections"]) == 3
        assert all(abs(s["area"] - 1.0) < 1e-10 for s in analysis["sections"])
    checksum = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(".zip.sha256").write_text(f"{checksum}  {output.name}\n", encoding="ascii")
    output.with_suffix(".validation.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(output)
    print(f"{output.stat().st_size} bytes; {len(entries)} files; archive and Windows examples/tests verified")
    print(results[-1]["stderr"][-250:])


if __name__ == "__main__":
    main()
