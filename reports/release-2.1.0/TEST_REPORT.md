# Local completion and test report — 2.1.0

Date: 2026-11-11. Scope: HW4 local mesh properties, HW7 tetrahedron predicates,
Bézier distribution consistency and regression of existing geometry APIs.

Implemented batch classification/weights/degeneracy, face properties, unique edges,
two explicitly named vertex area measures, native version export and ABI-2 additive
interfaces. Original homework applications remain unchanged as references.
No FEM/topology optimizer, AI runtime, point-triangle or point-plane public API was added.

Windows: 82/82 main tests passed with no skips. Original compatibility suites passed
4 HW4, 10 HW6 and 14 HW7 tests. The Cylinder face centroids, midpoints and HW4 tile
areas agreed with original Python; 1,000 random tetrahedron queries (seed 211)
agreed in states and weights. These checks overlap; their counts are not additive
independent-feature coverage. The earlier extracted local package passed 80 tests
and skipped two because NumPy and original model fixtures were not included.

Fifteen added tests cover analytic states/weights, 300 affine-transformed random
points, large/small scales, degeneracy, tolerances, invalid inputs, empty batches,
analytic triangle properties, partition sums, transforms, isolated vertices,
resource lifetime, short/null native buffers and Bézier analytic/invalid cases.
The previous 67 tests cover STL, topology, mass, transforms, distances, collision,
sections, slicing, concurrency and resource management.

Integration fixes: synchronized previously missing Bézier exports in packages;
separated HW4 tile area (sum = total area/4) from barycentric area (sum = total area);
corrected a comparison-script import path shadowed by an old homework package;
updated historical-hash-bound packaging scripts for the new release.

At the time of local verification, non-Windows execution remained pending. It has
since passed in native CI; see ../../CI_REPORT.md. Interactive GUI rendering was
not repeated for 2.1.0. No memory-sanitizer run, exact-predicate proof or new speed
benchmark was performed. Floating-point and solid-input limitations remain.

Evidence: suite.json/suite.log, homework logs, homework_comparison.json and packages.json.
Run tools/run_test_suite.py with PYTHONPATH and MESH_CORE_LIBRARY set to the intended package.

Native DLL SHA256: `f96c33b990e3c2b32b2f204510f2fc52681c0b3a7375b685189408824c920428`

