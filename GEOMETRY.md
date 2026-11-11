# 网格几何与制造分析（v2）

这一版提供三角网格的几何分析基础，不是完整 CAD 几何内核、CAE 求解器或 CAM 刀路系统。所有原生算法为标准 C++17 实现，没有新增必须安装的计算库。Python 基础接口仍只依赖标准库。

## 功能与示例

```python
from mesh_testbed import Mesh

with Mesh("part.stl") as part:
    # 均匀密度实体：体积、质量、质心、质心处惯性张量。
    props = part.mass_properties(density=1.0)
    print(props["centroid"], props["inertia"])

    # 一次传入一批点。输出距离、最近表面坐标、原网格三角形编号。
    result = part.nearest_points([(0, 0, 0), (1, 2, 3)])
    signed = part.nearest_points([(0, 0, 0)], signed=True)
    state = part.classify_points([(0, 0, 0)])  # -1 内部、0 边界、1 外部

    sec = part.section(origin=(0, 0, 0.5), normal=(0, 0, 1))
    print(sec.polylines, sec.closed, sec.perimeter)
    print(sec.area)  # 非闭合/分叉/交叉轮廓会报错

    for layer in part.slices([0.1, 0.2, 0.3], axis="z"):
        print(layer.origin, layer.polylines)

with Mesh("part.stl") as part, Mesh("fixture.stl") as fixture:
    print(part.distance_to(fixture))
    print(part.collision(fixture))
```

`python manufacturing_demo.py part.stl --layers 10 --output analysis.json` 会导出质量属性、查询点结果和每一层的 3D 轮廓。省略模型文件时使用单位立方体。运行包解压后即可使用，无需安装 NumPy。

| 接口 | 返回 / 含义 | 条件 |
|---|---|---|
| `mass_properties(density)` | `volume`、`mass`、`centroid`、`inertia` | 闭合、有向、无退化面；均匀正密度 |
| `nearest_points(points)` | `distances`、`points`、`face_ids` | 可用开放网格，退化三角形按线/点处理 |
| `nearest_points(points, signed=True)` | 内负外正，容差内为零 | 闭合有向网格 |
| `classify_points(points)` | 每点 -1 / 0 / 1 | 闭合有向网格 |
| `contains(points)` | 每点布尔值，默认包含边界 | 可用 `include_boundary=False` |
| `distance_to(other)` | 最小表面距离、对应面编号 | 两个网格都没有退化面 |
| `collision(other)` | `collides`、`kind`、`face_ids` | 默认视为实体，包含也计为碰撞 |
| `collision(other, solid=False)` | 仅判断表面相交或接触 | 支持开放网格 |
| `section(origin, normal)` | `Section` 对象 | 任意非零法向，支持开放网格；拒绝退化面 |
| `slices(heights, axis)` | 按指定绝对坐标逐层生成 Section | axis 为 x/y/z；不同时保留所有层 |

`nearest_points(..., numpy=True)` 返回 NumPy 数组，结果与原模型内存独立。`Section` 也不依赖模型生命周期，关闭模型后可以继续分析轮廓。

## 质量、惯性与单位

STL 不包含单位。本库不猜测 mm 或 m。密度必须采用与你的长度一致的单位：如果坐标使用 m、密度使用 kg/m³，则质量是 kg，惯性是 kg·m²。坐标使用 mm 时应先转换密度或统一缩放到 m。

惯性是质心处、沿当前世界坐标轴的 3×3 张量：对角线为 Ixx/Iyy/Izz，非对角线采用负积惯量约定。整体反转全部面方向不影响正质量；嵌套空腔必须与外壳相反定向，分离实体必须采用一致的实体定向。

实现用带符号四面体积分计算零阶、一阶、二阶体积矩，并采用局部参考点减少大平移下的消减误差。它可以向后续刚体、惯性载荷或优化程序提供输入，但没有材料力学或有限元求解。

## 距离与碰撞的区别

* 距离指**表面到表面**的距离。如果一个小实体完全位于另一个实体内，表面距离可能为正，但实体碰撞为真。
* 实体碰撞的 `kind` 为 `separated`、`surface_contact` 或 `containment`。`surface_contact` 同时包含相切和表面相交，不计算穿透深度。
* `face_ids` 对应当前网格面数组的位置，不是持久化 CAD 面标识；包含情况没有接触面，返回 `None`。
* `tolerance` 默认 `1e-9`，单位与模型长度相同。碰撞中的容差扩展分离轴投影区间，**不是**各方向都严格等价的欧氏安全间隙。要判断净间隙，使用 `distance_to`，并另行检查实体包含。
* 不提供连续运动碰撞、扫掠体、接触力或刀具补偿；离散姿态检查不能证明整段运动无碰撞。

最近点与网格对查询使用缓存的 AABB/BVH 空间索引，旋转/缩放/平移后自动失效并在下一次查询时重建。三角形距离求解考虑面内部、边和顶点；网格距离同时考虑边边最近点。碰撞采用三角形分离轴测试，包含共面情况。

带符号距离及实体包含用完整的三角形立体角求和，不是快速近似绕数算法；大量内部查询时仍为每点 O(三角形数)。没有宣称百万网格的所有操作都是实时的。

## 截面与切片

* 平面用 `origin`、`normal` 定义，法向自动归一化。
* `segments` 是原生计算的线段；`polylines` 是端点按容差连接、重复边去除后的折线。闭合折线重复首点作为末点。
* 平面与整个面共面时，输出共面区域边界，去掉内部剖分对角线；单点相切不输出线段。沿边相切可以形成开放线段。
* 截面可用于模型检查和切片前处理，不是已经带刀具半径补偿、进退刀、安全高度的加工刀路。
* `Section.area` 按轮廓嵌套的奇偶规则计算面积，支持孔洞。要求轮廓简单且闭合；开放、分叉、交叉、接触或端点合并导致坍缩的轮廓会报错。`perimeter` 对开放折线也会返回长度。
* 原始网格可能自交；不能因为边拓扑闭合就认为实体有效。示例 Cow 的包围盒中心 Z 截面有两条相交轮廓，本版保留轮廓并拒绝给出“实体截面面积”。
* 轮廓拼接和面积分析在 Python 中进行；轮廓交叉检查目前最坏 O(线段数²)。原生平面相交通过 BVH 剪枝。批量切片使用生成器，避免一次存放全部切片。

## 精度与支持范围

本版使用浮点几何，不采用任意精度/精确谓词。坐标应合理缩放，并按模型单位选择容差；容差过大会合并细小特征。当前只检查必要的闭合边和退化面条件，没有完整的自交、顶点流形、壳层方向和实体合法性修复功能。分析前需确保模型代表有效实体；不能把拓扑检查通过理解为制造可用性认证。

STEP/IGES/BREP、曲面曲线布尔运算、体网格生成、有限元、三轴/五轴刀路与 G-code 均未在这批网格模块中实现。后续应在确认需求后选用相应专业内核，不把它们伪装成简单网格函数。

## 数学参考

本实现是独立编写的，以下资料用于核对算法原理，没有引入对应库作为运行依赖：

* David Eberly：[点到三角形距离](https://www.geometrictools.com/Documentation/DistancePoint3Triangle3.pdf)。
* David Eberly：[多面体质量属性](https://www.geometrictools.com/Documentation/PolyhedralMassProperties.pdf)。
* David Eberly：[分离轴方法](https://www.geometrictools.com/Documentation/MethodOfSeparatingAxes.pdf)。
* CGAL：[网格截面接口与共面边约定](https://doc.cgal.org/latest/PMP_Boolean_operations/classCGAL_1_1Polygon__mesh__slicer.html)。
