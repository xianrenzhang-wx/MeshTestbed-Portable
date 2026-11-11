"""Geometry and manufacturing analysis; no mandatory third-party Python modules."""
import ctypes as C
from dataclasses import dataclass
import itertools
import math
from . import MeshError, _rows


def _point(value):
    p=tuple(float(x) for x in value)
    if len(p)!=3 or not all(math.isfinite(x) for x in p):
        raise ValueError("Expected three finite coordinates")
    return p


def _tolerance(value):
    value=float(value)
    if not math.isfinite(value) or value<0:
        raise ValueError("Tolerance must be finite and nonnegative")
    return value


def _batch(points):
    # NumPy arrays also work; inputs are copied once into a contiguous native buffer.
    rows=[_point(p) for p in points]
    return (C.c_double*(len(rows)*3))(*(x for p in rows for x in p)),len(rows)


def _stitch(segments,origin,tolerance):
    """Weld endpoints locally, deduplicate edges, preserve branch diagnostics."""
    points=[]; buckets={}; exact={}; edges=set(); collapsed=0
    def index(p):
        if tolerance==0:
            if p not in exact:exact[p]=len(points);points.append(p)
            return exact[p]
        cell=tuple(math.floor((p[k]-origin[k])/tolerance) for k in range(3))
        candidates=[]
        for delta in itertools.product((-1,0,1),repeat=3):
            for i in buckets.get(tuple(cell[k]+delta[k] for k in range(3)),()):
                if math.dist(p,points[i])<=tolerance:candidates.append(i)
        if candidates:return min(candidates)
        i=len(points);points.append(p);buckets.setdefault(cell,[]).append(i);return i
    for a,b in segments:
        i,j=index(a),index(b)
        if i==j:collapsed+=1
        else:edges.add((min(i,j),max(i,j)))
    edges=sorted(edges);adj=[[] for _ in points]
    for e,(i,j) in enumerate(edges):adj[i].append(e);adj[j].append(e)
    used=set();paths=[]
    def walk(start,e):
        path=[start];current=start
        while e not in used:
            used.add(e);a,b=edges[e];current=b if a==current else a;path.append(current)
            if current==start or len(adj[current])!=2:break
            options=[x for x in adj[current] if x not in used]
            if not options:break
            e=options[0]
        paths.append(tuple(points[i] for i in path))
    for i,es in enumerate(adj):
        if len(es)!=2:
            for e in es:
                if e not in used:walk(i,e)
    for e,(i,_) in enumerate(edges):
        if e not in used:walk(i,e)
    return tuple(paths),sum(len(es)>2 for es in adj),collapsed


@dataclass(frozen=True)
class Section:
    """Plane-intersection segments and stitched 3D polylines.

    Closed polylines repeat their first point at the end. Isolated tangent
    points are omitted. Coplanar patches contribute their boundary only.
    """
    origin: tuple
    normal: tuple
    segments: tuple
    polylines: tuple
    branch_vertices: int
    collapsed_segments: int
    tolerance: float

    @property
    def closed(self):
        return tuple(len(p)>2 and p[0]==p[-1] for p in self.polylines)

    @property
    def perimeter(self):
        return math.fsum(math.dist(a,b) for line in self.polylines for a,b in zip(line,line[1:]))

    def _plane_loops(self):
        # Choose the coordinate axis least aligned with the normal.
        n=self.normal;k=min(range(3),key=lambda i:abs(n[i]));axis=[0.,0.,0.];axis[k]=1.
        u=(n[1]*axis[2]-n[2]*axis[1],n[2]*axis[0]-n[0]*axis[2],n[0]*axis[1]-n[1]*axis[0])
        length=math.hypot(*u);u=tuple(x/length for x in u)
        v=(n[1]*u[2]-n[2]*u[1],n[2]*u[0]-n[0]*u[2],n[0]*u[1]-n[1]*u[0])
        return [tuple((sum((p[k]-self.origin[k])*u[k] for k in range(3)),
                       sum((p[k]-self.origin[k])*v[k] for k in range(3))) for p in line) for line in self.polylines]

    @property
    def area(self):
        """Even-odd area for simple, disjoint/nested closed contours.

        Raises for open, branched, collapsed, crossing or touching contours.
        Does not infer physical shell orientation from an STL surface.
        """
        if self.branch_vertices or self.collapsed_segments or not all(self.closed):
            raise MeshError("Section area requires closed, unbranched, uncollapsed contours")
        loops=self._plane_loops()
        # Reject self-crossing/touching contours rather than report plausible area.
        def orient(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
        def near_segment(p,a,b):
            dx,dy=b[0]-a[0],b[1]-a[1];den=dx*dx+dy*dy
            t=max(0.,min(1.,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/den)) if den else 0
            return math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)<=self.tolerance
        segments=[(li,k,a,b) for li,line in enumerate(loops) for k,(a,b) in enumerate(zip(line,line[1:]))]
        for i,(li,k,a,b) in enumerate(segments):
            for lj,j,c,d in segments[i+1:]:
                if li==lj and (abs(k-j)==1 or {k,j}=={0,len(loops[li])-2}):continue
                crossing=orient(a,b,c)*orient(a,b,d)<0 and orient(c,d,a)*orient(c,d,b)<0
                if crossing or any((near_segment(a,c,d),near_segment(b,c,d),near_segment(c,a,b),near_segment(d,a,b))):
                    raise MeshError("Section contours cross or touch; area is ambiguous")
        def contains(line,p):
            result=False
            for a,b in zip(line,line[1:]):
                if (a[1]>p[1])!=(b[1]>p[1]):
                    x=a[0]+(p[1]-a[1])*(b[0]-a[0])/(b[1]-a[1])
                    if p[0]<x:result=not result
            return result
        total=[]
        for i,line in enumerate(loops):
            # Translate each contour locally before the shoelace sum. Large
            # world coordinates otherwise cancel small cross-section areas.
            x0,y0=line[0]
            area=abs(math.fsum((a[0]-x0)*(b[1]-y0)-(b[0]-x0)*(a[1]-y0)
                               for a,b in zip(line,line[1:])))/2
            depth=sum(contains(other,line[0]) for j,other in enumerate(loops) if j!=i)
            total.append(area if depth%2==0 else -area)
        return math.fsum(total)


