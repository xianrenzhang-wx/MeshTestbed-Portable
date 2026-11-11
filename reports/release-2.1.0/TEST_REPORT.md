# MeshTestbed Portable 2.1.0 完成与测试报告

报告日期：2026-11-11。范围：本轮 HW4/HW7 通用计算集成、Bézier 发布统一和现有几何功能回归。

## 1. 完成情况

| 项目 | 结果 |
|---|---|
| HW7 向量判断 | C++ 批量四面体内外/边界/退化分类，返回重心坐标；Python 接口 tetrahedron |
| HW4 网格属性 | 面心、单位法向、面面积、唯一边/中点、barycentric 顶点面积、单独命名的 HW4 tile 面积 |
| HW6 Bézier | 原有三次曲线/双三次曲面扩展纳入四个平台的统一构建与包 |
| 版本 | Python 与原生 release 2.1.0；保留 ABI 2，新增 mc_version 和三个分析接口 |
| 使用材料 | API.md、USAGE.md、CHANGELOG.md、analysis_demo.py、C 头文件 |
| 发布 | 四个平台独立包和一个 All-Platforms 总包，附 SHA256 校验 |

原始作业代码保留，作为对照与演示。没有改写 HW5 优化器、期中 AI 模型或旧 GUI；没有新增点三角形/点平面公共接口，这些仍是后续扩展。

## 2. 实测结论

| 验证 | 结果 |
|---|---|
| Windows 主套件 | 82/82 通过，0 失败、0 错误、0 跳过 |
| HW4 原有兼容性测试 | 4/4 通过，指定新版 DLL |
| HW6 原有兼容性测试 | 10/10 通过，指定新版 DLL |
| HW7 原有兼容性测试 | 14/14 通过，指定新版 DLL |
| HW4 独立对照 | Cylinder 的面心、边中点和 HW4 tile 面积与原 Python 实现一致 |
| HW7 独立对照 | 固定种子 211 的 1000 个随机点，状态与权重和原 Python 实现一致 |
| Windows 平台 ZIP / 总 ZIP | 解压后 -S 模式运行，三个示例成功；82 项中 80 通过、2 预期跳过 |
| 四平台二进制 | 架构、导出接口、依赖检查通过，包含全部 25 个声明接口 |
| Linux/macOS 原生执行 | 未执行；不计作通过 |
| 新版交互式显示 | 本轮未重测；仅有历史版本 Windows 显示证据 |

-S 模式不加载 site-packages；两个跳过来自可选 NumPy 与未随运行包分发的原工程模型。包内基本计算示例无第三方 Python 依赖。兼容性测试与主套件存在覆盖重叠，不将其简单相加当作独立功能数。

## 3. 测试方法与覆盖

新增 15 项主测试覆盖解析四面体状态与权重、300 个随机重心坐标经剪切/反向/平移后的恢复、大小尺度与大平移、退化几何、容差边界、非有限输入、空批次、解析三角形属性、面积求和恒等式、变换后的更新、孤立顶点、零面积法向、关闭后访问、原生空指针/短缓冲区，以及 Bézier 解析结果和非法输入。

其余 67 项回归覆盖 STL 读写、损坏文件、拓扑、质量/惯性、变换、最近点、内外判断、碰撞、包含、截面、切片、资源管理及并发等。随机测试固定种子，但不是穷举证明；未执行专门内存检测器、精确算术证明或新增性能基准。

## 4. 实施中发现并处理的问题

1. 原源码含 Bézier 扩展，而旧总包缺失：统一四个平台编译源文件与 Python 模块，按头文件检查所有导出。
2. HW4 的 tile 面积不是完整顶点对偶面积：分别提供两个明确命名的量，并验证总和分别为总面积和总面积的 1/4。
3. 本地多个作业目录带有旧 mesh_testbed 副本：对照脚本第一次导入旧副本而无法找到 analysis；调整导入路径后通过。此为测试路径问题，不是数值算法错误。使用指南已列出排查方法。
4. 旧打包脚本绑定历史版本与历史 hash：更新到 2.1.0 独立输出与本轮审计证据，旧压缩包及报告保留。

## 5. 数值与使用边界

四面体容差按无量纲权重/归一化行列式定义，不能当成欧氏距离。近退化元素可能被返回状态 2，权重为 None；不应继续用于插值。有限精度和极端坐标可能产生误差或溢出错误。网格实体计算仍要求合适的闭合/方向/非退化输入，自相交等尚未全面验证。新增局部属性允许开口网格，唯一边按索引去重，不进行坐标焊接。旧版 ABI 2 不保证含所有新版扩展，升级应替换整个包。

## 6. 运行环境与二进制证据

- Windows 环境：`Windows-11-10.0.26200-SP0`
- Python：`3.12.14 (main, Aug 25 2026, 14:01:42) [MSC v.1944 64 bit (AMD64)]`
- 主套件时间：0.741 秒（本次运行，不作为性能承诺）
- Windows DLL SHA256：`f96c33b990e3c2b32b2f204510f2fc52681c0b3a7375b685189408824c920428`

| 目标 | 架构 | 导出数 | 缺失 | 系统依赖 |
|---|---|---|---|---|
| windows-x86_64 | 0x8664 | 25 | 0 | api-ms-win-crt-convert-l1-1-0.dll, api-ms-win-crt-locale-l1-1-0.dll, api-ms-win-crt-runtime-l1-1-0.dll, api-ms-win-crt-string-l1-1-0.dll, KERNEL32.dll, api-ms-win-crt-heap-l1-1-0.dll, api-ms-win-crt-stdio-l1-1-0.dll, api-ms-win-crt-private-l1-1-0.dll |
| linux-x86_64 | EM_X86_64 | 25 | 0 | libm.so.6, libpthread.so.0, libc.so.6, libdl.so.2, ld-linux-x86-64.so.2 |
| macos-arm64 | 16777228 | 25 | 0 | /usr/lib/libSystem.B.dylib |
| macos-x86_64 | 16777223 | 25 | 0 | /usr/lib/libSystem.B.dylib |

## 7. 复现与证据文件

源码根目录下设置 PYTHONPATH 为 python，MESH_CORE_LIBRARY 为匹配的新版库，运行：

```text
python tools/run_test_suite.py --output reports/release-2.1.0/suite.json
python -m unittest discover -s ../HW4_BRep -v
python -m unittest discover -s ../HW6_Bezier -v
python -m unittest discover -s ../HW7_Vector -v
python tools/package.py
python tools/audit_packages.py
python tools/package_bundle.py
```

主套件完整环境使用 NumPy；作业测试还使用对应作业的依赖。二进制审计额外依赖 pefile、pyelftools、macholib，均为开发工具依赖，运行包无需安装。交叉编译命令见 README/tools/build_zig.py。

- suite.json / suite.log：逐项结果、环境、DLL hash。
- HW4_BRep.log、HW6_Bezier.log、HW7_Vector.log：原作业兼容性结果。
- homework_comparison.json：原实现对照结论。
- packages.json：四平台架构、依赖、导出、hash、Windows 平台包示例及测试日志。
- 总包旁 .validation.json：总包解压后的实际示例和测试输出。
- 总包旁 .zip.sha256：最终压缩包校验值。

## 8. 主套件逐项结果

| 用例 | 状态 | 秒 |
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
