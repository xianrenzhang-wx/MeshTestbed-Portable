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

QUICKSTART = """# MeshTestbed Portable 使用说明

版本：2.1.0 / C ABI 2

## 选择平台

- Windows 64 位：windows-x86_64
- Linux x86_64：linux-x86_64（glibc 2.28+，不适用于 Alpine/musl）
- macOS Apple Silicon：macos-arm64（macOS 13+）
- macOS Intel：macos-x86_64（macOS 13+）

需要 Python 3.9+，Python 进程架构必须与动态库匹配。
Windows 已实际运行验证；Linux/macOS 已交叉编译和检查接口，原生运行验证待完成。

## 运行示例

解压后进入对应平台文件夹，在该文件夹打开终端：

```text
python demo.py
python analysis_demo.py
python manufacturing_demo.py --layers 5 --output analysis.json
python demo.py path/to/part.stl
python -m unittest discover -s tests -v
```

macOS/Linux 可将 python 替换为 python3。
前两个示例自动创建测试几何体，不需要外部模型。
demo.py 演示网格和几何属性；manufacturing_demo.py 演示质量属性、最近点、截面和多层切片，并可导出 JSON。
测试中缺少可选 NumPy 和原工程 STL 样本时，对应两项按预期跳过。

## 放入自己的 Python 项目

复制所选平台中的整个 mesh_testbed 文件夹到脚本旁边：

```python
from mesh_testbed import Mesh

with Mesh("part.stl") as mesh:
    print(mesh.area())
    print(mesh.mass_properties(density=1.0))
```

体积、质量属性等需要满足条件的实体网格。长度与密度单位应保持一致。
请一起复制 Python 文件和动态库，不要混用其他版本。

## 依赖

计算功能：所有项目运行文件已包含，无需安装第三方 Python 包、Visual Studio、MFC、CMake 或编译器。
Python 解释器和操作系统自带的运行库不随包分发。
Windows 使用系统 UCRT/Kernel32；Linux 使用系统 glibc、libm、libpthread、libdl 和加载器；macOS 使用系统 libSystem。
各二进制的具体依赖与校验值见 BINARY_DEPENDENCIES.json。

可选显示功能需要 NumPy 和 Polyscope：

```text
python -m pip install -r requirements-display.txt
python demo.py --show
```

requirements-display.txt 提供 Windows 已验证版本；其他平台和 Python 版本的可用 wheel 需由 pip 检查。
此压缩包不包含可选显示依赖的离线 wheel；安装显示依赖需要网络。
显示还需要可用的桌面图形环境及 OpenGL 驱动；纯计算无需显示依赖。

## 包内文件

每个平台目录包含动态库及 Python 接口、两个可直接运行的示例、测试、API 文档、第三方许可声明和可选依赖清单。
docs 内为项目技术方案与既有测试报告。SHA256SUMS.txt 可用于检查包内文件完整性。
"""


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
    entries["docs/test-report.html"] = (ROOT / "reports/full-test-2026-09-26/测试报告.html").read_bytes()
    # Retain the relative report link used by the project document.
    entries["docs/reports/full-test-2026-09-26/测试报告.md"] = (ROOT / "reports/full-test-2026-09-26/测试报告.md").read_bytes()
    for path in (ROOT / "reports/full-test-2026-09-26").glob("display-*.png"):
        entries[f"docs/reports/full-test-2026-09-26/{path.name}"] = path.read_bytes()
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
