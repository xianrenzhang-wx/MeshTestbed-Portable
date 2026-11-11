"""Build the Chinese audit report from retained test evidence (Markdown + HTML)."""
from pathlib import Path
import base64
import html
import json
import markdown

root=Path(__file__).resolve().parents[1]
out=root/'reports/full-test-2026-09-26'
suite=json.loads((out/'final-suite.json').read_text(encoding='utf-8'))
models=json.loads((out/'real-models.json').read_text(encoding='utf-8'))
packages=json.loads((out/'packages.json').read_text(encoding='utf-8'))
display=json.loads((out/'display.json').read_text(encoding='utf-8'))

text='''# MeshTestbed Portable 全功能测试报告

测试日期：2026年9月26日　测试对象：v2.0.1，原生接口 ABI 2

## 结论

本次对已经实现的网格计算、Python 调用、文件读写、资源管理、并发与显示进行了重新验证，并补充边界测试。原有 51 项测试通过；新增 16 项测试后发现并修复 3 类实际缺陷，最终 **67 项测试全部通过，失败 0，错误 0，跳过 0**。另外修正了重复显示时的初始化与自动取景。

Windows 解压包在不加载第三方 Python 包的环境中实际运行：67 项中 65 项通过、2 项按预期跳过。Polyscope 使用真实 OpenGL 后端完成两次渲染并保存截图。Linux 和两种 macOS 架构已经重新交叉编译并检查二进制及导出接口，**没有在目标系统运行，不能列为实机测试通过**。

本报告只覆盖已实现的功能，不代表完整 CAD、CAE、CAM 系统验收，也不代表代码行覆盖率达到 100%。未实现的 STEP/IGES、有限元、连续运动碰撞和刀路不计入通过项。

## 测试环境与方法

| 项目 | 实际环境或方法 |
|---|---|
| 操作系统 | Windows 11，版本 10.0.26200，x86_64 |
| Python | 3.12.14 |
| 编译工具 | Zig 0.14.1 / Clang 19.1.7，CMake + Ninja，Release |
| 可选显示依赖 | NumPy 2.3.5、Polyscope 2.6.1，独立测试目录安装 |
| 实际图形后端 | openGL3_glfw，OpenGL 3.3.0，驱动报告 Build 32.0.101.8132 |
| 数值判定 | 解析几何结果、随机解析对照、变换不变量、读写往返、错误条件检查 |
| 真实数据 | Cow、cube_in、Cylinder、foot、turbine_blade，共 5 个原始 STL |
| 交付验证 | 解压最终 Windows zip；清除源码路径及动态库环境变量；使用 Python -S 禁用第三方包 |

随机测试固定种子，便于复现。解析数值比较依用例采用约 7–12 位小数或归一化比例比较，并非对任意坐标规模的精度保证。计数中的一个测试方法可能包含多个模型、随机样本或子场景，因此 67 是测试方法数，不是所有输入样本总数。

## 功能覆盖与结果

| 功能 | 本次检查内容 | 结果 |
|---|---|---|
| STL 读取 | 二进制、ASCII、科学计数、空白、solid 二进制头、额外尾部、Unicode 文件名 | 通过 |
| 损坏输入处理 | 空文件、截断、异常三角形数、NaN 坐标、无效数组索引 | 通过 |
| STL 保存 | 二进制往返、5 个真实模型、float32 超范围、失败保留原文件与无残留新文件 | 修复后通过 |
| 数组建模与数据获取 | 顶点/三角形计数、数组复制、NumPy 输出、关闭模型后数组仍有效 | 通过 |
| 半边与拓扑诊断 | 反向半边互逆、边界、方向冲突、非流形边、退化面 | 通过 |
| 面积、体积与包围盒 | 单位四面体/立方体解析值、反射符号、开放网格拒绝体积 | 通过 |
| 几何变换 | X/Y/Z 旋转、平移、非均匀缩放、一般仿射剪切、错误矩阵不修改模型 | 通过 |
| 质量与惯性 | 立方体、四面体、长方体旋转、反向定向、空腔、凹棱柱、大小尺度 | 通过 |
| 最近点 | 面内/边/顶点、退化线段、500 个随机立方体点、200 个旋转后随机点 | 通过 |
| 带符号距离与内外判断 | 内部、边界、外部、孔洞、凹实体、边界是否计入包含 | 通过 |
| 模型间距离 | 分离、相交、包含、共面、80 对随机立方体解析间隙 | 通过 |
| 碰撞 | 表面接触、角点相切、三角形穿透、完全包含、多组件、包围盒假阳性 | 通过 |
| 空间索引 | 查询后变换模型，确认结果使用重建索引；重复查询与自查询 | 通过 |
| 任意平面截面 | 轴向、斜切、反向法线、共面边界、去掉剖分对角线、点/边相切 | 通过 |
| 轮廓面积与周长 | 闭合轮廓、孔洞、凹轮廓、开放/分叉/交叉拒绝面积、大坐标 | 修复后通过 |
| 多层切片与 JSON | X/Y/Z 多层、模型外空层、无效坐标、示例导出与解析检查 | 通过 |
| 生命周期与并发 | 重复 close、关闭后访问、1,000 次创建/查询/释放、同模型及双模型并发 | 通过 |
| C 接口错误边界 | 缓冲区不足、空输出、创建失败清空句柄、错误文本 | 通过 |
| 三维显示 | 实际 Mesh.show、变换后再次显示、自动取景、真实帧截图 | 通过，详见显示范围 |

## 发现的问题与处理

### 1 大坐标截面面积丢失

单位立方体平移至 X=10⁹、Y=10⁹ 后，以远离模型的平面原点求截面，原实现返回面积 0，正确值应为 1。原因是面积公式中的大数相减损失精度。已在每条轮廓内采用局部参考点计算面积；对应回归测试现返回 1，周长返回 4。

### 2 导出失败破坏目标文件

坐标超出 STL float32 范围时，原实现先打开目标文件，后续写入异常会覆盖已有文件或留下不完整新文件。已增加范围检查，并采用同目录临时文件写完后原子替换的方式。测试分别确认既有文件内容不变，以及新路径不留下残缺文件。

### 3 NumPy 混用后的 ASCII 解析异常

在扩展测试的特定顺序中，NumPy 结果测试之后读取合法 ASCII STL 失败；诊断显示首个关键字 solid 被流式分词为 so。原有 51 项单独运行未暴露该问题。已改为显式 ASCII 空白分词与独立 C 数字区域设置解析，避免依赖进程的字符分类状态。相同 67 项顺序重新运行全部通过。该异常是在本次 Windows/Zig 工具链上复现的，不据此推断其他平台也必然存在相同故障。

### 4 重复显示的稳定性与取景

显示过程中有一次中间运行出现 WGL 上下文与 swap interval 告警，截图仍生成；另发现变换后沿用旧相机可能使模型偏出画面。现避免对已初始化的 Polyscope 重复调用 init，并在注册网格后自动取景。最后一次完整显示运行没有这些告警，两张最终截图已查看，模型均正常渲染。不能由此保证所有显卡驱动均无问题。

最初新增测试中另有一处测试脚本自身的 ctypes 指针类型写法错误，已修正，不计为产品缺陷。修复前日志保留了该过程，没有将失败记录删除或改成通过。

## 真实模型与性能观察

全部 5 个模型完成读取、保存往返、质量属性和 10,000 个最近点查询。以下面积为包围盒中心 Z 平面的截面结果，单位随模型坐标；质量属性采用单位密度。没有据此验证原始模型自交或材料参数的物理正确性。

| 模型 | 顶点 | 三角形 | 中间截面 | 10,000 点无符号查询 |
|---|---:|---:|---|---:|
'''
for m in models['models']:
    sec=m['mid_z_section']
    area=f"面积 {sec['area']:.6g}" if 'area' in sec else '两条轮廓相交，拒绝面积计算'
    text+=f"| {m['file']} | {m['counts'][0]:,} | {m['counts'][1]:,} | {area} | {m['nearest_10000_seconds']:.4f} s |\n"
