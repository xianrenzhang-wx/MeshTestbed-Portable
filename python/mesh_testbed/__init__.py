"""Portable C++ mesh calculations. Python 3.9+, standard library only.

Different Mesh instances can run concurrently. Each instance serializes native
access; returned arrays own their memory and remain valid after close().
"""
import ctypes as C
import math
import operator
import os
from pathlib import Path
import struct
import sys
import threading

__all__ = ["Mesh", "MeshError", "Section"]
__version__ = "2.1.0"

class MeshError(RuntimeError):
    pass

_library = None
_load_lock = threading.Lock()

def _load():
    global _library
    with _load_lock:
        if _library is not None:
            return _library
        names = {"win32": "mesh_core.dll", "linux": "libmesh_core.so", "darwin": "libmesh_core.dylib"}
        name = names.get(sys.platform)
        if name is None:
            raise MeshError(f"Unsupported platform: {sys.platform}")
        path = Path(os.environ.get("MESH_CORE_LIBRARY", Path(__file__).parent / name)).resolve()
        if not path.is_file():
            raise MeshError(f"Native library missing: {path}. Use a package matching your OS and Python architecture, or build with CMake.")
        try:
            lib = C.CDLL(str(path))
        except OSError as e:
            raise MeshError(f"Cannot load {path}; check CPU architecture and runtime dependencies: {e}") from e
        try:
            lib.mc_abi_version.argtypes=[]
            lib.mc_abi_version.restype=C.c_int
            if lib.mc_abi_version()!=2:
                raise MeshError("Incompatible mesh_core ABI; replace the entire package with version 2")
        except AttributeError as e:
            raise MeshError("Not a mesh_core native library") from e
        ptr, sz = C.c_void_p, C.c_size_t
        dp, ip, sp = C.POINTER(C.c_double), C.POINTER(C.c_int64), C.POINTER(sz)
        signatures = {
            "mc_abi_version": ([], C.c_int),
            "mc_last_error": ([], C.c_char_p),
            "mc_from_stl": ([C.c_void_p, sz, C.POINTER(ptr)], C.c_int),
            "mc_from_arrays": ([dp, sz, ip, sz, C.POINTER(ptr)], C.c_int),
            "mc_destroy": ([ptr], None),
            "mc_counts": ([ptr, sp, sp], C.c_int),
            "mc_copy_mesh": ([ptr, dp, sz, ip, sz], C.c_int),
            "mc_copy_reverse": ([ptr, ip, sz], C.c_int),
            "mc_metrics": ([ptr, dp, sz, sp, sz], C.c_int),
            "mc_transform": ([ptr, dp], C.c_int),
            "mc_mass_properties": ([ptr,C.c_double,dp,sz],C.c_int),
            "mc_nearest": ([ptr,dp,sz,C.c_int,C.c_double,dp,sz,ip,sz],C.c_int),
            "mc_classify": ([ptr,dp,sz,C.c_double,C.POINTER(C.c_int),sz],C.c_int),
            "mc_distance": ([ptr,ptr,dp,ip,sz],C.c_int),
            "mc_collision": ([ptr,ptr,C.c_int,C.c_double,C.POINTER(C.c_int),ip,sz],C.c_int),
            "mc_section": ([ptr,dp,dp,C.c_double,C.POINTER(ptr)],C.c_int),
            "mc_section_size": ([ptr,sp],C.c_int),
            "mc_section_copy": ([ptr,dp,sz],C.c_int),
            "mc_section_destroy": ([ptr],None),
        }
        for name, (args, result) in signatures.items():
            f = getattr(lib, name); f.argtypes = args; f.restype = result
        if lib.mc_abi_version() != 2:
            raise MeshError("Incompatible mesh_core ABI; use matching Python wrapper and library")
        _library = lib
        return lib

def _rows(values, width, convert):
    rows = [tuple(convert(x) for x in row) for row in values]
    if not rows or any(len(row) != width for row in rows):
        raise ValueError(f"Expected a nonempty array with {width} columns")
    return rows

from .geometry import GeometryMixin, Section

from .analysis import AnalysisMixin

