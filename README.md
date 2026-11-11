# MeshTestbed Portable 2.1.0

> Update 2026-11-11: GitHub Actions native builds and all 82 tests passed on Windows, Linux, macOS ARM64 and macOS Intel (zero skips). See [CI_REPORT.md](CI_REPORT.md) for evidence and downloads. Earlier validation statements below are historical.

本轮新增批量四面体判断/重心坐标、面心/法向/面积、唯一边/中点和两种顶点面积；Bézier 扩展已统一到四个平台构建中。

- [使用流程](USAGE.md)
- [完整 API 与 C ABI 说明](API.md)
- [更新记录](CHANGELOG.md)
- [2.1.0 测试报告](reports/release-2.1.0/TEST_REPORT.md)（源码目录；总包中见 docs/release-2.1.0）

Linux/macOS 尚未原生运行验证。下文保留已有安装和几何行为说明。

## 基础库说明

## HW6 Bezier 扩展

新增 `mesh_testbed.bezier.curve(controls, segments=100)` 和
`mesh_testbed.bezier.surface(controls, u_segments=20, v_segments=20)`。
采样与曲面三角化由 C++ `src/mesh_bezier.cpp` 完成。
交互程序、作业报告、独立运行包位于同级 `HW6_Bezier` 文件夹。
本地 `python/mesh_testbed/mesh_core.dll` 已升级，并保留 `mesh_core.pre_hw6.dll` 备份；
其他平台和旧 `dist` 包须重新构建，原有 ABI 2 网格接口兼容。

独立 C++17 计算动态库 + Python `ctypes` 接口。计算运行时不需要 Visual Studio、MFC、OpenGL、NumPy；显示功能可选。

v2 新增：均匀实体的质量/质心/惯性、批量最近点和带符号距离、内外判断、模型间表面距离和实体碰撞、任意平面截面、带孔轮廓面积、多层切片。完整接口和适用条件见 [GEOMETRY.md](GEOMETRY.md)。这批优先完成网格几何与制造分析，尚未提供完整 CAD/CAE/CAM 系统。

**升级时复制整个 `mesh_testbed` 文件夹**：v2 的 Python 文件和 ABI 2 动态库必须配套，不要与第一版 DLL 混用。

## 平台与交付

| 系统 | 动态库 | 架构 |
|---|---|---|
| Windows | `mesh_core.dll` | x86_64 |
| Linux | `libmesh_core.so` | x86_64 |
| macOS | `libmesh_core.dylib` | arm64 / x86_64，分别构建 |

每个系统需要自己的二进制，不能共用 DLL。库架构必须与 Python 进程一致；Python 3.9+。其他架构可从源码构建，尚未验证。Linux 二进制依赖系统 C/C++ 运行库及其最低版本；不承诺适用于所有发行版。Windows 的 MSVC 构建静态链接 C/C++ 运行库。

## 直接使用免安装包

将整个 `mesh_testbed` 文件夹复制到脚本旁边（内含 Python 模块和对应动态库），执行：

```python
from mesh_testbed import Mesh

with Mesh("Cow.stl") as mesh:
    print(mesh.counts)  # 顶点数、三角形数
    print(mesh.area())
    print(mesh.volume())
    print(mesh.metrics())
    mesh.scale(2).rotate("z", 0.5).translate(1, 2, 3)
    mesh.save("result.stl")
```

使用 `with` 或 `close()` 及时释放 C++ 内存。模型会一直留在原生内存中，不会每次重新读取文件。`metrics()` 一次调用返回面积、带符号体积、包围盒和网格诊断，适合批量实验。

源码目录的运行示例：将 `python` 目录加入 `PYTHONPATH`，并把库放在 `python/mesh_testbed` 中；也可用环境变量 `MESH_CORE_LIBRARY` 指定库的绝对路径。不要把编译器复制到运行包中。

## 显示（可选）

```text
python -m pip install numpy polyscope
```

```python
with Mesh("Cow.stl") as mesh:
    mesh.show()
    vertices, faces = mesh.get_mesh(numpy=True)  # (N,3) float64 / int64
```

不安装这些包也能使用所有计算接口。`get_mesh()` 默认返回两个扁平 ctypes 数组；`numpy=True` 在一次 C++ 内存复制后创建 NumPy 视图。返回数组拥有独立数据，关闭模型后仍可使用。显示依赖可用的桌面图形环境，服务器优化任务不要调用 `show()`。

