"""Write English release documentation and evidence-based historical reports."""
from pathlib import Path
import json
import html

ROOT = Path(__file__).resolve().parents[1]
RUN = 'https://github.com/xianrenzhang-wx/MeshTestbed-Portable/actions/runs/42992820689'
DOCS = {
'README.md': '''# MeshTestbed Portable 2.1.0

A standard C++17 geometry library with a lightweight Python ctypes interface.
Core computation requires no third-party Python packages or compiler on the user's machine.

## Download and start

Download a platform ZIP from [GitHub Releases](https://github.com/xianrenzhang-wx/MeshTestbed-Portable/releases).
Choose Windows x86_64, Linux x86_64, macOS ARM64, or macOS x86_64. Extract the ZIP,
open a terminal in its directory, and run:

```text
python demo.py
python analysis_demo.py
python manufacturing_demo.py --layers 5 --output analysis.json
```

Use python3 where appropriate. Python 3.9+ is supported by the wrapper; the native
release was tested with CPython 3.11. The bundled optional display wheels target
CPython 3.11 only. Python and operating-system runtimes are not bundled.

## Features

- Binary/ASCII STL loading, indexed meshes, halfedges, and mesh diagnostics.
- Area, volume, bounds, uniform-density mass, centroid, and inertia tensor.
- Affine transforms, nearest points, signed distances, inside/outside classification.
- Mesh surface distance, collision/containment, plane sections, and multilayer slicing.
- Batch tetrahedron predicates and barycentric coordinates.
- Face centroids/normals/areas, unique edges/midpoints, and two vertex area definitions.
- Cubic curves and bicubic surface sampling with triangle output.
- Python STL export and optional NumPy/Polyscope visualization.

## Documentation

- [Usage and installation](USAGE.md)
- [API and C ABI reference](API.md)
- [Geometry conventions and limitations](GEOMETRY.md)
- [Dependencies](DEPENDENCIES.md)
- [Native CI results](CI_REPORT.md)
- [Validation history](VALIDATION.md)
- [Architecture and roadmap](MeshTestbed%20Portable.md)
- [Changes](CHANGELOG.md)

## Build from source

Requires CMake 3.20+, a C++17 compiler, and Python. MFC is not required.

```text
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release --parallel
ctest --test-dir build -C Release --output-on-failure
cmake --install build --config Release --prefix dist
```

Install NumPy to exercise optional array tests. On Windows, MSVC uses a static
C/C++ runtime. Linux and macOS native compiler runtimes remain system dependencies.
Copy the entire mesh_testbed directory into your Python project. Do not mix versions.

## Scope and provenance

The library independently reimplements selected calculations from the original
MeshTestbed teaching project (whose source identifies Yong CHEN, 12/05), while
preserving the original project separately. Legacy MFC menus, dialogs and all
auxiliary predicates are not ported. This is not a complete CAD kernel, FEM solver,
or CAM toolpath system. See third_party_notices for included toolchain notices.

STL coordinates weld only on exact equality. Array input does not weld. Solid
operations require valid closed oriented input; self-intersection is not fully
certified. Coordinate and density units are the caller's responsibility. Each Mesh
serializes native access; independent instances may execute concurrently.
''',
'USAGE.md': '''# Usage guide

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
''',
'DEPENDENCIES.md': '''# Runtime dependencies

## Core computation

Python 3.9+ and a matching operating system/CPU architecture are required.
Native CI used Python 3.11. No NumPy, MFC, Visual Studio, compiler, CUDA or MATLAB
installation is needed for core computation. Python is not included.

Operating-system libraries are required and are not redistributed. Windows uses
Windows system DLLs (including the Universal C Runtime where imported); the MSVC
build uses a static C/C++ runtime. The Linux GCC build uses glibc, libstdc++ and
other system libraries reported in BINARY_DEPENDENCIES.json. macOS uses system
libraries such as libSystem and libc++. Do not copy the earlier cross-build
dependency assumptions onto these native CI artifacts.

The packages were tested on Windows Server 2025, Ubuntu 22.04, and macOS 15.
See BINARY_DEPENDENCIES.json for inspected imports, architecture and hash.
No broader minimum-OS compatibility is claimed beyond the test environments.

## Optional display

- NumPy 2.3.5
- Polyscope 2.6.1
- A working desktop graphics environment and OpenGL driver

Each platform ZIP contains wheels for CPython 3.11 of that architecture, including
dependencies resolved by pip. Install using requirements-display.txt and the local
wheels directory. Wheel contents retain upstream license and metadata files.
Other Python versions require a matching online installation or separate wheels.
GPU/driver software and Python itself are not included.

## Development only

CMake 3.20+ and a C++17 compiler build the library. NumPy enables optional tests.
Release inspection uses pefile and macholib plus the runner's readelf tool.
These inspection tools are not required by end users.
''',
'GEOMETRY.md': '''# Mesh geometry and manufacturing analysis

The C++17 core implements triangle-mesh calculations. Python stitches section
contours and computes contour area/perimeter. It is not a complete CAD/CAE/CAM system.

## Example

```python
from mesh_testbed import Mesh
with Mesh('part.stl') as part:
    props = part.mass_properties(density=1.0)
    result = part.nearest_points([(0,0,0),(1,2,3)])
    states = part.classify_points([(0,0,0)])  # -1 inside, 0 boundary, +1 outside
    sec = part.section(origin=(0,0,.5), normal=(0,0,1))
    print(sec.polylines, sec.closed, sec.perimeter)
    print(sec.area)  # Rejects invalid/open/branched/crossing contours.
    for layer in part.slices([.1,.2,.3], axis='z'):
        print(layer.origin, layer.polylines)
```

## Queries and conditions

| Interface | Result | Conditions |
|---|---|---|
| mass_properties(density) | volume, mass, centroid, inertia | Closed oriented nondegenerate solid, positive uniform density |
| nearest_points(points) | distances, points, face_ids | Open meshes allowed; degenerate triangles reduce to segments/points |
| nearest_points(points,signed=True) | Negative inside, positive outside, zero within tolerance | Closed oriented mesh |
| classify_points(points) | -1 / 0 / +1 | Closed oriented mesh |
| contains(points) | Boolean list | Boundary included unless include_boundary=False |
| distance_to(other) | Surface distance and face_ids | Nondegenerate meshes |
| collision(other) | collides, kind, face_ids | Solid by default; containment counts |
| collision(other,solid=False) | Surface contact/intersection only | Open meshes allowed |
| section(origin,normal) | Section object | Nonzero normal; open meshes allowed; degenerate faces rejected |
| slices(heights,axis) | Generator of Sections at absolute coordinates | axis x/y/z |

NumPy output arrays and Section objects own their data and survive mesh closure.
See API.md for signatures, new tetrahedron queries and local mesh properties.

## Mass, inertia and units

STL has no unit metadata. Coordinates in metres and density in kg/m³ produce kg
and kg·m². Inertia is a 3x3 tensor about the centroid in current world axes, with
negative products of inertia off the diagonal. Reversing all faces does not change
positive mass, but cavity shells must oppose exterior winding and disconnected
solids need consistent orientation. Signed tetrahedral integration computes volume
moments using a local reference to reduce cancellation under large translations.

## Distances and collisions

Surface distance can be positive for a solid fully contained in another. Collision
kind is separated, surface_contact (including intersection), or containment.
Containment returns no contact face pair (None). Face indices refer to the current
triangle array, not persistent CAD identities. No penetration depth, continuous
collision, swept volume, contact force or tool compensation is computed.

Default spatial tolerance is 1e-9 in coordinate units. Collision inflates SAT
projection intervals; this is not an exact Euclidean clearance. Use distance_to
and a separate containment check for clearance. Cached AABB/BVH indices are
invalidated by transforms and rebuilt lazily. Triangle distance considers face,
edge and vertex regions; pair queries also consider edge-edge distances. SAT
includes coplanar cases. Signed queries use full triangle solid-angle sums,
O(triangles) per point, not a fast approximate winding algorithm.

## Sections and slices

The plane normal is normalized. Native segments are stitched with tolerance-based
endpoint merging and duplicate-edge removal; a closed polyline repeats its first
point. Coplanar face regions contribute exterior boundaries, excluding internal
triangulation diagonals. Isolated tangent points produce no segment; tangent edges
can produce open segments. Results are preprocessing geometry, not machine toolpaths.

Section.area uses even-odd nesting and supports holes. Open, branched, crossing,
touching or collapsed contours are rejected; perimeter also measures open polylines.
The supplied Cow model has crossing contours at its mid-Z plane, so area is rejected.
Closed edge topology alone does not prove a valid solid. Python contour intersection
checks are worst-case quadratic in segment count; native plane queries use BVH
pruning. The slicing generator avoids holding all layers at once.

## Precision and scope

These are floating-point algorithms, not exact predicates. Choose reasonable
scales and tolerances; excessive tolerances can merge small features. Validation
does not fully detect self-intersections, vertex-manifold defects or shell errors.
STEP/IGES/BREP kernels, solid Booleans, volume meshing, FEM, three-/five-axis
toolpaths and G-code are not implemented. Tetrahedron tolerances are dimensionless,
unlike spatial mesh tolerances; see API.md.

## Mathematical references

Independent implementation; these references are not runtime dependencies:

- [Eberly: point-triangle distance](https://www.geometrictools.com/Documentation/DistancePoint3Triangle3.pdf)
- [Eberly: polyhedral mass properties](https://www.geometrictools.com/Documentation/PolyhedralMassProperties.pdf)
- [Eberly: separating axes](https://www.geometrictools.com/Documentation/MethodOfSeparatingAxes.pdf)
- [CGAL: mesh slicing conventions](https://doc.cgal.org/latest/PMP_Boolean_operations/classCGAL_1_1Polygon__mesh__slicer.html)
''',
'VALIDATION.md': '''# Validation history

## Current native validation: 2.1.0

On 2026-11-11, GitHub Actions built the library natively on Windows x86_64,
Ubuntu 22.04 x86_64, macOS 15 ARM64 and macOS 15 Intel. Each target passed all
82 tests with no failures, errors or skips. CTest, installed-package tests and
three examples also passed. See CI_REPORT.md for the immutable tested commit
and run link. Interactive rendering was not tested by this workflow.

## Local 2.1.0 validation

The Windows source suite passed 82 tests. Original HW4/HW6/HW7 compatibility suites
passed 4/10/14 tests against the updated DLL. Independent HW4 geometry and 1,000
HW7 random-point comparisons agreed with the original Python calculations.
The earlier minimal local ZIP passed 80 tests with two expected skips; current
native CI includes NumPy and all five fixtures, so no tests were skipped.

## Historical 2.0.1 validation (2026-09-26)

The Windows suite expanded from 51 to 67 passing tests. Fixes addressed large-offset
section area cancellation, destructive failed STL exports and ASCII parsing after
NumPy initialization. Real Polyscope 2.6.1/OpenGL 3.3 rendering was exercised twice,
including a transformed model and camera reset. Manual interaction, all drivers,
and headless rendering were not certified. Historical extracted packages passed
65 tests and skipped two. Linux/macOS were only cross-compiled at that time.

Five teaching meshes (Cow, cube_in, Cylinder, foot, turbine_blade) were checked.
Historical 10,000-point unsigned query observations ranged from roughly 0.019 to
0.101 seconds after BVH construction. These are single-machine observations, not
hardware-independent performance promises or comparisons against the legacy app.
Cow's crossing section contours were intentionally rejected for area computation.

The old Zig binaries had different runtime dependencies and minimum targets from
the native CI release. Native validation does not retroactively validate those
old binaries. See DEPENDENCIES.md and each release manifest for the current files.
''',
}

