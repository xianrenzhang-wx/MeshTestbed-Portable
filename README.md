# MeshTestbed Portable

MeshTestbed Portable aims to provide a flexible, high-performance foundation for geometry processing, engineering analysis, and automated model design.

The project combines **Python and a C++ dynamic library** to support both efficient computation and an extensible environment for future development.

## Why Python + C++?

**Python is the upper layer — the brain of the system.** It coordinates visualization, higher-level computation, and data analysis. Its flexibility also provides a foundation for future AI integration, automated model design, and iterative optimization.

**C++ is the computational foundation — the engine that carries out the work.** It handles core algorithms and intensive calculations. Packaging this capability as a dynamic library reduces the setup required by users while retaining the efficiency of native code.

Together, these layers combine C++ computational performance with Python's accessibility and flexibility.

## Project direction

The long-term aim is to connect geometry generation, analysis, simulation workflows, and optimization in a reusable environment. As the project develops, this foundation can support intelligent design tools that generate models, evaluate results, and improve designs through repeated iterations.

The current focus is geometry computation. AI-driven design and broader simulation capabilities are future extensions.

## Get started

- [Download a release](https://github.com/xianrenzhang-wx/MeshTestbed-Portable/releases)
- [Usage guide](USAGE.md)
- [API reference](API.md)
- [Test results](CI_REPORT.md)
