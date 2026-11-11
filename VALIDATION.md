# 2.1.0 验证入口

本轮结果见 reports/release-2.1.0/TEST_REPORT.md（总包 docs/release-2.1.0）。下面的 2.0.x 结果是历史记录。

# 验证记录：v2 网格几何与制造分析

2026-09-26 完整复测更新：现为 v2.0.1，扩展至 67 项测试并全部通过，修复大坐标截面面积消减误差、导出失败破坏目标文件、NumPy 混用后的 ASCII STL 解析异常。Windows 实际 OpenGL 3.3 显示已验证（Polyscope 2.6.1，两次显示及变换后渲染）。详细证据见源码目录 `reports/full-test-2026-09-26/测试报告.md`。下文 51 项和旧计时保留为 v2 初版记录，不代表本次完整复测的统计。

日期：2026-09-26。宿主：Windows x86_64，Python 3.12.14，Zig 0.14.1 / Clang 19.1.7。

| 交付包 | 编译 | 原生运行 |
|---|---|---|
| windows-x86_64 | CMake + Ninja 成功 | 51 项 unittest 全部通过；CMake/CTest 通过；独立安装目录示例通过 |
| linux-x86_64 | Zig 交叉编译成功 | 未测试：当前宿主没有可用 Linux/WSL 环境 |
| macos-arm64 | Zig 交叉编译成功 | 未测试：当前没有 macOS 环境 |
| macos-x86_64 | Zig 交叉编译成功 | 未测试：当前没有 macOS 环境 |

Windows 测试包含原始工程的 Cow、Cylinder、cube_in、foot、turbine_blade 共 5 个 STL 的读取和保存往返。解析四面体体积为 1/6，面积为 (3+sqrt(3))/2；验证缩放、旋转、平移、反射，以及损坏输入、Unicode 路径、半边关系、对象关闭、线程独立实例。NumPy 数组形状、类型与关闭模型后的数据生命周期另行验证通过。

v2 新增验证：立方体/四面体的解析质心和惯性、长方体旋转惯性、凹 L 形棱柱、反向面方向、空腔实体、500 个随机点与解析立方体距离对照、80 对随机立方体的碰撞与间隙对照、共面相交与分离、三角形穿透、点/边接触、完全包含、多连通分量包含、包围盒重叠但实体不相交、模型变换后的 BVH 重建、各轴切片、斜切正六边形、共面面的对角线去除、孔洞截面、相切点和边、开放/分叉/交叉轮廓拒绝面积计算，以及相反顺序的双模型并发查询。

真实模型新增观察见 `geometry_validation.json`。该报告可通过 `tools/validate_geometry.py` 重现。所有 5 个模型完成质量属性、10,000 点查询和中间 Z 截面计算；Cow 的两条截面轮廓存在严格线段交叉，返回轮廓但拒绝计算面积。这不构成对原模型实体合法性的完整认证，质量属性仍依赖输入有效性。

本机单次观察（索引建立后，包含 Python 数据准备与结果转换的批量调用）：

| 模型 | 三角形数 | 10,000 个无符号最近点查询 |
|---|---:|---:|
| Cow | 5,804 | 约 0.065 s |
| cube_in | 12 | 约 0.019 s |
| Cylinder | 400 | 约 0.039 s |
| foot | 20,016 | 约 0.101 s |
| turbine_blade | 2,750 | 约 0.054 s |

以上不是跨硬件性能保证，也没有与旧 Visual Studio 程序比较。带符号查询、碰撞和轮廓面积分析采用不同算法，不应套用该计时。

静态二进制依赖检查：

* Windows 包依赖 KERNEL32 和系统 UCRT API DLL；不依赖 MFC、OpenGL 或额外的 libstdc++ DLL。面向已有系统 UCRT 的 Windows 10/11；不是完全无系统依赖。
* Linux 交叉编译目标是 glibc 2.28；动态依赖为系统 libc、libm、libpthread、libdl 和动态加载器，没有外部 C++ 标准库依赖。仍需在实际发行版验证。
* 两个 macOS 包的 Mach-O 最低系统版本标记为 macOS 13.0，链接 `/usr/lib/libSystem.B.dylib`。已生成对应架构文件，尚未验证加载、签名策略与实际运行。

初版记录：当时尚未验证 Polyscope 图形窗口；本次 v2.0.1 已完成实际渲染验证，见文首更新。没有自动化测试所有鼠标键盘操作。不承诺相对于旧程序的加速倍数。

GitHub Actions 四个平台原生构建/测试流程已写好，但未上传或执行。跨平台交叉编译成功不等同于目标平台测试通过。

在目标系统解压对应 zip，进入目录后执行：

```text
python demo.py
python manufacturing_demo.py --layers 3 --output analysis.json
python -m unittest discover -s tests -v
```

压缩包不带原工程的 5 个模型，所以模型文件测试会跳过；没有安装可选 NumPy 时，相应的一项测试也会跳过。其余测试应通过。
