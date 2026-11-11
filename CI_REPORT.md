# Native CI test report — 2.1.0

Date: 2026-11-11. Tested commit: `0525fb168bd513c37c41b200b8d6dceca98231d1`.

[Workflow run and artifacts](https://github.com/xianrenzhang-wx/MeshTestbed-Portable/actions/runs/42992820689)

| Target | Compiler | Python | Results |
|---|---|---|---|
| Windows x86_64 | MSVC 19.51 | 3.11.9 | 82 passed; 0 failures/errors/skips |
| Ubuntu 22.04 x86_64 | GCC 11.4 | 3.11.18 | 82 passed; 0 failures/errors/skips |
| macOS 15 ARM64 | AppleClang 17 | 3.11.9 | 82 passed; 0 failures/errors/skips |
| macOS 15 Intel | AppleClang 17 | 3.11.9 | 82 passed; 0 failures/errors/skips |

Each job completed native CMake compilation, CTest, installation, three examples,
installed-package unittest discovery, and a recorded JSON/log test run. NumPy 2.3.5
and five STL fixtures were available. Each platform artifact contains its native
library, Python modules, examples, headers, tests and documentation.

This verifies computation, not interactive OpenGL rendering. It does not certify
all OS versions or earlier cross-compiled binaries. The Release packages preserve
these exact tested native binaries and record their SHA256 against suite.json.

The original Actions artifacts expire on 2027-02-09. GitHub Releases provides the
packaged downloads independently of Actions artifact retention.

Historical local reports remain useful evidence but their pending-platform status
is superseded by this native run. See VALIDATION.md for the chronology.
