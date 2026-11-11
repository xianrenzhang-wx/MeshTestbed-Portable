# GitHub Actions 跨平台测试报告

日期：2026-11-11。版本：2.1.0。

测试提交：`0525fb168bd513c37c41b200b8d6dceca98231d1`。

[完整 Actions 运行记录及下载产物](https://github.com/xianrenzhang-wx/MeshTestbed-Portable/actions/runs/42992820689)

| 平台 | 编译器 | Python | 结果 |
|---|---|---|---|
| Windows x86_64 | MSVC 19.51 | 3.11.9 | 82/82 通过，0 跳过 |
| Ubuntu 22.04 x86_64 | GCC 11.4 | 3.11.18 | 82/82 通过，0 跳过 |
| macOS 15 Apple Silicon | AppleClang 17 | 3.11.9 | 82/82 通过，0 跳过 |
| macOS 15 Intel | AppleClang 17 | 3.11.9 | 82/82 通过，0 跳过 |

每个任务完成 CMake 原生构建、CTest、安装包中的三个示例、安装后完整测试和 JSON/日志记录。NumPy 2.3.5 用于可选数组接口测试，五个 STL 测试模型随仓库提供。

这次验证覆盖计算接口，未运行交互式 OpenGL 窗口。验证对象是 Actions 本机编译的产物，不代表此前 Zig 交叉编译包已在目标机器运行，也不证明兼容所有系统版本。

## 下载

打开上方运行页面，在 Artifacts 中下载：

- mesh-testbed-windows-x86_64
- mesh-testbed-linux-x86_64
- mesh-testbed-macos-arm64
- mesh-testbed-macos-x86_64
- 对应的 test-results-* 包：包含 suite.json、suite.log 和 CTest 日志。

下载包内有动态库、Python 接口、示例、测试及 API 文档。产物有 GitHub 保留期限；此次到期时间为 2027-02-09。过期后可重新运行工作流生成。

## 日志中的结果摘要

### build (windows-latest, windows-x86_64)

[任务日志](https://github.com/xianrenzhang-wx/MeshTestbed-Portable/actions/runs/42992820689/job/130429567947)

```text
2026-11-11T09:09:53.7276684Z Successfully set up CPython (3.11.9)
2026-11-11T09:10:20.1160209Z -- The CXX compiler identification is MSVC 19.51.36260.0
2026-11-11T09:10:34.9851190Z Ran 82 tests in 0.725s
2026-11-11T09:10:35.9516950Z {'tests': 82, 'successful': True, 'failures': 0, 'errors': 0, 'skipped': 0, 'seconds': 0.7374708000000112}
```

### build (macos-15-intel, macos-x86_64)

[任务日志](https://github.com/xianrenzhang-wx/MeshTestbed-Portable/actions/runs/42992820689/job/130429568151)

```text
2026-11-11T09:09:54.5723590Z Successfully set up CPython (3.11.9)
2026-11-11T09:10:04.2922310Z -- The CXX compiler identification is AppleClang 17.0.0.17000013
2026-11-11T09:10:19.8939610Z Ran 82 tests in 1.905s
2026-11-11T09:10:21.7781450Z {'tests': 82, 'successful': True, 'failures': 0, 'errors': 0, 'skipped': 0, 'seconds': 1.6306620029999976}
```

### build (macos-15, macos-arm64)

[任务日志](https://github.com/xianrenzhang-wx/MeshTestbed-Portable/actions/runs/42992820689/job/130429568278)

```text
2026-11-11T09:09:51.6585830Z Successfully set up CPython (3.11.9)
2026-11-11T09:09:58.6976840Z -- The CXX compiler identification is AppleClang 17.0.0.17000013
2026-11-11T09:10:06.7954140Z Ran 82 tests in 0.897s
2026-11-11T09:10:08.1174330Z {'tests': 82, 'successful': True, 'failures': 0, 'errors': 0, 'skipped': 0, 'seconds': 1.116112292000011}
```

### build (ubuntu-22.04, linux-x86_64)

[任务日志](https://github.com/xianrenzhang-wx/MeshTestbed-Portable/actions/runs/42992820689/job/130429568424)

```text
2026-11-11T09:09:50.4372251Z Successfully set up CPython (3.11.18)
2026-11-11T09:09:58.8589284Z -- The CXX compiler identification is GNU 11.4.0
2026-11-11T09:10:04.2608146Z Ran 82 tests in 0.846s
2026-11-11T09:10:05.0073046Z {'tests': 82, 'successful': True, 'failures': 0, 'errors': 0, 'skipped': 0, 'seconds': 0.6588165769999961}
```


原 reports/release-2.1.0/TEST_REPORT.md 是本地测试的历史快照；其中“Linux/macOS 未原生执行”的状态已由本报告补充更新。

