# Kunpeng DevKit AI TUI

本归档包含原生 `devkitai` 终端应用。

## 使用方式

- Windows x64：打开 PowerShell，运行 `.\devkitai.exe --help`。
- Linux x86_64 或 ARM64：解压归档后运行 `./devkitai --help`。归档已将 `devkitai`
  记录为 0755 权限，通常不需要手动执行 `chmod`。
- 在至少为 58×32 单元格的终端中运行 `devkitai` 启动 TUI，推荐使用 160×50 的终端。

当前版本使用确定性的本地 Mock 数据，不启动或连接 Service。可以通过
`DEVKITAI_MOCK_SCENARIO=happy|empty|error|slow|offline|extreme` 选择数据场景；设置
`NO_COLOR=1` 可启用无颜色降级模式。

`manifest.json` 记录精确的目标平台和工具链。`licenses/index.json` 列出所有已安装的生产依赖，
完整的许可证和声明文件位于 `licenses/` 下。使用 Windows 构建的 Linux 归档，在目标 Linux
环境执行原生 smoke 命令之前，状态保持为 `native-runtime-unverified`。
