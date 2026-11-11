import concurrent.futures
import ctypes as C
import math
from pathlib import Path
import struct
import tempfile
import unittest
from mesh_testbed import Mesh, MeshError

V=[(0,0,0),(1,0,0),(0,1,0),(0,0,1)]
F=[(0,2,1),(0,1,3),(0,3,2),(1,2,3)]

class MeshTests(unittest.TestCase):
    def tetra(self):
        m=Mesh.from_arrays(V,F);self.addCleanup(m.close);return m

    def test_analytic_tetrahedron(self):
        m=self.tetra()
        self.assertEqual(m.counts,(4,4))
        self.assertAlmostEqual(m.area(),(3+math.sqrt(3))/2)
        self.assertAlmostEqual(m.volume(signed=True),1/6)
        self.assertEqual(m.metrics()["bounds"],((0,0,0),(1,1,1)))

    def test_reverse_halfedges(self):
        m=self.tetra(); r=m.halfedges();v,f=m.get_mesh()
        for h,j in enumerate(r):
            self.assertGreaterEqual(j,0);self.assertEqual(r[j],h)
            self.assertEqual(f[h],f[3*(j//3)+(j%3+1)%3])

    def test_transform(self):
        m=self.tetra();a=m.area()
        m.scale(2).rotate("z",math.pi/2).translate(1e6,-3,7)
        self.assertAlmostEqual(m.area(),a*4)
        self.assertAlmostEqual(m.volume(),8/6)

    def test_reflection(self):
        m=self.tetra();m.scale(-1,1,1)
        self.assertAlmostEqual(m.volume(signed=True),-1/6)
        self.assertAlmostEqual(m.volume(),1/6)

    def test_open_mesh(self):
        with Mesh.from_arrays(V,F[:1]) as m:
            self.assertEqual(m.metrics()["boundary_halfedges"],3)
            with self.assertRaises(MeshError):m.volume()

    def test_inconsistent_orientation(self):
        with Mesh.from_arrays(V,[F[0][::-1]]+F[1:]) as m:
            self.assertGreater(m.metrics()["invalid_halfedges"],0)
            with self.assertRaises(MeshError):m.volume()

    def test_nonmanifold_and_degenerate(self):
        with Mesh.from_arrays(V,F+[F[0]]) as m:
            self.assertGreater(m.metrics()["invalid_halfedges"],0)
        with Mesh.from_arrays(V,[(0,0,1)]) as m:
            self.assertEqual(m.metrics()["degenerate_faces"],1)
            with self.assertRaises(MeshError):m.volume()

    def test_invalid_arrays(self):
        for vertices,faces in [([],F),(V,[(0,1,100)]),(V,[(0,1,-1)]),(V,[(0.,1,2)]),(V,[(0,1)])]:
            with self.assertRaises((ValueError,TypeError)):Mesh.from_arrays(vertices,faces)
        with self.assertRaises(MeshError):Mesh.from_arrays([(math.nan,0,0)]+V[1:],F)

    def test_failed_transform_is_atomic(self):
        m=self.tetra();before=list(m.get_mesh()[0])
        with self.assertRaises(MeshError):m.scale(math.inf)
        self.assertEqual(list(m.get_mesh()[0]),before)
        with self.assertRaises(MeshError):m.transform([[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,1,1]])

    def test_lifetime(self):
        m=self.tetra();v,f=m.get_mesh();m.close();m.close()
        self.assertEqual(len(v),12)
        with self.assertRaises(MeshError):m.area()
        with self.assertRaises(MeshError):m.get_mesh()

    def test_unicode_binary_roundtrip(self):
        m=self.tetra()
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"测试 mesh.stl";m.save(path)
            # Binary STL header may start with 'solid'.
            data=bytearray(path.read_bytes());data[:5]=b"solid";path.write_bytes(data)
            with Mesh(path) as other:
                self.assertEqual(other.counts,(4,4));self.assertAlmostEqual(other.volume(),m.volume())

    def test_ascii_stl(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"a.stl"
            p.write_text("solid test\nfacet normal 0 0 1\nouter loop\nvertex 0 0 0\nvertex 1 0 0\nvertex 0 1 0\nendloop\nendfacet\nendsolid test\n")
            with Mesh(p) as m:self.assertAlmostEqual(m.area(),0.5)

    def test_corrupt_stl(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"a.stl"
            for data in (b"",b"hello",b"solid bad\n",b"X"*80+struct.pack("<I",0xffffffff), b"X"*84):
                p.write_bytes(data)
                with self.assertRaises(MeshError):Mesh(p)

    def test_c_buffer_checks(self):
        m=self.tetra()
        self.assertEqual(m._lib.mc_copy_reverse(m._handle,(C.c_int64*1)(),1),-1)
        self.assertEqual(m._lib.mc_metrics(None,(C.c_double*8)(),8,(C.c_size_t*3)(),3),-1)

    def test_concurrent_independent_instances(self):
        def run(i):
            with Mesh.from_arrays(V,F) as m:return m.scale(i).volume()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            for i,value in enumerate(pool.map(run,range(1,21)),1):self.assertAlmostEqual(value,i**3/6)

    def test_supplied_models(self):
        models=Path(__file__).resolve().parents[2]/"MeshTestbed_C++"/"STLs"
        if not models.exists():models=Path(__file__).resolve().parent/"fixtures"/"stl"
        if not models.exists():self.skipTest("Original teaching data not included in this package")
        for p in models.glob("*.stl"):
            with self.subTest(model=p.name),Mesh(p) as m:
                self.assertGreater(m.counts[1],0);self.assertGreater(m.area(),0)
                with tempfile.TemporaryDirectory() as d:
                    out=Path(d)/"roundtrip.stl";m.save(out)
                    with Mesh(out) as other:
                        self.assertEqual(m.counts,other.counts)
                        self.assertAlmostEqual(m.area(),other.area())

if __name__=="__main__":unittest.main()
