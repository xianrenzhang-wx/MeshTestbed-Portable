"""C++ Bernstein sampling. No third-party packages required for computation.

Import explicitly: from mesh_testbed.bezier import curve, surface.
Older ABI 2 libraries retain their existing mesh APIs; these functions require
the additional mc_bezier_* exports built from src/mesh_bezier.cpp.
"""
import ctypes as C
import math
import operator
from . import _load, MeshError


def _subdivisions(value):
    if isinstance(value, bool):
        raise ValueError('Subdivision count must be an integer in [1,1000]')
    n = operator.index(value)
    if not 1 <= n <= 1000:
        raise ValueError('Subdivision count must be in [1,1000]')
    return n


def _controls(rows, count):
    rows = [tuple(float(v) for v in row) for row in rows]
    if len(rows) != count or any(len(row) != 3 for row in rows):
        raise ValueError(f'Expected {count} control points with three coordinates each')
    flat = [x for row in rows for x in row]
    if not all(math.isfinite(x) for x in flat):
        raise ValueError('Control coordinates must be finite')
    return (C.c_double * len(flat))(*flat)


def _native():
    lib = _load()
    try:
        cf, sf = lib.mc_bezier_curve, lib.mc_bezier_surface
    except AttributeError as exc:
        raise MeshError('This DLL lacks the Bezier extension; rebuild mesh_core or use the HW6 package') from exc
    dp, ip, sz = C.POINTER(C.c_double), C.POINTER(C.c_int64), C.c_size_t
    cf.argtypes = [dp, sz, dp, sz]; cf.restype = C.c_int
    sf.argtypes = [dp, sz, sz, dp, sz, ip, sz]; sf.restype = C.c_int
    return lib


def _check(lib, status):
    if status:
        raise MeshError(lib.mc_last_error().decode('utf-8', errors='replace'))


def curve(controls, segments=100):
    """Return segments+1 (x,y,z) tuples, including t=0 and t=1."""
    cp, n = _controls(controls, 4), _subdivisions(segments)
    out = (C.c_double * (3*(n+1)))()
    lib = _native(); _check(lib, lib.mc_bezier_curve(cp, n, out, len(out)))
    return [tuple(out[3*i:3*i+3]) for i in range(n+1)]


def surface(controls, u_segments=20, v_segments=20):
    """Return (vertices, triangles) as lists, controls indexed [u row][v column]."""
    grid = [list(row) for row in controls]
    if len(grid) != 4 or any(len(row) != 4 for row in grid):
        raise ValueError('Expected a 4 by 4 control net')
    cp = _controls([p for row in grid for p in row], 16)
    nu, nv = _subdivisions(u_segments), _subdivisions(v_segments)
    out = (C.c_double * (3*(nu+1)*(nv+1)))()
    faces = (C.c_int64 * (6*nu*nv))()
    lib = _native()
    _check(lib, lib.mc_bezier_surface(cp, nu, nv, out, len(out), faces, len(faces)))
    return ([tuple(out[i:i+3]) for i in range(0, len(out), 3)],
            [tuple(faces[i:i+3]) for i in range(0, len(faces), 3)])