class GeometryMixin:
    def mass_properties(self,density=1.0):
        """Uniform solid volume, mass, center of mass, 3x3 centroidal inertia.

        Use consistent length/mass units. Requires valid closed oriented input;
        self-intersections and shell orientation are the caller's responsibility.
        """
        with self._lock:
            self._alive();out=(C.c_double*14)()
            self._check(self._lib.mc_mass_properties(self._handle,float(density),out,14))
            return dict(volume=out[0],mass=out[1],centroid=tuple(out[2:5]),
                        inertia=tuple(tuple(out[5+3*i:8+3*i]) for i in range(3)))

    def nearest_points(self,points,signed=False,tolerance=1e-9,numpy=False):
        """Batch point-to-surface distance, closest coordinates and face IDs.

        Negative signed distance means inside; within tolerance is zero.
        Unsigned queries work with open and degenerate meshes. Signed queries
        use solid angles and require a closed oriented mesh.
        """
        p,n=_batch(points);eps=_tolerance(tolerance)
        out=(C.c_double*(4*n))();faces=(C.c_int64*n)()
        with self._lock:
            self._alive()
            self._check(self._lib.mc_nearest(self._handle,p,n,bool(signed),eps,out,len(out),faces,n))
        if numpy:
            import numpy as np
            a=np.ctypeslib.as_array(out).reshape(-1,4)
            return dict(distances=a[:,0],points=a[:,1:],face_ids=np.ctypeslib.as_array(faces))
        return dict(distances=list(out[::4]),points=[tuple(out[4*i+1:4*i+4]) for i in range(n)],face_ids=list(faces))

    def classify_points(self,points,tolerance=1e-9):
        """Return -1 inside, 0 on/near boundary, +1 outside for each point."""
        p,n=_batch(points);eps=_tolerance(tolerance);states=(C.c_int*n)()
        with self._lock:
            self._alive();self._check(self._lib.mc_classify(self._handle,p,n,eps,states,n))
        return list(states)

    def contains(self,points,include_boundary=True,tolerance=1e-9):
        return [s<0 or (s==0 and include_boundary) for s in self.classify_points(points,tolerance)]

    def distance_to(self,other):
        """Minimum surface separation. Nested solids may have positive distance."""
        if type(other) is not type(self):raise TypeError("other must be a Mesh")
        first,second=sorted((self,other),key=id)
        with first._lock,second._lock:
            self._alive();other._alive();value=C.c_double();faces=(C.c_int64*2)()
            self._check(self._lib.mc_distance(self._handle,other._handle,C.byref(value),faces,2))
            return dict(distance=value.value,face_ids=tuple(faces))

    def collision(self,other,solid=True,tolerance=1e-9):
        """Report separated, surface_contact or containment; touching counts.

        solid=False checks surfaces only and permits open triangle meshes.
        Tolerance expands SAT projection intervals; it is not a clearance radius.
        """
        if type(other) is not type(self):raise TypeError("other must be a Mesh")
        eps=_tolerance(tolerance);first,second=sorted((self,other),key=id)
        with first._lock,second._lock:
            self._alive();other._alive();value=C.c_int();faces=(C.c_int64*2)()
            self._check(self._lib.mc_collision(self._handle,other._handle,bool(solid),eps,C.byref(value),faces,2))
            kind=("separated","surface_contact","containment")[value.value]
            return dict(collides=value.value!=0,kind=kind,face_ids=tuple(faces) if value.value==1 else None)

    def section(self,origin=(0,0,0),normal=(0,0,1),tolerance=1e-9):
        """Intersect a plane, return segments, polylines, perimeter and area."""
        origin=_point(origin);normal=_point(normal);eps=_tolerance(tolerance)
        length=math.hypot(*normal)
        if not math.isfinite(length) or length==0:raise ValueError("Plane normal must be nonzero")
        normal=tuple(x/length for x in normal);o=(C.c_double*3)(*origin);n=(C.c_double*3)(*normal)
        handle=C.c_void_p()
        with self._lock:
            self._alive()
            self._check(self._lib.mc_section(self._handle,o,n,eps,C.byref(handle)))
            try:
                count=C.c_size_t();self._check(self._lib.mc_section_size(handle,C.byref(count)))
                data=(C.c_double*(6*count.value))()
                self._check(self._lib.mc_section_copy(handle,data,len(data)))
            finally:self._lib.mc_section_destroy(handle)
        segments=tuple((tuple(data[i:i+3]),tuple(data[i+3:i+6])) for i in range(0,len(data),6))
        lines,branches,collapsed=_stitch(segments,origin,eps)
        return Section(origin,normal,segments,lines,branches,collapsed,eps)

    def slices(self,heights,axis="z",tolerance=1e-9):
        """Yield a Section per absolute coordinate; results are not all retained.

        Reuses the mesh's BVH. Do not transform the mesh during iteration if
        slices must all represent one snapshot.
        """
        if axis not in ("x","y","z"):raise ValueError("axis must be x, y or z")
        k=("x","y","z").index(axis);normal=[0.,0.,0.];normal[k]=1.
        for height in heights:
            origin=[0.,0.,0.];origin[k]=float(height)
            yield self.section(origin,normal,tolerance)