def table(suite):
    return '\n| Test | Status | Seconds |\n|---|---|---|\n' + ''.join(
        f"| `{c['id']}` | {c['status']} | {c['seconds']:.6f} |\n" for c in suite['cases'])

def main():
    for name, content in DOCS.items():
        if name == 'README.md': continue
        (ROOT/name).write_text(content, encoding='utf-8')
    ci = f'''# Native CI test report — 2.1.0

Date: 2026-11-11. Tested commit: `0525fb168bd513c37c41b200b8d6dceca98231d1`.

[Workflow run and artifacts]({RUN})

| Target | Compiler | Python | Results |
|---|---|---|---|
| Windows x86_64 | MSVC 19.51 | 3.11.9 | 82 passed; 0 failures/errors/skips |
| Ubuntu 22.04 x86_64 | GCC 11.4 | 3.11.18 | 82 passed; 0 failures/errors/skips |
| macOS 15 ARM64 | AppleClang 17 | 3.11.9 | 82 passed; 0 failures/errors/skips |
| macOS 15 Intel | AppleClang 17 | 3.11.9 | 82 passed; 0 failures/errors/skips |

Each job completed native CMake compilation, CTest, installation, three examples,
installed-package unittest discovery, and a recorded JSON/log test run. NumPy 2.3.5
and five STL fixtures were available. Each platform artifact contains its native
library, Python modules, examples, headers, tests and documentation.

This verifies computation, not interactive OpenGL rendering. It does not certify
all OS versions or earlier cross-compiled binaries. The Release packages preserve
these exact tested native binaries and record their SHA256 against suite.json.

The original Actions artifacts expire on 2027-02-09. GitHub Releases provides the
packaged downloads independently of Actions artifact retention.

Historical local reports remain useful evidence but their pending-platform status
is superseded by this native run. See VALIDATION.md for the chronology.
'''
    (ROOT/'CI_REPORT.md').write_text(ci,encoding='utf-8')
    for dirname, filename, intro in [
        ('release-2.1.0','suite.json','''# Local completion and test report — 2.1.0

Date: 2026-11-11. Scope: HW4 local mesh properties, HW7 tetrahedron predicates,
Bézier distribution consistency and regression of existing geometry APIs.

Implemented batch classification/weights/degeneracy, face properties, unique edges,
two explicitly named vertex area measures, native version export and ABI-2 additive
interfaces. Original homework applications remain unchanged as references.
No FEM/topology optimizer, AI runtime, point-triangle or point-plane public API was added.

Windows: 82/82 main tests passed with no skips. Original compatibility suites passed
4 HW4, 10 HW6 and 14 HW7 tests. The Cylinder face centroids, midpoints and HW4 tile
areas agreed with original Python; 1,000 random tetrahedron queries (seed 211)
agreed in states and weights. These checks overlap; their counts are not additive
independent-feature coverage. The earlier extracted local package passed 80 tests
and skipped two because NumPy and original model fixtures were not included.

Fifteen added tests cover analytic states/weights, 300 affine-transformed random
points, large/small scales, degeneracy, tolerances, invalid inputs, empty batches,
analytic triangle properties, partition sums, transforms, isolated vertices,
resource lifetime, short/null native buffers and Bézier analytic/invalid cases.
The previous 67 tests cover STL, topology, mass, transforms, distances, collision,
sections, slicing, concurrency and resource management.

Integration fixes: synchronized previously missing Bézier exports in packages;
separated HW4 tile area (sum = total area/4) from barycentric area (sum = total area);
corrected a comparison-script import path shadowed by an old homework package;
updated historical-hash-bound packaging scripts for the new release.

At the time of local verification, non-Windows execution remained pending. It has
since passed in native CI; see ../../CI_REPORT.md. Interactive GUI rendering was
not repeated for 2.1.0. No memory-sanitizer run, exact-predicate proof or new speed
benchmark was performed. Floating-point and solid-input limitations remain.

Evidence: suite.json/suite.log, homework logs, homework_comparison.json and packages.json.
Run tools/run_test_suite.py with PYTHONPATH and MESH_CORE_LIBRARY set to the intended package.
'''),
        ('full-test-2026-09-26','final-suite.json','''# Historical full test report — 2.0.1

Date: 2026-09-26. Windows 11 x86_64, Python 3.12.14, Zig 0.14.1/Clang 19.1.7,
CMake/Ninja. The original 51 tests passed; 16 additional tests exposed three defect
categories. After repairs all 67 tests passed with no failures, errors or skips.
Extracted minimal Windows packages passed 65 and skipped two expected optional cases.

Fixed: section-area cancellation at large coordinate offsets, partial/destructive
STL export on float32 overflow, and ASCII STL parsing affected by initialization
order when mixed with NumPy. Export now prevalidates and atomically replaces the
destination; ASCII numeric parsing uses an independent C locale. A test harness
pointer mistake was fixed separately and was not a product defect.

Polyscope 2.6.1 with NumPy 2.3.5 used the real openGL3_glfw backend, OpenGL 3.3.0
driver Build 32.0.101.8132. Two bounded render sessions produced 960x720 screenshots,
including a rotated Cow mesh. Repeated initialization was guarded and the camera
reset after registration. This did not test all controls, drivers or headless use.

Analytic solids, 500 random cube points, 200 transformed random queries, 80 random
box pairs, STL corruption/roundtrips, topology, resource lifetime, concurrency,
1,000 create/query/free cycles and native buffer errors were covered. Cow,
cube_in, Cylinder, foot and turbine_blade were evaluated. Cow's crossing mid-Z
contours were returned but area was rejected. Mass output is not a validity certificate.

Linux and macOS were cross-compiled and their exports inspected, without native
runtime execution at this historical date. Later native results are in CI_REPORT.md.
No full CAD/CAE/CAM certification, exact geometry proof, memory-leak proof or
complete code-coverage claim follows from these tests. The complete recorded
per-test results below retain the original evidence.
''')]:
        folder=ROOT/'reports'/dirname
        if not (folder/filename).exists():continue
        suite=json.loads((folder/filename).read_text(encoding='utf-8'))
        content=intro+f"\nNative DLL SHA256: `{suite['library_sha256']}`\n"+table(suite)
        (folder/'TEST_REPORT.md').write_text(content,encoding='utf-8')
        # Keep existing historical filenames compatible, but make their contents English.
        for p in folder.glob('*.md'):
            p.write_text(content,encoding='utf-8')
        for p in [folder/'TEST_REPORT.html',*folder.glob('*.html')]:
            p.write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Test report</title><style>body{max-width:1100px;margin:40px auto;font:15px/1.6 system-ui}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style><pre>'+html.escape(content)+'</pre></html>',encoding='utf-8')
    p=ROOT/'MeshTestbed Portable.md'
    s=p.read_text(encoding='utf-8').replace('[full test report (Chinese)](reports/full-test-2026-09-26/测试报告.md)', '[full test report](reports/release-2.1.0/TEST_REPORT.md)')
    p.write_text(s,encoding='utf-8')

if __name__=='__main__':main()
