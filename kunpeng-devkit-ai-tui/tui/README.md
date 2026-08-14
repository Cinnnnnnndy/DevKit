# Kunpeng DevKit AI

Kunpeng DevKit AI 是面向开发者、芯片工程师和性能工程师的原生终端工程工作台。
它将 AI Agent、DevKit 工具链和工程可视化组织在同一个全屏 TUI 中，命令为
`devkitai`。

当前阶段使用确定性异步 Mock 数据，不启动 Service，也不访问真实后端。页面通过
`DevKitGateway` 获取数据；后续联调只需替换 adapter。

## 技术栈

- Bun 1.3.14
- TypeScript 5.9.3
- React 19.2.0
- OpenTUI Core / React 0.5.1

## 开发

```bash
bun install --frozen-lockfile
bun run dev
bun run check
```

发布工程命令：

- `bun run package:all`：单机交叉构建 Windows x64、Linux x86_64 和 Linux ARM64
- `bun run verify:packages`：校验归档、manifest、架构、OpenTUI 原生库和 SHA-256
- `bun run release:check`：运行完整质量门禁并构建、校验三平台发布包

具体发布和 Linux 原生验收要求见 `docs/release/README.md`。

常用命令：

- `bun run typecheck`：严格 TypeScript 检查
- `bun run lint`：Biome lint
- `bun run format:check`：格式检查
- `bun run test`：Vitest 全量测试
- `bun run test:unit`：纯 domain/data 单元测试

Mock 场景可通过 `DEVKITAI_MOCK_SCENARIO` 选择：`happy`、`empty`、`error`、
`slow`、`offline` 或 `extreme`，默认是 `happy`。

工程、架构和验证规则见根目录 `AGENTS.md` 与仓库内
`devkit-tui-implementation` Skill。本仓库只保存实现代码和实现验证资产，不保存 UI 设计内容。
UI 的正式规范来自上级 `kunpeng-devkit-ai-tui/`：

- `../UI-SPEC.md`：全局 UI 规范
- `../pages/<page-id>.md`：页面合同

只有状态为 `approved` 且 `ui-spec-version` 完全相等的全局规范和页面合同才可用于正式 UI 实施。`DevKit` 的 `docs/`、`web/` 和普通 `assets/` 不替代正式交付，也不得复制到本仓库作为本地设计资料。
