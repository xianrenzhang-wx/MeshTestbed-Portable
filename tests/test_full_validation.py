"""Additional independent regressions from the full functional audit."""
import ctypes as C
import concurrent.futures
import math
from pathlib import Path
import random
import struct
import tempfile
import unittest
from mesh_testbed import Mesh, MeshError
from test_geometry import BOX_V, BOX_F, box_arrays

class FullValidation(unittest.TestCase):
    def box(self):
        m=Mesh.from_arrays(BOX_V,BOX_F);self.addCleanup(m.close);return m

    def test_section_far_from_plane_origin(self):
        m=self.box().translate(1e9,1e9,0)
        s=m.section((0,0,.5))
        self.assertAlmostEqual(s.area,1,places=10)
        self.assertAlmostEqual(s.perimeter,4,places=10)

    def test_save_failure_preserves_existing_file(self):
        m=self.box().scale(1e40)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'keep.stl';path.write_bytes(b'original file')
            with self.assertRaises((OverflowError,ValueError,MeshError)):m.save(path)
            self.assertEqual(path.read_bytes(),b'original file')

    def test_save_failure_does_not_leave_new_file(self):
        m=self.box().scale(1e40)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'new.stl'
            with self.assertRaises((OverflowError,ValueError,MeshError)):m.save(path)
            self.assertFalse(path.exists())

    def test_each_rotation_axis(self):
        expected={'x':(1,-3,2),'y':(3,2,-1),'z':(-2,1,3)}
        for axis in 'xyz':
            with Mesh.from_arrays([(1,2,3),(2,2,3),(1,3,3)],[(0,1,2)]) as m:
                m.rotate(axis,math.pi/2);v,_=m.get_mesh()
                for got,want in zip(v[:3],expected[axis]):self.assertAlmostEqual(got,want)

    def test_general_affine_shear_volume(self):
        m=self.box();m.transform(((1,.3,.2,5),(0,1,.4,6),(0,0,1,7),(0,0,0,1)))
        self.assertAlmostEqual(m.volume(),1)
        self.assertAlmostEqual(m.mass_properties()['volume'],1)

    def test_copy_is_independent(self):
        m=self.box();v,f=m.get_mesh();v[0]=100;f[0]=7
        self.assertAlmostEqual(m.volume(),1)
        self.assertEqual(m.get_mesh()[0][0],0)

    def test_random_rotated_nearest_points(self):
        angle=.731;c=math.cos(angle);s=math.sin(angle);rng=random.Random(555)
        m=self.box().rotate('z',angle).translate(7,-3,2)
        local=[tuple(rng.uniform(-1,2) for _ in range(3)) for _ in range(200)]
        world=[(c*x-s*y+7,s*x+c*y-3,z+2) for x,y,z in local]
        distances=m.nearest_points(world)['distances']
        for p,d in zip(local,distances):
            delta=[max(0,-x,x-1) for x in p]
            expected=math.hypot(*delta) if any(delta) else min(*p,*(1-x for x in p))
            self.assertAlmostEqual(d,expected,places=12)

    def test_signed_distance_and_mass_scaling(self):
        for scale in (1e-6,1e6):
            with Mesh.from_arrays(*box_arrays(scale)) as m:
                q=m.nearest_points([(scale/2,)*3],signed=True,tolerance=scale*1e-10)
                self.assertAlmostEqual(q['distances'][0]/scale,-.5)
                self.assertAlmostEqual(m.mass_properties()['volume']/scale**3,1)

    def test_native_output_guards(self):
        m=self.box();lib=m._lib;h=m._handle
        p=(C.c_double*3)(0,0,0);d=(C.c_double*16)();i=(C.c_int64*2)();s=(C.c_size_t*3)();state=C.c_int()
        calls=[lambda:lib.mc_counts(h,None,s),
               lambda:lib.mc_copy_mesh(h,d,1,i,1),
               lambda:lib.mc_metrics(h,d,7,s,3),
               lambda:lib.mc_mass_properties(h,1,d,13),
               lambda:lib.mc_nearest(h,p,1,0,1e-9,d,3,i,2),
               lambda:lib.mc_classify(h,p,1,1e-9,None,1),
               lambda:lib.mc_distance(h,h,d,i,1),
               lambda:lib.mc_collision(h,h,1,1e-9,C.byref(state),i,1),
               lambda:lib.mc_section(h,p,p,1e-9,None)]
        for call in calls:
            self.assertEqual(call(),-1);self.assertTrue(lib.mc_last_error())
        section=C.c_void_p();normal=(C.c_double*3)(0,0,1)
        self.assertEqual(lib.mc_section(h,p,normal,1e-9,C.byref(section)),0)
        try:self.assertEqual(lib.mc_section_copy(section,d,1),-1)
        finally:lib.mc_section_destroy(section)

    def test_native_creation_failure_clears_handle(self):
        m=self.box();handle=C.c_void_p(123)
        self.assertEqual(m._lib.mc_from_stl(None,0,C.byref(handle)),-1)
        self.assertIsNone(handle.value)

    def test_binary_nan_and_truncation(self):
        m=self.box()
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'model.stl';m.save(path);data=path.read_bytes()
            bad=bytearray(data);bad[96:100]=struct.pack('<f',math.nan)
            for content in (bytes(bad),data[:-1],data[:100]):
                path.write_bytes(content)
                with self.assertRaises(MeshError):Mesh(path)

    def test_ascii_scientific_and_whitespace(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.stl';p.write_text('  solid x\nfacet normal 0 0 1\nouter loop\nvertex 0 0 0\nvertex 1e0 0 0\nvertex 0 1.0e+0 0\nendloop\nendfacet\nendsolid x\n')
            with Mesh(p) as m:self.assertAlmostEqual(m.area(),.5)

    def test_invalid_transform_and_axis(self):
        m=self.box()
        for matrix in ([],[[1,2,3]],[[1,0,0,0]]*3):
            with self.assertRaises(ValueError):m.transform(matrix)
        with self.assertRaises(ValueError):m.rotate('q',0)
        with self.assertRaises(ValueError):list(m.slices([0],axis='q'))
        with self.assertRaises(ValueError):list(m.slices([math.nan]))

    def test_closed_pair_and_save_access(self):
        a=self.box();b=self.box();b.close()
        with self.assertRaises(MeshError):a.distance_to(b)
        with self.assertRaises(MeshError):a.collision(b)
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(MeshError):b.save(Path(d)/'a.stl')

    def test_parallel_same_mesh_reads(self):
        m=self.box()
        def run(_):return m.mass_properties()['volume'],m.section((0,0,.5)).area,m.nearest_points([(2,0,0)])['distances'][0]
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            for volume,area,distance in pool.map(run,range(40)):
                self.assertAlmostEqual(volume,1);self.assertEqual(area,1);self.assertEqual(distance,1)

    def test_repeat_resource_lifecycle(self):
        for _ in range(1000):
            with Mesh.from_arrays(BOX_V,BOX_F) as m:
                self.assertEqual(m.section((0,0,.5)).area,1)
                self.assertAlmostEqual(m.nearest_points([(2,.5,.5)])['distances'][0],1)

if __name__=='__main__':unittest.main()
