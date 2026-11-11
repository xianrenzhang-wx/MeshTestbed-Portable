# 2.1.0 使用流程

> Update 2026-11-11: GitHub Actions native builds and all 82 tests passed on Windows, Linux, macOS ARM64 and macOS Intel (zero skips). See [CI_REPORT.md](CI_REPORT.md) for evidence and downloads. Earlier validation statements below are historical.

## 1. 选择对应系统

解压新版 All-Platforms 压缩包，进入 windows-x86_64、linux-x86_64、macos-arm64
或 macos-x86_64。需要 Python 3.9+ 且进程架构一致。Linux 目标 glibc 2.28+；
macOS 目标 13+。Linux/macOS 已构建及检查接口，尚未完成原生运行验证。

计算无需第三方 Python 包，也不需要 Visual Studio、MFC 或编译器。
系统运行库和 Python 解释器不随包分发。

## 2. 运行示例

```text
python demo.py
python analysis_demo.py
python manufacturing_demo.py --layers 5 --output analysis.json
python -m unittest discover -s tests -v
```

macOS/Linux 可使用 python3。示例自动构造几何体，不需要下载模型。
analysis_demo 演示新版向量判断、网格属性、边中点和 Bézier。

## 3. 接入自己的程序

将当前平台的整个 mesh_testbed 文件夹复制到脚本旁边，不要只替换 DLL。

```python
from mesh_testbed import Mesh
from mesh_testbed.analysis import tetrahedron

vertices = [(0,0,0),(1,0,0),(0,1,0),(0,0,1)]
faces = [(0,2,1),(0,1,3),(0,3,2),(1,2,3)]
print(tetrahedron([(.2,.2,.2), (2,2,2)], vertices))
with Mesh.from_arrays(vertices, faces) as mesh:
    print(mesh.local_properties())
    print(mesh.unique_edges())
    print(mesh.mass_properties())
    mesh.save('tetrahedron.stl')
```

已有 STL 可使用 `with Mesh('part.stl') as mesh:`。数值单位由调用者统一。
四面体判断无需先创建 Mesh，适合批量计算；任意封闭实体用 classify_points。

## 4. 可选显示

```text
python -m pip install -r requirements-display.txt
python demo.py --show
```

显示依赖 NumPy、Polyscope 和桌面 OpenGL 驱动；依赖清单固定历史验证版本，
可用 wheel 由 pip 检查。不含离线显示 wheel。无界面服务器不要调用 show。

## 5. 常见问题

- 无法加载动态库：检查系统、处理器/Python 架构、库文件及系统运行库。
- 缺少扩展：旧 ABI 2 库不一定有新版接口；替换整个 2.1.0 包。
- 导入了旧库：检查脚本旁是否有旧 mesh_testbed，或 MESH_CORE_LIBRARY 是否指定旧文件。
- 体积或质量失败：检查网格闭合、面方向、退化面；并非所有网格都代表有效实体。
- 四面体返回状态 2：退化或接近退化；不能用其权重做插值。
- 顶点面积和总面积不一致：barycentric 总和等于总面积，HW4 tile 总和等于总面积的 1/4。

## 6. 开发与验证

源码开发可将 python 目录加入 PYTHONPATH。CMake 构建命令见 README。
tools/build_zig.py 可构建四个目标；tools/package.py 生成平台包，
tools/audit_packages.py 检查导出并验证 Windows 平台包，
tools/package_bundle.py 生成总包。新增接口定义见 API.md 与 include/mesh_core.h。
本轮详细结果保存在 reports/release-2.1.0，历史报告不作为新版测试证据。

本轮没有将 HW5 的 FEM/拓扑优化求解器或期中的 AI 模型放入几何库。
它们保留独立依赖和 Python 调用流程，后续可通过网格接口连接。
