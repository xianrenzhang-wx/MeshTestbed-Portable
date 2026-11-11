# MeshTestbed Portable 2.1.0 API

## Contract

Python 3.9+, standard library for computation. Coordinates are finite xyz values;
indices start at zero. Length units are user-defined; density must use consistent
mass/length³ units. Angles are radians. Results own their data. Use `with Mesh(...)`
or `close()` to release native memory. Calls on one Mesh are serialized; independent
meshes may run concurrently. No GPU execution or automatic differentiation.

Python validation raises ValueError/TypeError; native validation raises MeshError.
File operations may raise OSError. After close, computation raises MeshError.
Replace the entire package when upgrading. ABI remains 2 (additive exports), but
new methods require native release 2.1.0. `__version__` is the Python release;
`mc_version()` reports the native release. Old ABI-2 libraries can run old APIs,
but new calls report a missing-extension error. Never infer features from ABI alone.

## Mesh creation and basic methods

```python
from mesh_testbed import Mesh, MeshError
```

| Interface | Input / return |
|---|---|
| `Mesh(filename)` | ASCII or binary STL; exact coordinate welding |
| `Mesh.from_arrays(vertices, faces)` | Nx3 coordinates, Mx3 integer indices; copies input, no welding |
| `counts` | Property `(vertex_count, face_count)` |
| `get_mesh(numpy=False)` | Two flat owning ctypes arrays; with NumPy, shaped Nx3/Mx3 arrays |
| `halfedges()` | Opposite halfedge indices; -1 boundary, -2 invalid pairing |
| `metrics()` | area, signed_volume, bounds, boundary_halfedges, invalid_halfedges, degenerate_faces |
| `area()` | Scalar surface area |
| `volume(signed=False)` | Solid volume; orientation sign optional |
| `translate(x,y,z)` | In-place; returns self |
| `rotate(axis,radians)` | Axis x/y/z; in-place; returns self |
| `scale(x,y=None,z=None)` | Uniform or per-axis scaling; returns self |
| `transform(matrix)` | Row-major 4x4 affine matrix; returns self |
| `save(filename)` | Atomic binary float32 STL export in Python |
| `show()` | Optional NumPy/Polyscope viewer |
| `close()` | Idempotent release |

## Geometry queries

| Interface | Result |
|---|---|
| `mass_properties(density=1.0)` | volume, mass, centroid, centroidal inertia tensor |
| `nearest_points(points,signed=False,tolerance=1e-9,numpy=False)` | distances, nearest points, face_ids; batch Nx3 input |
| `classify_points(points,tolerance=1e-9)` | List: -1 inside, 0 boundary, +1 outside |
| `contains(points,include_boundary=True,tolerance=1e-9)` | Boolean list |
| `distance_to(other)` | Minimum surface distance and face_ids |
| `collision(other,solid=True,tolerance=1e-9)` | collides, kind, face_ids; kind separated/surface_contact/containment |
| `section(origin=(0,0,0),normal=(0,0,1),tolerance=1e-9)` | Section with segments, polylines, closed flags, area/perimeter and graph diagnostics |
| `slices(heights,axis="z",tolerance=1e-9)` | Generator of Sections |

See [GEOMETRY.md](GEOMETRY.md) for detailed return fields and section diagnostics.
Solid operations require closed, consistently oriented, nondegenerate meshes.
Self-intersection and all vertex-manifold conditions are not fully certified.
Surface distance can be positive for nested solids. Collision tolerance is SAT
projection inflation, not an exact Euclidean clearance threshold. Section area
rejects invalid/open/branched/crossing contours. Spatial query tolerances have
coordinate length units; tetrahedron tolerances below do not.

## Batch tetrahedron classification — new

```python
from mesh_testbed.analysis import tetrahedron
result = tetrahedron(points, vertices, tolerance=1e-9,
                     degeneracy_tolerance=1e-12)
```

- `points`: Nx3 iterable; an empty batch is accepted.
- `vertices`: exactly four xyz vertices defining one tetrahedron.
- Return: `{"states": [...], "weights": [...]}`; each weight tuple has four
  barycentric coordinates corresponding to the input vertex order.
- States: **-1 inside, 0 boundary, +1 outside, 2 degenerate**. Degenerate weights
  are `None`. Finite exterior points still receive barycentric coordinates.
