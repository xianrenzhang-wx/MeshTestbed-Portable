import ctypes as C
import math
import random
import unittest
from mesh_testbed import Mesh, MeshError, _load
from mesh_testbed.analysis import tetrahedron, _function, DP, IP, SZ
from mesh_testbed.bezier import curve, surface

V = [(0,0,0),(1,0,0),(0,1,0),(0,0,1)]
F = [(0,2,1),(0,1,3),(0,3,2),(1,2,3)]

class AnalysisTests(unittest.TestCase):
    def test_version(self):
        f = _load().mc_version; f.restype = C.c_char_p
        self.assertEqual(f(), b'2.1.0')

    def test_tetra_states_and_weights(self):
        r = tetrahedron([(0.2,0.2,0.2), (0,0,0), (.5,.5,0), (1,1,1)], V)
        self.assertEqual(r['states'], [-1,0,0,1])
        for a,b in zip(r['weights'][0], [.4,.2,.2,.2]):self.assertAlmostEqual(a,b)

    def test_random_affine_reconstruction(self):
        rng = random.Random(20261111)
        # A sheared tetrahedron with reversed orientation and translated coordinates.
        v = [(12,-4,9),(12,0,9),(15,-3,9),(13,-2,14)]
        weights = []
        for _ in range(300):
            w = [rng.uniform(.1,1) for _ in range(4)];weights.append([x/sum(w) for x in w])
        points = [tuple(sum(w[i]*v[i][k] for i in range(4)) for k in range(3)) for w in weights]
        result = tetrahedron(points,v)
        self.assertEqual(result['states'], [-1]*300)
        for actual,expected in zip(result['weights'],weights):
            for a,b in zip(actual,expected):self.assertAlmostEqual(a,b,places=12)

    def test_scale_and_translation(self):
        for scale,shift in [(1e-9,0),(1e9,0),(1,1e9)]:
            v = [tuple(scale*x+shift for x in row) for row in V]
            p = [[shift+.25*scale]*3]
            self.assertEqual(tetrahedron(p,v)['states'],[-1])

    def test_tetra_degenerate(self):
        for v in [[(0,0,0)]*4,[(0,0,0),(1,0,0),(0,1,0),(1,1,0)]]:
            r=tetrahedron([(0,0,0),(10,10,10)],v)
            self.assertEqual(r,{'states':[2,2],'weights':[None,None]})

    def test_tolerances(self):
        self.assertEqual(tetrahedron([(-1e-10,.2,.2)],V)['states'],[0])
        self.assertEqual(tetrahedron([(-1e-10,.2,.2)],V,tolerance=0)['states'],[1])
        thin=[(0,0,0),(1,0,0),(0,1,0),(0,0,1e-14)]
        self.assertEqual(tetrahedron([(0,0,0)],thin)['states'],[2])

    def test_invalid_and_empty(self):
        self.assertEqual(tetrahedron([],V),{'states':[],'weights':[]})
        for p,v in [([(math.nan,0,0)],V),([(0,0)],V),([(0,0,0)],V[:3])]:
            with self.assertRaises(ValueError):tetrahedron(p,v)
        for eps in [-1,math.nan,math.inf]:
            with self.assertRaises(MeshError):tetrahedron([(0,0,0)],V,tolerance=eps)

    def test_single_triangle_properties(self):
        with Mesh.from_arrays([(0,0,0),(2,0,0),(0,3,0)],[(0,1,2)]) as m:
            r=m.local_properties()
            self.assertEqual(r['face_areas'],[3])
            self.assertEqual(r['face_normals'],[(0,0,1)])
            self.assertEqual(r['face_centroids'],[(2/3,1,0)])
            self.assertEqual(r['vertex_barycentric_areas'],[1]*3)
            self.assertEqual(r['vertex_centroidal_tile_areas'],[.25]*3)
            self.assertEqual(m.unique_edges()['indices'],[(0,1),(0,2),(1,2)])
            self.assertEqual(m.unique_edges()['midpoints'],[(1,0,0),(0,1.5,0),(1,1.5,0)])

    def test_partition_and_transform(self):
        with Mesh.from_arrays(V,F) as m:
            for _ in range(2):
                r=m.local_properties();area=m.area()
                self.assertAlmostEqual(sum(r['face_areas']),area)
                self.assertAlmostEqual(sum(r['vertex_barycentric_areas']),area)
                self.assertAlmostEqual(sum(r['vertex_centroidal_tile_areas']),area/4)
                self.assertEqual(len(m.unique_edges()['indices']),6)
                m.scale(2).translate(5,7,9)

    def test_degenerate_normals_and_isolated_vertex(self):
        with Mesh.from_arrays([(0,0,0),(1,0,0),(2,0,0),(9,9,9)],[(0,1,2)]) as m:
            r=m.local_properties()
            self.assertEqual(r['face_normals'],[(0,0,0)])
            self.assertEqual(r['vertex_barycentric_areas'],[0]*4)

    def test_closed_and_owned_results(self):
        m=Mesh.from_arrays(V,F);r=m.local_properties();edges=m.unique_edges();m.close()
        self.assertEqual(len(edges['indices']),6);self.assertEqual(len(r['face_areas']),4)
        for fn in [m.local_properties,m.unique_edges]:
            with self.assertRaises(MeshError):fn()

    def test_native_buffers(self):
        lib,f=_function('mc_tetra_classify',[DP,DP,SZ,C.c_double,C.c_double,C.POINTER(C.c_int),SZ,DP,SZ])
        v=(C.c_double*12)(*(x for row in V for x in row));p=(C.c_double*3)(.2,.2,.2)
        s=(C.c_int*1)();w=(C.c_double*4)()
        self.assertEqual(f(v,p,1,1e-9,1e-12,s,0,w,4),-1)
        self.assertEqual(f(None,p,1,1e-9,1e-12,s,1,w,4),-1)
        with Mesh.from_arrays(V,F) as m:
            lib,f=_function('mc_local_properties',[C.c_void_p,DP,SZ,DP,SZ])
            self.assertEqual(f(m._handle,w,4,w,4),-1)
            lib,f=_function('mc_unique_edges',[C.c_void_p,IP,SZ,DP,SZ,C.POINTER(SZ)])
            n=SZ();pair=(C.c_int64*2)()
            self.assertEqual(f(m._handle,pair,2,w,4,C.byref(n)),-1)
            self.assertEqual(n.value,6)

    def test_bezier_curve_analytic(self):
        points=curve([(0,0,0),(1,0,0),(2,0,0),(3,0,0)],10)
        for i,p in enumerate(points):self.assertAlmostEqual(p[0],3*i/10)
        self.assertEqual(curve([(1,2,3)]*4,1),[(1,2,3)]*2)

    def test_bezier_surface_analytic(self):
        v,f=surface([[(i,j,2*i+3*j) for j in range(4)] for i in range(4)],3,4)
        self.assertEqual((len(v),len(f)),(20,24))
        for p in v:self.assertAlmostEqual(p[2],2*p[0]+3*p[1])
        with Mesh.from_arrays(v,f) as m:self.assertAlmostEqual(m.area(),9*math.sqrt(14))

    def test_bezier_invalid(self):
        for n in [0,1001,True]:
            with self.assertRaises(ValueError):curve(V,n)
        with self.assertRaises(ValueError):surface([[V[0]]])

if __name__=='__main__':unittest.main()
