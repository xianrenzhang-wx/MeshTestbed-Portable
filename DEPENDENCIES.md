# Runtime dependencies

## Core computation

Python 3.9+ and a matching operating system/CPU architecture are required.
Native CI used Python 3.11. No NumPy, MFC, Visual Studio, compiler, CUDA or MATLAB
installation is needed for core computation. Python is not included.

Operating-system libraries are required and are not redistributed. Windows uses
Windows system DLLs (including the Universal C Runtime where imported); the MSVC
build uses a static C/C++ runtime. The Linux GCC build uses glibc, libstdc++ and
other system libraries reported in BINARY_DEPENDENCIES.json. macOS uses system
libraries such as libSystem and libc++. Do not copy the earlier cross-build
dependency assumptions onto these native CI artifacts.

The packages were tested on Windows Server 2025, Ubuntu 22.04, and macOS 15.
See BINARY_DEPENDENCIES.json for inspected imports, architecture and hash.
No broader minimum-OS compatibility is claimed beyond the test environments.

## Optional display

- NumPy 2.3.5
- Polyscope 2.6.1
- A working desktop graphics environment and OpenGL driver

Each platform ZIP contains wheels for CPython 3.11 of that architecture, including
dependencies resolved by pip. Install using requirements-display.txt and the local
wheels directory. Wheel contents retain upstream license and metadata files.
Other Python versions require a matching online installation or separate wheels.
GPU/driver software and Python itself are not included.

## Development only

CMake 3.20+ and a C++17 compiler build the library. NumPy enables optional tests.
Release inspection uses pefile and macholib plus the runner's readelf tool.
These inspection tools are not required by end users.