| Test | Status | Seconds |
|---|---|---|
| `test_analysis.AnalysisTests.test_bezier_curve_analytic` | passed | 0.030444 |
| `test_analysis.AnalysisTests.test_bezier_invalid` | passed | 0.000075 |
| `test_analysis.AnalysisTests.test_bezier_surface_analytic` | passed | 0.000206 |
| `test_analysis.AnalysisTests.test_closed_and_owned_results` | passed | 0.000113 |
| `test_analysis.AnalysisTests.test_degenerate_normals_and_isolated_vertex` | passed | 0.000054 |
| `test_analysis.AnalysisTests.test_invalid_and_empty` | passed | 0.000207 |
| `test_analysis.AnalysisTests.test_native_buffers` | passed | 0.000063 |
| `test_analysis.AnalysisTests.test_partition_and_transform` | passed | 0.000287 |
| `test_analysis.AnalysisTests.test_random_affine_reconstruction` | passed | 0.001267 |
| `test_analysis.AnalysisTests.test_scale_and_translation` | passed | 0.000077 |
| `test_analysis.AnalysisTests.test_single_triangle_properties` | passed | 0.000170 |
| `test_analysis.AnalysisTests.test_tetra_degenerate` | passed | 0.000058 |
| `test_analysis.AnalysisTests.test_tetra_states_and_weights` | passed | 0.000047 |
| `test_analysis.AnalysisTests.test_tolerances` | passed | 0.000053 |
| `test_analysis.AnalysisTests.test_version` | passed | 0.000018 |
| `test_full_validation.FullValidation.test_ascii_scientific_and_whitespace` | passed | 0.004337 |
| `test_full_validation.FullValidation.test_binary_nan_and_truncation` | passed | 0.008071 |
| `test_full_validation.FullValidation.test_closed_pair_and_save_access` | passed | 0.000976 |
| `test_full_validation.FullValidation.test_copy_is_independent` | passed | 0.000104 |
| `test_full_validation.FullValidation.test_each_rotation_axis` | passed | 0.000116 |
| `test_full_validation.FullValidation.test_general_affine_shear_volume` | passed | 0.000091 |
| `test_full_validation.FullValidation.test_invalid_transform_and_axis` | passed | 0.000074 |
| `test_full_validation.FullValidation.test_native_creation_failure_clears_handle` | passed | 0.000048 |
| `test_full_validation.FullValidation.test_native_output_guards` | passed | 0.000109 |
| `test_full_validation.FullValidation.test_parallel_same_mesh_reads` | passed | 0.039255 |
| `test_full_validation.FullValidation.test_random_rotated_nearest_points` | passed | 0.000905 |
| `test_full_validation.FullValidation.test_repeat_resource_lifecycle` | passed | 0.266385 |
| `test_full_validation.FullValidation.test_save_failure_does_not_leave_new_file` | passed | 0.001269 |
| `test_full_validation.FullValidation.test_save_failure_preserves_existing_file` | passed | 0.002665 |
| `test_full_validation.FullValidation.test_section_far_from_plane_origin` | passed | 0.000474 |
| `test_full_validation.FullValidation.test_signed_distance_and_mass_scaling` | passed | 0.000278 |
| `test_geometry.GeometryTests.test_bbox_overlap_does_not_imply_collision` | passed | 0.000176 |
| `test_geometry.GeometryTests.test_bvh_against_analytic_cube_distance` | passed | 0.001374 |
| `test_geometry.GeometryTests.test_bvh_invalidation` | passed | 0.000376 |
| `test_geometry.GeometryTests.test_closed_geometry_lifetime` | passed | 0.000328 |
| `test_geometry.GeometryTests.test_collision_corner_touch` | passed | 0.000102 |
| `test_geometry.GeometryTests.test_collision_separation_touch_overlap` | passed | 0.000129 |
| `test_geometry.GeometryTests.test_collision_tolerance_and_repeated_self_query` | passed | 0.000091 |
| `test_geometry.GeometryTests.test_concave_prism` | passed | 0.000681 |
| `test_geometry.GeometryTests.test_containment` | passed | 0.000178 |
| `test_geometry.GeometryTests.test_coplanar_triangle_collision` | passed | 0.000085 |
| `test_geometry.GeometryTests.test_crossing_section_rejected` | passed | 0.000045 |
| `test_geometry.GeometryTests.test_cube_sections_and_coplanar_diagonals` | passed | 0.000794 |
| `test_geometry.GeometryTests.test_degenerate_unsigned_distance` | passed | 0.000066 |
| `test_geometry.GeometryTests.test_disconnected_component_containment` | passed | 0.000112 |
| `test_geometry.GeometryTests.test_empty_queries_and_errors` | passed | 0.000078 |
| `test_geometry.GeometryTests.test_exact_section_without_welding_tolerance` | passed | 0.000131 |
| `test_geometry.GeometryTests.test_hollow_solid` | passed | 0.000662 |
| `test_geometry.GeometryTests.test_mass_cube` | passed | 0.000050 |
| `test_geometry.GeometryTests.test_mass_reversed_orientation` | passed | 0.000040 |
| `test_geometry.GeometryTests.test_mass_tetrahedron` | passed | 0.000056 |
| `test_geometry.GeometryTests.test_mass_translation_rotation` | passed | 0.000080 |
| `test_geometry.GeometryTests.test_mass_validation` | passed | 0.000092 |
| `test_geometry.GeometryTests.test_nearest_triangle_regions` | passed | 0.000052 |
| `test_geometry.GeometryTests.test_numpy_geometry_results` | passed | 0.087212 |
| `test_geometry.GeometryTests.test_oblique_section` | passed | 0.000926 |
| `test_geometry.GeometryTests.test_open_section_and_branch` | passed | 0.000327 |
| `test_geometry.GeometryTests.test_pair_lock_order` | passed | 0.001530 |
| `test_geometry.GeometryTests.test_random_box_collision_and_clearance` | passed | 0.004797 |
| `test_geometry.GeometryTests.test_scale_and_translation_sections` | passed | 0.000935 |
| `test_geometry.GeometryTests.test_signed_classification` | passed | 0.000152 |
| `test_geometry.GeometryTests.test_slicing_axes` | passed | 0.001381 |
| `test_geometry.GeometryTests.test_surface_mode_open_mesh` | passed | 0.000111 |
| `test_geometry.GeometryTests.test_tangent_and_empty_sections` | passed | 0.000116 |
| `test_geometry.GeometryTests.test_tolerance_validation` | passed | 0.000055 |
| `test_geometry.GeometryTests.test_triangle_piercing` | passed | 0.000053 |
| `test_mesh.MeshTests.test_analytic_tetrahedron` | passed | 0.000084 |
| `test_mesh.MeshTests.test_ascii_stl` | passed | 0.002421 |
| `test_mesh.MeshTests.test_c_buffer_checks` | passed | 0.000072 |
| `test_mesh.MeshTests.test_concurrent_independent_instances` | passed | 0.001821 |
| `test_mesh.MeshTests.test_corrupt_stl` | passed | 0.011912 |
| `test_mesh.MeshTests.test_failed_transform_is_atomic` | passed | 0.000138 |
| `test_mesh.MeshTests.test_inconsistent_orientation` | passed | 0.000047 |
| `test_mesh.MeshTests.test_invalid_arrays` | passed | 0.000061 |
| `test_mesh.MeshTests.test_lifetime` | passed | 0.000039 |
| `test_mesh.MeshTests.test_nonmanifold_and_degenerate` | passed | 0.000074 |
| `test_mesh.MeshTests.test_open_mesh` | passed | 0.000030 |
| `test_mesh.MeshTests.test_reflection` | passed | 0.000038 |
| `test_mesh.MeshTests.test_reverse_halfedges` | passed | 0.000050 |
| `test_mesh.MeshTests.test_supplied_models` | passed | 0.163191 |
| `test_mesh.MeshTests.test_transform` | passed | 0.000121 |
| `test_mesh.MeshTests.test_unicode_binary_roundtrip` | passed | 0.007882 |
