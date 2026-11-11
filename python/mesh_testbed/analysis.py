"""Batch tetrahedron predicates and local mesh properties (native 2.1+)."""
import ctypes as C
import math

def _function(name, args):
    from . import _load, MeshError
    lib = _load()
    try:
        f = getattr(lib, name)
    except AttributeError as exc:
        raise MeshError('Native extension missing; replace the entire package with 2.1.0+') from exc
    f.argtypes = args
    f.restype = C.c_int
    return lib, f

def _check(lib, result):
    from . import MeshError
    if result:
        raise MeshError(lib.mc_last_error().decode('utf-8', errors='replace'))

def _points(rows):
    rows = [tuple(float(x) for x in row) for row in rows]
    if any(len(row) != 3 or not all(math.isfinite(x) for x in row) for row in rows):
        raise ValueError('Expected finite xyz coordinates')
    return rows, (C.c_double * (3*len(rows)))(*(x for row in rows for x in row))

DP = C.POINTER(C.c_double)
IP = C.POINTER(C.c_int64)
SZ = C.c_size_t

def tetrahedron(points, vertices, tolerance=1e-9, degeneracy_tolerance=1e-12):
    """Classify a batch against one tetrahedron; return states and barycentric weights.

    State: -1 inside, 0 boundary, 1 outside, 2 degenerate. Degenerate weights
    are None. Both tolerances are dimensionless. Empty point batches are valid.
    """
    rows, p = _points(points)
    vrows, v = _points(vertices)
    if len(vrows) != 4:
        raise ValueError('Expected four tetrahedron vertices')
    n = len(rows)
    states, weights = (C.c_int*n)(), (C.c_double*(4*n))()
    lib, f = _function('mc_tetra_classify', [DP, DP, SZ, C.c_double, C.c_double, C.POINTER(C.c_int), SZ, DP, SZ])
    _check(lib, f(v, p, n, tolerance, degeneracy_tolerance, states, n, weights, 4*n))
    return {'states': list(states), 'weights': [None if states[i] == 2 else tuple(weights[4*i:4*i+4]) for i in range(n)]}

class AnalysisMixin:
    def local_properties(self):
        """Return face centroids/normals/areas and two distinct vertex area measures."""
        with self._lock:
            self._alive()
            nv, nf = self.counts
            faces, vertices = (C.c_double*(7*nf))(), (C.c_double*(2*nv))()
            lib, f = _function('mc_local_properties', [C.c_void_p, DP, SZ, DP, SZ])
            _check(lib, f(self._handle, faces, len(faces), vertices, len(vertices)))
        return {'face_centroids': [tuple(faces[7*i:7*i+3]) for i in range(nf)],
                'face_normals': [tuple(faces[7*i+3:7*i+6]) for i in range(nf)],
                'face_areas': [faces[7*i+6] for i in range(nf)],
                'vertex_barycentric_areas': list(vertices[::2]),
                'vertex_centroidal_tile_areas': list(vertices[1::2])}

    def unique_edges(self):
        """Return sorted undirected index pairs and their xyz midpoints."""
        with self._lock:
            self._alive()
            lib, f = _function('mc_unique_edges', [C.c_void_p, IP, SZ, DP, SZ, C.POINTER(SZ)])
            n = SZ()
            _check(lib, f(self._handle, None, 0, None, 0, C.byref(n)))
            pairs, mids = (C.c_int64*(2*n.value))(), (C.c_double*(3*n.value))()
            _check(lib, f(self._handle, pairs, len(pairs), mids, len(mids), C.byref(n)))
        return {'indices': [tuple(pairs[2*i:2*i+2]) for i in range(n.value)],
                'midpoints': [tuple(mids[3*i:3*i+3]) for i in range(n.value)]}
