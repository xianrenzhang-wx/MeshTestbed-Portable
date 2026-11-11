# Release 2.1.0 — 2026-11-11

> Update 2026-11-11: GitHub Actions native builds and all 82 tests passed on Windows, Linux, macOS ARM64 and macOS Intel (zero skips). See [CI_REPORT.md](CI_REPORT.md) for evidence and downloads. Earlier validation statements below are historical.

- Added batched tetrahedron classification, barycentric coordinates and explicit degeneracy states.
- Added face centroids, unit normals, face areas, barycentric vertex areas and separately named HW4 centroidal tile areas.
- Added sorted unique mesh edges and midpoints.
- Unified cubic/bicubic Bézier extensions across native build targets and Python packaging.
- Added native version export; preserved ABI 2 and existing signatures.
- Added dependency-free analysis demo, API reference and Chinese usage guide.
- Added numerical and buffer-validation regression tests. See reports/release-2.1.0 for actual results.

No new FEM solver, topology optimizer, GPU backend or deep-learning runtime dependency.
Linux/macOS native runtime validation remains pending; binary construction is not runtime certification.
