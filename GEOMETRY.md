# Mesh geometry and manufacturing analysis

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
