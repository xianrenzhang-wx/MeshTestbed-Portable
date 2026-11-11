import concurrent.futures
import math
import random
import unittest
from mesh_testbed import Mesh, MeshError

BOX_V=[(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1)]
BOX_F=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),
       (1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]

def box_arrays(scale=1,offset=(0,0,0)):
    return [tuple(scale*p[k]+offset[k] for k in range(3)) for p in BOX_V],BOX_F

def join(*parts):
    vertices=[];faces=[]
    for v,f in parts:
        faces.extend(tuple(i+len(vertices) for i in t) for t in f);vertices.extend(v)
    return vertices,faces

class GeometryTests(unittest.TestCase):
    def box(self,scale=1,offset=(0,0,0)):
        m=Mesh.from_arrays(*box_arrays(scale,offset));self.addCleanup(m.close);return m

    def mesh(self,v,f):
        m=Mesh.from_arrays(v,f);self.addCleanup(m.close);return m

    def test_mass_cube(self):
        m=self.box();p=m.mass_properties(6)
        self.assertAlmostEqual(p["volume"],1);self.assertAlmostEqual(p["mass"],6)
        for x in p["centroid"]:self.assertAlmostEqual(x,.5)
        for i in range(3):
            for j in range(3):self.assertAlmostEqual(p["inertia"][i][j],1 if i==j else 0)

    def test_mass_tetrahedron(self):
        m=self.mesh([(0,0,0),(1,0,0),(0,1,0),(0,0,1)],[(0,2,1),(0,1,3),(0,3,2),(1,2,3)])
        p=m.mass_properties(6)
        self.assertAlmostEqual(p["mass"],1);self.assertEqual(p["centroid"],(.25,.25,.25))
        for i in range(3):
            for j in range(3):self.assertAlmostEqual(p["inertia"][i][j],.075 if i==j else .0125)

    def test_mass_translation_rotation(self):
        m=self.box();m.scale(2,3,4)
        p=m.mass_properties();self.assertEqual(p["mass"],24)
        self.assertAlmostEqual(p["inertia"][0][0],50)
        m.rotate("z",math.pi/2).translate(1e8,2e8,-3e8);q=m.mass_properties()
        self.assertAlmostEqual(q["inertia"][0][0],40)
        self.assertAlmostEqual(q["inertia"][1][1],50)
        for a,b in zip(q["centroid"],(1e8-1.5,2e8+1,-3e8+2)):self.assertAlmostEqual(a,b)

    def test_mass_reversed_orientation(self):
        m=self.mesh(BOX_V,[t[::-1] for t in BOX_F]);p=m.mass_properties()
        self.assertAlmostEqual(p["mass"],1);self.assertAlmostEqual(p["inertia"][0][0],1/6)

    def test_mass_validation(self):
        m=self.box()
        for density in (0,-1,math.nan,math.inf):
            with self.assertRaises(MeshError):m.mass_properties(density)
        m=self.mesh(BOX_V,BOX_F[:1])
        with self.assertRaises(MeshError):m.mass_properties()

    def test_nearest_triangle_regions(self):
        m=self.mesh([(0,0,0),(1,0,0),(0,1,0)],[(0,1,2)])
        p=[(.25,.25,2),(-1,-1,0),(.5,-1,0),(1,1,0)]
        r=m.nearest_points(p)
        for actual,expected in zip(r["distances"],(2,math.sqrt(2),1,math.sqrt(.5))):self.assertAlmostEqual(actual,expected)
        self.assertEqual(r["points"],[(.25,.25,0),(0,0,0),(.5,0,0),(.5,.5,0)])
        self.assertEqual(r["face_ids"],[0]*4)

    def test_degenerate_unsigned_distance(self):
        m=self.mesh([(0,0,0),(1,0,0),(2,0,0)],[(0,1,2)])
        self.assertAlmostEqual(m.nearest_points([(1,1,0)])["distances"][0],1)
        with self.assertRaises(MeshError):m.nearest_points([(1,1,0)],signed=True)

    def test_bvh_against_analytic_cube_distance(self):
        m=self.box();random.seed(321)
        pts=[tuple(random.uniform(-2,3) for _ in range(3)) for _ in range(500)]
        r=m.nearest_points(pts)
        for p,d in zip(pts,r["distances"]):
            delta=[max(0,-x,x-1) for x in p]
            expected=math.hypot(*delta) if any(delta) else min(*p,*(1-x for x in p))
            self.assertAlmostEqual(d,expected,places=12)

    def test_signed_classification(self):
        m=self.box();p=[(.5,.5,.5),(2,.5,.5),(0,.2,.3),(0,0,0),(1,1,.5)]
        self.assertEqual(m.classify_points(p),[-1,1,0,0,0])
        self.assertEqual(m.contains(p),[True,False,True,True,True])
        self.assertEqual(m.contains(p,include_boundary=False),[True,False,False,False,False])
        self.assertEqual(m.nearest_points(p,signed=True)["distances"],[-.5,1,0,0,0])

    def test_bvh_invalidation(self):
        m=self.box();self.assertEqual(m.nearest_points([(2,.5,.5)])["distances"],[1])
        m.translate(10,0,0)
        self.assertEqual(m.nearest_points([(2,.5,.5)])["distances"],[8])
        self.assertEqual(m.section((10.5,0,0),(1,0,0)).area,1)

    def test_empty_queries_and_errors(self):
        m=self.box();self.assertEqual(m.nearest_points([])["distances"],[])
        self.assertEqual(m.classify_points([]),[])
        for p in ([(1,2)],[(math.nan,0,0)]):
            with self.assertRaises(ValueError):m.nearest_points(p)
        for eps in (-1,math.nan,math.inf):
            with self.assertRaises(ValueError):m.classify_points([(0,0,0)],eps)

    def test_collision_separation_touch_overlap(self):
        a=self.box();b=self.box(offset=(2,0,0))
        self.assertEqual(a.collision(b)["kind"],"separated")
        self.assertAlmostEqual(a.distance_to(b)["distance"],1)
        b.translate(-1,0,0)
        self.assertEqual(a.collision(b)["kind"],"surface_contact")
        self.assertEqual(a.distance_to(b)["distance"],0)
        b.translate(-.2,0,0);self.assertTrue(a.collision(b)["collides"])

    def test_collision_corner_touch(self):
        a=self.box();b=self.box(offset=(1,1,1))
        self.assertTrue(a.collision(b)["collides"]);self.assertEqual(a.distance_to(b)["distance"],0)

    def test_containment(self):
        a=self.box(3);b=self.box(offset=(1,1,1))
        self.assertEqual(a.collision(b)["kind"],"containment")
        self.assertFalse(a.collision(b,solid=False)["collides"])
        self.assertAlmostEqual(a.distance_to(b)["distance"],1)

    def test_disconnected_component_containment(self):
        a=self.mesh(*join(box_arrays(offset=(10,0,0)),box_arrays(offset=(1,1,1))))
        b=self.box(3)
        self.assertEqual(a.collision(b)["kind"],"containment")

    def test_hollow_solid(self):
        v,f=box_arrays(offset=(1,1,1))
        m=self.mesh(*join(box_arrays(3),(v,[t[::-1] for t in f])))
        self.assertAlmostEqual(m.mass_properties()["volume"],26)
        self.assertEqual(m.classify_points([(1.5,1.5,1.5),(.5,.5,.5)]),[1,-1])
        inner=self.box(.2,(1.4,1.4,1.4))
        self.assertFalse(m.collision(inner)["collides"])
        sec=m.section((0,0,1.5));self.assertEqual(len(sec.polylines),2)
        self.assertAlmostEqual(sec.area,8);self.assertAlmostEqual(sec.perimeter,16)

    def test_coplanar_triangle_collision(self):
        a=self.mesh([(0,0,0),(2,0,0),(0,2,0)],[(0,1,2)])
        b=self.mesh([(2,2,0),(2,.75,0),(.75,2,0)],[(0,1,2)])
        self.assertFalse(a.collision(b,solid=False)["collides"])
        self.assertAlmostEqual(a.distance_to(b)["distance"],.75/math.sqrt(2))
        b.translate(-.5,-.5,0);self.assertTrue(a.collision(b,solid=False)["collides"])

    def test_triangle_piercing(self):
        a=self.mesh([(0,0,0),(2,0,0),(0,2,0)],[(0,1,2)])
        b=self.mesh([(.5,.5,-1),(.5,.5,1),(.5,1,0)],[(0,1,2)])
        self.assertTrue(a.collision(b,solid=False)["collides"])
        self.assertEqual(a.distance_to(b)["distance"],0)

    def test_bbox_overlap_does_not_imply_collision(self):
        a=self.mesh([(0,0,0),(1,0,0),(0,1,0),(0,0,1)],[(0,2,1),(0,1,3),(0,3,2),(1,2,3)])
        b=self.box(.1,(.8,.8,.8))
        self.assertFalse(a.collision(b)["collides"])
        self.assertAlmostEqual(a.distance_to(b)["distance"],1.4/math.sqrt(3))

    def test_surface_mode_open_mesh(self):
        a=self.mesh(BOX_V,BOX_F[:1]);b=self.box()
        with self.assertRaises(MeshError):a.collision(b)
        self.assertTrue(a.collision(b,solid=False)["collides"])

    def test_cube_sections_and_coplanar_diagonals(self):
        m=self.box()
        for z in (0,.25,.5,1):
            with self.subTest(z=z):
                s=m.section((0,0,z))
                self.assertEqual(s.closed,(True,));self.assertEqual(s.branch_vertices,0)
                self.assertAlmostEqual(s.area,1);self.assertAlmostEqual(s.perimeter,4)
                if z in (0,1):self.assertEqual(len(s.segments),4)

    def test_tangent_and_empty_sections(self):
        m=self.box();s=m.section((0,0,2));self.assertEqual(s.polylines,());self.assertEqual(s.area,0)
        s=m.section((0,0,0),(1,1,1));self.assertEqual(s.area,0)
        s=m.section((0,0,0),(1,1,0));self.assertEqual(s.closed,(False,))
        with self.assertRaises(MeshError):_ = s.area

    def test_oblique_section(self):
        m=self.box();s=m.section((.5,.5,.5),(1,1,1))
        self.assertAlmostEqual(s.area,3*math.sqrt(3)/4)
        self.assertAlmostEqual(s.perimeter,3*math.sqrt(2))
        reverse=m.section((.5,.5,.5),(-2,-2,-2))
        self.assertAlmostEqual(s.area,reverse.area)

    def test_open_section_and_branch(self):
        m=self.mesh([(0,0,-1),(1,0,1),(-1,0,1)],[(0,1,2)])
        s=m.section();self.assertEqual(s.closed,(False,))
        with self.assertRaises(MeshError):_ = s.area
        # Three coplanar triangles sharing an edge create branch vertices.
        m=self.mesh([(0,0,0),(1,0,0),(0,1,0),(0,-1,0),(2,1,0)],[(0,1,2),(0,1,3),(0,1,4)])
        s=m.section();self.assertGreater(s.branch_vertices,0)
        with self.assertRaises(MeshError):_ = s.area

    def test_slicing_axes(self):
        m=self.box()
        for axis in "xyz":
            sections=list(m.slices([-.1,0,.5,1,1.1],axis=axis))
            self.assertEqual([s.area for s in sections],[0,1,1,1,0])

    def test_scale_and_translation_sections(self):
        for scale in (1e-6,1,1e6):
            m=self.box(scale,tuple(10*scale for _ in range(3)))
            s=m.section((0,0,10.5*scale),tolerance=scale*1e-9)
            self.assertAlmostEqual(s.area/(scale*scale),1)
            self.assertAlmostEqual(s.perimeter/scale,4)

    def test_tolerance_validation(self):
        m=self.box()
        for normal in ((0,0,0),(math.nan,0,1)):
            with self.assertRaises(ValueError):m.section(normal=normal)
        with self.assertRaises(ValueError):m.section(tolerance=-1)

    def test_closed_geometry_lifetime(self):
        m=self.box();s=m.section((0,0,.5));m.close()
        self.assertEqual(s.area,1)
        for fn in (m.mass_properties,lambda:m.section(),lambda:m.nearest_points([])):
            with self.assertRaises(MeshError):fn()

    def test_pair_lock_order(self):
        a=self.box();b=self.box(offset=(2,0,0))
        def run(reverse):return (b.distance_to(a) if reverse else a.distance_to(b))["distance"]
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(list(pool.map(run,[False,True]*10)),[1]*20)

    def test_random_box_collision_and_clearance(self):
        a=self.box();rng=random.Random(44)
        for _ in range(80):
            offset=tuple(rng.uniform(-2,2) for _ in range(3))
            with Mesh.from_arrays(*box_arrays(offset=offset)) as b:
                gap=[max(abs(x)-1,0) for x in offset]
                self.assertEqual(a.collision(b)["collides"],not any(gap))
                self.assertAlmostEqual(a.distance_to(b)["distance"],math.hypot(*gap))

    def test_collision_tolerance_and_repeated_self_query(self):
        a=self.box();b=self.box(offset=(1+1e-10,0,0))
        self.assertFalse(a.collision(b,tolerance=0)["collides"])
        self.assertTrue(a.collision(b,tolerance=1e-9)["collides"])
        self.assertEqual(a.distance_to(a)["distance"],0)
        self.assertTrue(a.collision(a)["collides"])

    def test_numpy_geometry_results(self):
        try:import numpy as np
        except ImportError:self.skipTest("Optional NumPy is not installed")
        m=self.box();r=m.nearest_points([(2,.5,.5)],numpy=True);m.close()
        self.assertEqual(r["points"].shape,(1,3));self.assertEqual(r["face_ids"].dtype,np.int64)
        self.assertEqual(r["distances"][0],1)

    def test_concave_prism(self):
        poly=[(0,0),(2,0),(2,1),(1,1),(1,2),(0,2)]
        v=[(x,y,z) for z in (0,1) for x,y in poly]
        top=[(0,1,3),(1,2,3),(0,3,5),(3,4,5)]
        f=[t[::-1] for t in top]+[tuple(i+6 for i in t) for t in top]
        for i in range(6):
            j=(i+1)%6;f.extend([(i,j,j+6),(i,j+6,i+6)])
        m=self.mesh(v,f)
        self.assertAlmostEqual(m.mass_properties()["volume"],3)
        s=m.section((0,0,.5));self.assertAlmostEqual(s.area,3);self.assertAlmostEqual(s.perimeter,8)
        self.assertEqual(m.classify_points([(.5,.5,.5),(1.5,1.5,.5)]),[-1,1])

    def test_exact_section_without_welding_tolerance(self):
        m=self.box();s=m.section((0,0,.5),tolerance=0)
        self.assertEqual(s.closed,(True,));self.assertEqual(s.area,1)

    def test_crossing_section_rejected(self):
        from mesh_testbed import Section
        line=((0,0,0),(1,1,0),(0,1,0),(1,0,0),(0,0,0))
        s=Section((0,0,0),(0,0,1),tuple(zip(line,line[1:])),(line,),0,0,1e-9)
        with self.assertRaises(MeshError):_ = s.area

if __name__=="__main__":unittest.main()