class Mesh(AnalysisMixin, GeometryMixin):
    def __init__(self, filename):
        self._init()
        data = Path(filename).read_bytes()  # Unicode paths on every platform
        self._check(self._lib.mc_from_stl(data, len(data), C.byref(self._handle)))

    def _init(self):
        self._handle = C.c_void_p()
        self._lock = threading.RLock()
        self._lib = _load()

    @classmethod
    def from_arrays(cls, vertices, faces):
        """Copy indexed triangles into C++. Face indices must be zero-based integers."""
        v = _rows(vertices, 3, float)
        f = _rows(faces, 3, operator.index)
        if any(i < 0 or i >= len(v) for row in f for i in row):
            raise ValueError("Face index out of range")
        va = (C.c_double * (len(v)*3))(*(x for row in v for x in row))
        fa = (C.c_int64 * (len(f)*3))(*(x for row in f for x in row))
        obj = cls.__new__(cls); obj._init()
        obj._check(obj._lib.mc_from_arrays(va,len(v),fa,len(f),C.byref(obj._handle)))
        return obj

    def _check(self, status):
        if status != 0:
            raise MeshError(self._lib.mc_last_error().decode("utf-8", errors="replace"))

    def _alive(self):
        if not self._handle.value:
            raise MeshError("Mesh is closed")

    def close(self):
        with self._lock:
            if self._handle.value:
                self._lib.mc_destroy(self._handle)
                self._handle = C.c_void_p()

    def __del__(self):
        if getattr(self, "_handle", None) and getattr(self, "_lib", None):
            self.close()

    def __enter__(self):
        self._alive(); return self

    def __exit__(self, *args):
        self.close()

    @property
    def counts(self):
        with self._lock:
            self._alive(); nv,nf=C.c_size_t(),C.c_size_t()
            self._check(self._lib.mc_counts(self._handle,C.byref(nv),C.byref(nf)))
            return nv.value,nf.value

    def metrics(self):
        """One native call for area, signed volume, bounds and edge diagnostics."""
        with self._lock:
            self._alive(); values=(C.c_double*8)(); topology=(C.c_size_t*3)()
            self._check(self._lib.mc_metrics(self._handle,values,8,topology,3))
            return dict(area=values[0],signed_volume=values[1],
                        bounds=(tuple(values[2:5]),tuple(values[5:8])),
                        boundary_halfedges=topology[0],invalid_halfedges=topology[1],
                        degenerate_faces=topology[2])

    def area(self):
        return self.metrics()["area"]

    def volume(self, signed=False):
        """Require closed, consistently oriented edges and nondegenerate faces.

        Self-intersections and nested-shell orientation are not checked.
        """
        m=self.metrics()
        if any(m[k] for k in ("boundary_halfedges","invalid_halfedges","degenerate_faces")):
            raise MeshError("Volume requires a closed, consistently oriented, nondegenerate mesh")
        return m["signed_volume"] if signed else abs(m["signed_volume"])

    def get_mesh(self, numpy=False):
        """Return owning flat ctypes buffers; optional NumPy arrays have shape (N,3).

        One bulk copy from C++. numpy=True creates views of those copied buffers.
        """
        with self._lock:
            nv,nf=self.counts
            v=(C.c_double*(nv*3))(); f=(C.c_int64*(nf*3))()
            self._check(self._lib.mc_copy_mesh(self._handle,v,len(v),f,len(f)))
        if numpy:
            import numpy as np
            return np.ctypeslib.as_array(v).reshape(-1,3),np.ctypeslib.as_array(f).reshape(-1,3)
        return v,f

    def halfedges(self):
        """Return reverse indices. h=3*face+corner; -1 boundary, -2 invalid edge."""
        with self._lock:
            _,nf=self.counts; r=(C.c_int64*(nf*3))()
            self._check(self._lib.mc_copy_reverse(self._handle,r,len(r)))
            return r

    def transform(self, matrix):
        rows=_rows(matrix,4,float)
        if len(rows)!=4:
            raise ValueError("Expected a 4x4 matrix")
        a=(C.c_double*16)(*(x for row in rows for x in row))
        with self._lock:
            self._alive(); self._check(self._lib.mc_transform(self._handle,a))
        return self

    def scale(self, x, y=None, z=None):
        y=x if y is None else y; z=x if z is None else z
        return self.transform(((x,0,0,0),(0,y,0,0),(0,0,z,0),(0,0,0,1)))

    def translate(self, x, y, z):
        return self.transform(((1,0,0,x),(0,1,0,y),(0,0,1,z),(0,0,0,1)))

    def rotate(self, axis, radians):
        if axis not in ("x","y","z"):
            raise ValueError("axis must be x, y or z")
        c,s=math.cos(radians),math.sin(radians)
        a=[[1.,0.,0.,0.],[0.,1.,0.,0.],[0.,0.,1.,0.],[0.,0.,0.,1.]]
        i,j={"x":(1,2),"y":(2,0),"z":(0,1)}[axis]
        a[i][i]=a[j][j]=c; a[i][j]=-s; a[j][i]=s
        return self.transform(a)

    def save(self, filename):
        """Atomically write binary STL; a failed export preserves the destination."""
        import tempfile
        v,f=self.get_mesh()
        if any(abs(x)>3.4028234663852886e38 for x in v):
            raise OverflowError("STL coordinates exceed the float32 range")
        if len(f)//3>0xffffffff:raise OverflowError("Too many triangles for binary STL")
        target=Path(filename).resolve();temporary=None
        try:
            with tempfile.NamedTemporaryFile(mode="wb",dir=target.parent,prefix=target.name+".",suffix=".tmp",delete=False) as out:
                temporary=Path(out.name)
                out.write(b"MeshTestbed Portable".ljust(80,b"\0")); out.write(struct.pack("<I",len(f)//3))
                for i in range(0,len(f),3):
                    p=[v[3*j:3*j+3] for j in f[i:i+3]]
                    a=[p[1][k]-p[0][k] for k in range(3)]; b=[p[2][k]-p[0][k] for k in range(3)]
                    n=[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
                    length=math.hypot(*n); n=[x/length for x in n] if length else [0.,0.,0.]
                    out.write(struct.pack("<12fH",*n,*(x for row in p for x in row),0))
            os.replace(temporary,target)
        finally:
            if temporary is not None:temporary.unlink(missing_ok=True)

    def show(self):
        """Optional viewer: python -m pip install numpy polyscope."""
        import polyscope as ps
        vertices,faces=self.get_mesh(numpy=True)
        if not ps.is_initialized():ps.init()
        ps.register_surface_mesh("Mesh",vertices,faces)
        ps.reset_camera_to_home_view()
        ps.show()
