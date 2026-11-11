# Usage guide

## 1. Choose a release package

Select the ZIP matching both your operating system and Python process architecture.
Windows and Linux use x86_64. macOS packages are separate for Apple Silicon (ARM64)
and Intel (x86_64). The native artifacts were built and tested on Windows Server
2025, Ubuntu 22.04, and macOS 15. Compatibility with older operating systems is
not established by these tests. In particular, these are not the earlier Zig
cross-compiled Linux glibc 2.28 or macOS 13 packages.

The all-platforms ZIP contains the same four packages in separate directories.
Python is required but not bundled. Core computation has no third-party Python dependencies.

## 2. Run the examples

From the extracted platform directory:

```text
python demo.py
python analysis_demo.py
python manufacturing_demo.py --layers 5 --output analysis.json
python -m unittest discover -s tests -v
```

The examples construct their own geometry. A supplied model can be used with
`python demo.py path/to/part.stl`. Use python3 if required on your system.
The NumPy-specific test may skip when NumPy is absent; test STL fixtures are included.

## 3. Use the library in a project

Copy the entire mesh_testbed folder beside your script:

```python
from mesh_testbed import Mesh
from mesh_testbed.analysis import tetrahedron

vertices = [(0,0,0),(1,0,0),(0,1,0),(0,0,1)]
faces = [(0,2,1),(0,1,3),(0,3,2),(1,2,3)]
print(tetrahedron([(.2,.2,.2), (2,2,2)], vertices))
with Mesh.from_arrays(vertices, faces) as mesh:
    print(mesh.local_properties())
    print(mesh.unique_edges())
    print(mesh.mass_properties())
    mesh.save('tetrahedron.stl')
```

For an STL file, use `with Mesh('part.stl') as mesh:`. Units must be consistent.
Use tetrahedron for a batch against one four-vertex element; use classify_points
for a general closed mesh. Context managers release native resources.

## 4. Optional display

For CPython 3.11 matching the package architecture, install the bundled wheels offline:

```text
python -m pip install --no-index --find-links wheels -r requirements-display.txt
python demo.py --show
```

Other Python versions can install compatible wheels from PyPI:

```text
python -m pip install -r requirements-display.txt
```

Display requires a desktop OpenGL driver. Do not call show on a headless server.
Bundled wheel availability is checked during packaging; the current native CI does
not test interactive rendering or all driver configurations.

## 5. Troubleshooting

- Loader error: check OS, CPU/Python architecture, library location and system runtimes.
- Missing extension: replace the complete package; ABI 2 alone does not identify all features.
- Unexpected old behavior: check for a nearby old mesh_testbed copy or MESH_CORE_LIBRARY override.
- Solid operation rejected: inspect closure, winding and degenerate faces.
- Tetrahedron state 2: degenerate or nearly degenerate; weights cannot be used for interpolation.
- Vertex area mismatch: barycentric areas sum to total area; HW4 tile areas sum to one quarter.

## 6. Reproduce the release

The release workflow downloads the previously tested native artifacts, verifies
each binary against the corresponding suite.json SHA256, adds English documents,
optional display wheels, examples and test evidence, and creates release ZIPs.
It does not rebuild or substitute the tested dynamic libraries.