text+='''
Cow 的截面面积报错是预期的输入几何诊断，不是本次测试失败。报告仍保留其轮廓；质量和体积结果属于基于输入面的代数计算，不能当作模型已通过实体合法性认证。

上述时间是本机单次、空间索引已建立后的观察，包含 Python 参数整理及结果转换。带符号距离和截面面积采用不同计算流程，不能套用该性能数字；没有与原 Visual Studio 程序进行速度比较。

## 显示实测

使用真实 Cow 网格（2,903 顶点、5,804 三角形）调用现有 Mesh.show。测试只将交互等待限定为 8 帧，渲染、网格注册与截图均为真实执行，没有使用 mock 图形后端。第一张为初始模型，第二张为 Z 轴旋转后再次显示。两次均生成 960×720 图像并经查看确认。

![初次显示](display-1.png)

![旋转后再次显示](display-2.png)

本次没有自动化拖动鼠标、滚轮缩放、所有菜单操作，也没有测试远程桌面、无显示服务器或其他显卡。最终显示日志见 display.log，结构化结果见 display.json。

## 跨平台与免安装包检查

| 目标 | 编译及静态检查 | 运行状态 |
|---|---|---|
| Windows x64 | 清理后重编译；PE 架构、完整 C 接口导出、依赖检查通过 | 源码环境 67/67；解压标准库环境 65 通过、2 跳过；显示通过 |
| Linux x64 | 重新交叉编译；ELF 架构、完整 C 接口导出、依赖检查通过 | 未实机运行 |
| macOS Apple Silicon | 重新交叉编译；Mach-O 架构、完整 C 接口导出、依赖检查通过 | 未实机运行 |
| macOS Intel | 重新交叉编译；Mach-O 架构、完整 C 接口导出、依赖检查通过 | 未实机运行 |

解压测试的两项跳过是原始模型测试（交付包不携带课程模型）和可选 NumPy 测试（使用 Python -S 禁用第三方包）。它们在源码环境中均已运行通过。独立 demo 和制造分析示例均退出成功，导出的单位立方体质量为 1，三层截面面积均为 1。

Windows 仍依赖系统 UCRT；Linux 仍依赖系统 glibc；macOS 仍依赖系统 libSystem。免安装指运行时无需配置 C++ 开发环境，不是无操作系统依赖。原生构建用 Zig/Clang，本次没有另用 MSVC 或 GCC 重编译。未启用 ASan/Valgrind，1,000 次生命周期循环通过不等同于严格的无内存泄漏证明。

## 证据与复现

| 文件 | 内容 |
|---|---|
| baseline.json / baseline.log | 原有 51 项基线运行 |
| extended-before-fixes.json / .log | 新增测试首次运行，含测试脚本指针错误 |
| extended-confirmed.json / .log | 修正测试脚本后，仍存在 3 个失败用例与 1 个 ASCII 错误 |
| diagnostic.json / .log | ASCII 分词错误定位记录 |
| final-suite.json / final-suite.log | 最终 67 项结果、每项耗时、动态库 SHA256 |
| build-windows.log / ctest.log | 清理重建及 CTest 日志 |
| real-models.json | 5 个真实模型的数值、诊断和计时 |
| display.json / display.log / display-*.png | 最终真实渲染结果与截图 |
| packages.json | 四个二进制导出与依赖、压缩包及源码哈希、解压运行日志 |

源码目录配置 PYTHONPATH 指向 python、MESH_CORE_LIBRARY 指向对应动态库后，可以使用以下命令重复核心测试：

```text
python -m unittest discover -s tests -v
```

已提供 tools/run_test_suite.py、tools/test_display.py、tools/validate_geometry.py 和 tools/audit_packages.py 保留或重现测试证据。显示测试需要 NumPy/Polyscope；包审计脚本需要 pefile、pyelftools、macholib，这些仅是测试工具依赖，不属于计算库必需依赖。

## 剩余限制

目前可以用于已覆盖条件下的网格分析和算法实验。Linux/macOS 实机执行、完整交互测试、跨 Python 版本验证、长时间内存检测，以及更大规模网格性能仍未完成。几何内核使用浮点运算，尚无完整自交修复和实体合法性认证；连续碰撞、制造刀路与物理仿真不在当前功能范围。

## 附录 逐项测试结果

下表来自 final-suite.json。图形和解压包检查单独记录，不重复计入 67 项。

| 测试用例 | 状态 | 耗时 ms |
|---|---|---:|
'''
for c in suite['cases']:
    text+=f"| `{c['id']}` | {'通过' if c['status']=='passed' else c['status']} | {c['seconds']*1000:.2f} |\n"
