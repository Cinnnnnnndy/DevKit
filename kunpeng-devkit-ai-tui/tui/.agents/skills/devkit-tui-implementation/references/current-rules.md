# DevKit TUI 实现检查表

更新日期：2026-08-13

本文件只汇总实现仓库的执行检查项，不是 UI 规范回退。任何页面、视觉、交互、组件状态或终端降级要求，都以实时读取的正式 UI 交付为准。

## 正式输入

- 实现仓库规则：根 `AGENTS.md`
- 全局 UI 规范：同级 `DevKit/kunpeng-devkit-ai-tui/UI-SPEC.md`
- 页面合同：同级 `DevKit/kunpeng-devkit-ai-tui/pages/<page-id>.md`
- 稳定工程边界：[formal-project.md](formal-project.md)

UI 仓库根 `AGENTS.md`、`docs/`、`web/`、普通 `assets/` 和本 Skill references 都不是正式 UI 规则来源。页面明确引用的参考材料只作辅助，不能复制到实现仓库或补充合同缺失项。

## UI 交付门禁

- [ ] 已明确稳定 `page-id`。
- [ ] 全局规范存在且为 `approved`。
- [ ] 页面文件存在且为 `approved`。
- [ ] 页面 `ui-spec-version` 与全局版本完全相等。
- [ ] 所有规则 ID 和组件 ID 均可解析。
- [ ] 所有 `EXC-*` 均在全局例外表中批准并被页面引用。
- [ ] 布局、数据、状态、焦点、键鼠、降级和验收无待猜测项。

任一项失败时停止 UI 实施并报告缺口。不得用历史实现、分散研究文档或本文件推断设计。与 UI 无关的工程工作可以继续。

## 规则边界

- 实现仓库 `AGENTS.md`：代码、架构、构建、测试、发布。
- `UI-SPEC.md`：跨页面 UI。
- 页面文件：页面局部 UI，不得覆盖全局规则。
- 技术约束与正式 UI 交付冲突：列证据并等待裁决，不静默覆盖。
- 未经明确授权，不修改 UI 仓库。

## 确定技术栈

- TypeScript 5.9.3
- React 19.2.0
- `@opentui/core` 0.5.1
- `@opentui/react` 0.5.1
- Bun 1.3.14

依赖使用精确版本并提交 `bun.lock`。产品保持原生 TUI，不引入 HTTP Server、Service 或 IDE 宿主运行方式。

## 实施映射

- [ ] 变更记录包含 `page-id`、`ui-spec-version`、规则/组件/例外 ID。
- [ ] 全局 UI 规则进入共享 theme、基础组件、交互原语或能力探测。
- [ ] 页面数据、状态和操作进入 feature、typed props、状态模型与测试。
- [ ] 页面验收条件逐项映射为自动测试或明确人工验收。
- [ ] 全局版本变化时审计其列出的全部受影响页面和共享组件。
- [ ] 业务页面没有复制 token、焦点规则、键位语义或公共状态实现。

本仓库不保存 UI 设计内容。运行时字符帧只作为实现测试快照保存在 `tests/` 下，并记录对应页面与全局版本。

## 架构与数据

- Domain 保持纯 TypeScript，不依赖 React/OpenTUI。
- Feature 只依赖 typed data port，不直接依赖 adapter。
- 默认 Mock 异步、可取消、确定性并支持场景切换。
- 组件不直接导入 fixture；render 期间禁止随机数。
- 后端联调只新增 Gateway adapter，不改页面和 domain 契约。
- Chrome、Canvas、Data 分层；高密度数据受 viewport 限制。
- CJK、Braille、emoji 使用终端 display width；尺寸、坐标和比例均 clamp。

## 状态与交互

- [ ] 实现页面合同列出的全部同步、异步和恢复状态。
- [ ] 鼠标操作均有键盘等价路径。
- [ ] 返回、中断、确认和焦点恢复符合合同。
- [ ] 语义不能只靠颜色表达。
- [ ] 无法实现的要求已进入冲突裁决，没有静默近似替代。

## 验证

- [ ] `bun run format:check`
- [ ] `bun run lint`
- [ ] `bun run typecheck`
- [ ] 相关单测、集成测试和 OpenTUI render 测试
- [ ] 页面合同全部验收条件
- [ ] 160×50、58×32 和动态 resize
- [ ] TrueColor、ANSI 16、`NO_COLOR`、SSH、纯键盘和字符能力降级
- [ ] loading、empty、error、极值、长 CJK 和超量数据等适用场景
- [ ] 真实字符帧与颜色 span 复验

需要发布时再运行 `bun run release:check`，并按 [formal-project.md](formal-project.md) 检查三平台产物。