## 源码构建：只需在构建电脑配置一次

准备 CMake 3.20+、C++17 编译器和 Python。Windows 可用 MSVC Build Tools（无需 MFC）、Linux 用 GCC/Clang、macOS 用 Xcode Command Line Tools。

在本目录运行：

```text
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release --parallel
ctest --test-dir build -C Release --output-on-failure
cmake --install build --config Release --prefix dist
```

`dist` 是交付目录，进入后可执行 `python demo.py`，或 `python demo.py /path/to/model.stl --show`。Windows 默认生成器若为 Visual Studio，可在配置命令中添加 `-A x64`；macOS 可使用 `-DCMAKE_OSX_ARCHITECTURES=arm64` 或 `x86_64`，测试时 Python 架构也须匹配。

也提供 Zig 0.14.1 交叉编译脚本，例如 `python tools/build_zig.py --zig /path/to/zig --target linux-x86_64`。支持上表四个目标；输出到 `dist/<目标>`。Linux 交叉编译目标为 glibc 2.28；该包不适用于 musl/Alpine。这能生成其他系统的文件，但不能替代目标系统运行验证。解压交付包后，可在目标系统运行 `python -m unittest discover -s tests -v`。

`.github/workflows/build.yml` 为 Windows、Linux、macOS Intel/Apple Silicon 分别构建、运行测试并上传交付包。要运行该流程，应将 **本目录作为 Git 仓库根目录**；如果放在更大的仓库中，需要把 workflow 移到仓库根目录的 `.github/workflows`，并相应调整工作目录。当前本地目录不是 Git 仓库，流程尚未上传或执行。

## 与原工程的关系、行为差异

原始 `MeshTestbed_C++` 保留不变，作者注释标明 Yong CHEN、12/05。此目录是其核心功能的独立标准 C++ 重实现，而不是原 MFC 类的二进制兼容包装。没有打包旧 OpenGL DLL，也没有复制旧窗口代码。

已覆盖：二进制/ASCII STL 读取、二进制 STL 保存、索引网格、反向半边、面积/带符号体积、包围盒、仿射变换、Python 调用和可选网格显示。

尚未迁移：旧菜单/对话框、鼠标选择、边凸凹分类、顶点法向/价数接口、变换历史，以及 Vertex 类中的所有点线面关系辅助函数。此库不是物理仿真求解器。

* STL 按**坐标完全相同**合并顶点；旧代码使用约 `1e-5` 容差。不会自动焊接相近但不重合的点，避免更改几何。需要容差焊接时应显式预处理。
* 二进制 STL 读取声明数量的三角形，允许忽略末尾附加数据（示例 cube 文件带 4 字节尾部校验数据）；不校验导出器私有校验码。
* `from_arrays(vertices, faces)` 保留传入索引，不自动焊接；faces 必须是从零开始的整数。
* 不默默删除退化三角形；`metrics()` 报告退化面和边问题。
* `volume()` 要求闭合、边方向一致且无零面积三角形，否则报错。默认返回绝对值；`signed=True` 保留方向符号。`metrics()['signed_volume']` 对开口网格只是代数值，不能当物理体积。未检测自相交、嵌套壳方向或全部顶点流形条件。
* 变换直接更新坐标，面积和体积随之变化；角度单位为弧度。STL 导出使用 float32，可能损失精度。
* 半边 `h=3*face+corner` 从当前角点指向下一个角点。`halfedges()[h]` 为反向半边，`-1` 表示边界，`-2` 表示非流形或方向冲突；不要假设编号与旧工程一致。
* 每个 Python Mesh 对象内部加锁，独立模型可以并行调用；ctypes 原生计算期间释放 GIL。库不会自动把单个计算并行化。
* 通过 C 接口传递调用方分配的缓冲区；C++ 异常转为错误码和线程局部错误文本。原生调用者须保证句柄有效，不能重复销毁或并发修改同一个句柄。

测试覆盖解析损坏文件、Unicode 路径、解析/保存往返、解析几何体的面积体积、方向与拓扑检查、变换、关闭后访问、缓冲区长度和独立实例并发。实际平台验证记录见 `VALIDATION.md`。
