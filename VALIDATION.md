# Validation history

## Current native validation: 2.1.0

On 2026-11-11, GitHub Actions built the library natively on Windows x86_64,
Ubuntu 22.04 x86_64, macOS 15 ARM64 and macOS 15 Intel. Each target passed all
82 tests with no failures, errors or skips. CTest, installed-package tests and
three examples also passed. See CI_REPORT.md for the immutable tested commit
and run link. Interactive rendering was not tested by this workflow.

## Local 2.1.0 validation

The Windows source suite passed 82 tests. Original HW4/HW6/HW7 compatibility suites
passed 4/10/14 tests against the updated DLL. Independent HW4 geometry and 1,000
HW7 random-point comparisons agreed with the original Python calculations.
The earlier minimal local ZIP passed 80 tests with two expected skips; current
native CI includes NumPy and all five fixtures, so no tests were skipped.

## Historical 2.0.1 validation (2026-09-26)

The Windows suite expanded from 51 to 67 passing tests. Fixes addressed large-offset
section area cancellation, destructive failed STL exports and ASCII parsing after
NumPy initialization. Real Polyscope 2.6.1/OpenGL 3.3 rendering was exercised twice,
including a transformed model and camera reset. Manual interaction, all drivers,
and headless rendering were not certified. Historical extracted packages passed
65 tests and skipped two. Linux/macOS were only cross-compiled at that time.

Five teaching meshes (Cow, cube_in, Cylinder, foot, turbine_blade) were checked.
Historical 10,000-point unsigned query observations ranged from roughly 0.019 to
0.101 seconds after BVH construction. These are single-machine observations, not
hardware-independent performance promises or comparisons against the legacy app.
Cow's crossing section contours were intentionally rejected for area computation.

The old Zig binaries had different runtime dependencies and minimum targets from
the native CI release. Native validation does not retroactively validate those
old binaries. See DEPENDENCIES.md and each release manifest for the current files.
