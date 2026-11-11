#pragma once
#include <stddef.h>
#include <stdint.h>
#ifdef _WIN32
#define MC_API __declspec(dllexport)
#else
#define MC_API __attribute__((visibility("default")))
#endif
#ifdef __cplusplus
extern "C" {
#endif
/* ABI 2. All counts are elements, not bytes. Caller owns output buffers.
   Handles must be live, created by this library, and externally synchronized.
   Status: 0 success, -1 failure; details in thread-local mc_last_error().
   Halfedge h=3*face+corner runs corner -> (corner+1)%3.
   Reverse: -1 boundary; -2 nonmanifold/inconsistently oriented edge. */
MC_API int mc_abi_version(void);
MC_API const char* mc_last_error(void);
MC_API int mc_from_stl(const unsigned char* data, size_t bytes, void** out);
MC_API int mc_from_arrays(const double* vertices, size_t nv, const int64_t* faces, size_t nf, void** out);
MC_API void mc_destroy(void* mesh);
MC_API int mc_counts(void* mesh, size_t* nv, size_t* nf);
MC_API int mc_copy_mesh(void* mesh, double* vertices, size_t vertex_elements, int64_t* faces, size_t face_elements);
MC_API int mc_copy_reverse(void* mesh, int64_t* reverse, size_t elements);
/* metrics: area, signed volume, xmin,ymin,zmin,xmax,ymax,zmax.
   topology: boundary halfedges, invalid halfedges, zero-area faces. */
MC_API int mc_metrics(void* mesh, double* metrics, size_t elements, size_t* topology, size_t topology_elements);
MC_API int mc_transform(void* mesh, const double* row_major_4x4);
/* Homogeneous solid: [volume,mass,centroid(3),inertia_at_centroid(9 row-major)]. */
MC_API int mc_mass_properties(void* mesh,double density,double* output,size_t elements);
/* Batch nearest points: result rows [distance,x,y,z]; face_ids has n elements.
   signed_distance != 0 requires closed oriented mesh; inside is negative. */
MC_API int mc_nearest(void* mesh,const double* points,size_t n,int signed_distance,double epsilon,
                      double* result,size_t elements,int64_t* face_ids,size_t face_elements);
/* states: -1 inside, 0 boundary (within epsilon), +1 outside. */
MC_API int mc_classify(void* mesh,const double* points,size_t n,double epsilon,int* states,size_t elements);
/* Surface distance. Contained disjoint surfaces can have positive distance. */
MC_API int mc_distance(void* mesh,void* other,double* distance,int64_t* faces,size_t elements);
/* result: 0 separated, 1 surfaces touch/intersect within SAT epsilon,
   2 solid containment (only when solid != 0). pair=(-1,-1) for containment. */
MC_API int mc_collision(void* mesh,void* other,int solid,double epsilon,int* result,int64_t* pair,size_t elements);
/* Plane section owns segment data until mc_section_destroy. Coplanar faces
   contribute their boundary edges, not triangulation diagonals. */
MC_API int mc_section(void* mesh,const double* origin,const double* normal,double epsilon,void** section);
MC_API int mc_section_size(void* section,size_t* segments);
MC_API int mc_section_copy(void* section,double* coordinates,size_t elements);
MC_API void mc_section_destroy(void* section);
/* Additive ABI 2 Bezier extension. Controls: 4x3 or 4x4x3 row-major.
   Curve includes both endpoints, so segments+1 output points.
   Surface vertex index a*(v_segments+1)+b corresponds to (u=a/nu,v=b/nv).
   Each parameter-space quad is split along its (a,b)--(a+1,b+1) diagonal.
   Faces follow increasing u cross increasing v. Counts are buffer elements.
   Subdivision counts must be in [1,1000]. */
MC_API int mc_bezier_curve(const double* controls,size_t segments,double* points,size_t elements);
MC_API int mc_bezier_surface(const double* controls,size_t u_segments,size_t v_segments,
                            double* points,size_t elements,int64_t* faces,size_t face_elements);
/* Additive ABI 2 extension, release 2.1.0. */
MC_API const char* mc_version(void);
/* vertices: 4x3; points: nx3; states: -1 inside,0 boundary,1 outside,2 degenerate.
   weights: nx4, NaN for degenerate. eps is dimensionless barycentric tolerance;
   degen tests abs(det(edges / longest_edge)). Buffers count scalar elements. */
MC_API int mc_tetra_classify(const double* vertices,const double* points,size_t n,double eps,double degen,
                           int* states,size_t ns,double* weights,size_t nw);
/* faces: nf x 7 [centroid xyz, unit normal xyz, area]; degenerate normal zero.
   vertices: nv x 2 [sum incident area/3, HW4 centroidal tile sum area/12]. */
MC_API int mc_local_properties(void* mesh,double* faces,size_t nf,double* vertices,size_t nv);
/* Sorted unique index pairs and midpoints. Query count using null buffers and
   zero capacities. Caller must lock the mesh across query and copy. */
MC_API int mc_unique_edges(void* mesh,int64_t* pairs,size_t np,double* midpoints,size_t nm,size_t* count);
#ifdef __cplusplus
}
#endif