(out/'测试报告.md').write_text(text,encoding='utf-8')
body=markdown.markdown(text,extensions=['tables','fenced_code'])
for filename in ('display-1.png','display-2.png'):
    data=base64.b64encode((out/filename).read_bytes()).decode()
    body=body.replace(f'src="{filename}"',f'src="data:image/png;base64,{data}"')
style='''body{font-family:"Microsoft YaHei",system-ui,sans-serif;color:#17212c;background:#fff;margin:36px auto;max-width:1100px;padding:0 28px;line-height:1.8}h1{font-size:30px}h2{margin-top:34px;font-size:23px;border-bottom:1px solid #ddd;padding-bottom:8px}h3{font-size:19px}table{border-collapse:collapse;width:100%;font-size:14px;margin:18px 0}th,td{border:1px solid #d4dce3;padding:9px 12px;text-align:left;overflow-wrap:anywhere}th{background:#eef3f6}tr:nth-child(even){background:#fafbfc}code{font-family:Consolas,monospace;font-size:.88em}pre{background:#f2f5f7;padding:16px;overflow:auto}img{display:block;max-width:100%;height:auto;margin:20px auto}a{color:#1766a4}@media print{body{margin:0;font-size:10pt}h2,h3{break-after:avoid}tr,img{break-inside:avoid}thead{display:table-header-group}pre{white-space:pre-wrap}}'''
(out/'测试报告.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>MeshTestbed Portable 全功能测试报告</title><style>'+style+'</style><body>'+body+'</body></html>',encoding='utf-8')
print('Generated 测试报告.md and standalone 测试报告.html')