- Reconstruction: `point = sum(weights[i] * vertices[i])`; weights sum to one
  up to floating-point rounding. Negative weights indicate exterior locations.
- `tolerance` is dimensionless: any weight below `-tolerance` means outside;
  otherwise any absolute weight at most `tolerance` means boundary.
- Degeneracy: let L be the longest edge. L=0 or
  `abs(det((v1-v0)/L,(v2-v0)/L,(v3-v0)/L)) <= degeneracy_tolerance` means degenerate.
  Both tolerances must be finite and nonnegative. This is a floating-point
  predicate, not an exact arithmetic predicate; extremely thin elements may be
  deliberately classified as degenerate. Unrepresentable intermediate values
  raise an error. No tolerance value guarantees accuracy for all scales.

## Local mesh properties — new

`mesh.local_properties()` returns:

| Key | Shape | Meaning |
|---|---|---|
| face_centroids | Mx3 | Arithmetic mean of triangle vertices |
| face_normals | Mx3 | Unit normal from input winding; zero for zero-area triangles |
| face_areas | M | Triangle areas |
| vertex_barycentric_areas | N | Sum of incident triangle area / 3 |
| vertex_centroidal_tile_areas | N | HW4 construction: sum of incident triangle area / 12 |

The first vertex measure sums to total surface area. The HW4 measure sums to
one quarter of surface area: each tile joins two edge midpoints and the face
centroid, excluding the original vertex. It is not a full dual-cell area.
Isolated vertices receive zero. Open meshes are accepted. Results are recomputed
from current coordinates after transforms; no closed-solid assumption is needed.

`mesh.unique_edges()` returns `indices` (Ex2 integer tuples) and `midpoints` (Ex3).
Pairs are undirected, sorted internally and then lexicographically. Distinct
indices at identical coordinates remain distinct; no geometric welding occurs.
Repeated indices can produce self-edges on degenerate input; they are retained.

## Bézier — now included in every release target

```python
from mesh_testbed.bezier import curve, surface
points = curve(controls, segments=100)
vertices, triangles = surface(control_grid, u_segments=20, v_segments=20)
```

Curve controls: 4x3; cubic Bernstein basis, `segments+1` points including endpoints.
Surface controls: 4x4x3 in [u][v] order; tensor-product bicubic sampling.
Returns `(nu+1)*(nv+1)` vertices and `2*nu*nv` triangles. Index is `a*(nv+1)+b`;
normals follow increasing-u cross increasing-v. Subdivisions are integers 1–1000.
No NURBS, derivative API, adaptive tessellation, or exact surface intersection.

## C ABI and ownership

Authoritative declarations: [include/mesh_core.h](include/mesh_core.h).
All capacities count scalar elements, not bytes. Status-returning functions
return 0 on success and -1 on failure; `mc_last_error()` is thread-local UTF-8.
Do not use output buffers after failure: writes may have partially completed.
Caller must supply valid input arrays of the documented size and live handles.
Never destroy twice or mutate/destroy a handle concurrently with a query.

| New export | Buffers / contract |
|---|---|
| `mc_version()` | Borrowed static C string; do not free |
| `mc_tetra_classify` | Input 12 vertex doubles, 3N point doubles; N states and 4N weights. Degenerate native weights are NaN |
| `mc_local_properties` | 7M face doubles [centroid3,normal3,area]; 2N vertex doubles [barycentric_area,HW4_tile_area] |
| `mc_unique_edges` | Query E with both buffers null and capacities zero; then supply 2E int64 indices and 3E doubles. Lock across both calls |

Existing export groups: creation/destruction (`mc_from_stl`, `mc_from_arrays`,
`mc_destroy`), mesh access (`mc_counts`, `mc_copy_mesh`, `mc_copy_reverse`), metrics
and transforms (`mc_metrics`, `mc_transform`, `mc_mass_properties`), queries
(`mc_nearest`, `mc_classify`, `mc_distance`, `mc_collision`), section lifecycle
(`mc_section`, `mc_section_size`, `mc_section_copy`, `mc_section_destroy`), and
Bézier (`mc_bezier_curve`, `mc_bezier_surface`). Section handles must be released
with `mc_section_destroy`; mesh handles with `mc_destroy`.
