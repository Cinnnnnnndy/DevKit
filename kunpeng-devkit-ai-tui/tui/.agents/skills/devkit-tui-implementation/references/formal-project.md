# Kunpeng DevKit AI 实现仓库稳定规则

更新日期：2026-08-13

本文件只保存不应随页面设计变化的工程边界。视觉 token、布局、交互、组件状态和终端降级规则不得复制到这里，应实时读取正式 UI 交付。

## 仓库职责

- 只保存产品源码、测试、运行时快照、打包和发布配置。
- 不保存或维护全局 UI 规范、页面合同、线框、参考图或其他设计产物。
- 运行时字符帧只作为实现测试快照保存在 `tests/` 下。
- UI 仓库默认只读；未经明确授权不反向修改。

## 技术栈

- TypeScript 5.9.3
- React 19.2.0
- `@opentui/core` 0.5.1
- `@opentui/react` 0.5.1
- Bun 1.3.14

版本由 `package.json` 和 `bun.lock` 锁定。应用是独立原生 TUI，命令为 `devkitai`。

## 代码边界

- `src/domain/`：纯 TypeScript 模型与用例契约，不依赖 React/OpenTUI。
- `src/data/ports/`：功能层依赖的数据端口。
- `src/data/adapters/mock/`：默认异步 Mock，实现确定性、取消和场景切换。
- `src/data/fixtures/`：只允许 adapter 或专用演示 feature 引用。
- `src/components/charts/`：可独立复制，只依赖 React、OpenTUI 和目录内部文件。
- 后端接入通过新增 Gateway adapter 完成，不改变页面与 domain 契约。

异步边界接受 `AbortSignal`；失败使用 typed `AppError`；不得吞异常。render 期间禁止 `Math.random()`。

## 质量门禁

- TypeScript strict，并保持 `noUncheckedIndexedAccess`、`exactOptionalPropertyTypes`、`noImplicitOverride`、`useUnknownInCatchVariables`。
- 提交前运行 format check、lint、typecheck、相关单元/集成/render 测试和 Bun 构建。
- UI 验收必须来自已批准、版本匹配的全局规范与页面合同。
- 视觉验证捕获真实 OpenTUI 字符帧和颜色 span；组件挂载成功不能替代视觉复验。
- 不提交密钥、真实凭据、构建产物、覆盖率目录或临时文件。

## 打包发布

- 使用 Bun 单机交叉构建 Windows x64、Linux x86_64 baseline、Linux ARM64。
- 每个目标使用隔离 staging 安装对应 OpenTUI 原生包，不复用宿主平台 `node_modules` 判断目标依赖。
- 发布包包含单可执行文件、README、NOTICE、版本/commit/target manifest；根目录生成 `SHA256SUMS`。
- Windows 产物执行本机 smoke；Linux 包在 Windows 上检查 PE/ELF、架构与内嵌依赖。
- 未在 Linux 目标机执行 native smoke 时必须明确标记，不能声称已验证。
- 版本只取根 `package.json`；文件名包含产品、版本和目标三元组。
