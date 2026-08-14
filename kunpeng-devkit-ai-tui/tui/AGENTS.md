# Kunpeng DevKit AI TUI 工程规则

## 仓库定位

- 本目录是 Kunpeng DevKit AI TUI 的实现，只负责源码、测试、运行时快照、打包和发布。
- 自 2026-08-14 起，实现与设计**同仓**：设计交付在上级 `kunpeng-devkit-ai-tui/`，本目录不重复保存 UI 规范、页面合同、线框或参考图。
- 修改设计交付（`UI-SPEC.md`、`pages/`）属于跨边界改动，需在变更说明中显式声明。

## 确定的实现技术栈

- TypeScript 5.9.3
- React 19.2.0
- `@opentui/core` 0.5.1
- `@opentui/react` 0.5.1
- Bun 1.3.14 构建、测试和打包

依赖必须使用精确版本并提交 `bun.lock`。产品是原生 TUI，二进制名称为
`devkitai`；不得引入 HTTP Server、Service 进程或依赖 IDE 的运行方式。

## UI 正式交付源

涉及页面、布局、视觉、交互、组件状态或终端降级的工作，必须使用同级 UI 仓库中的正式交付：

```text
../
├── UI-SPEC.md              # 全局 UI 规则的唯一事实源
└── pages/
    └── <page-id>.md        # 当前页面的完整 UI 合同
```

正式 UI 规则的适用关系为：

1. 本仓库 `AGENTS.md` 约束代码、架构、构建、测试和仓库工作流。
2. `UI-SPEC.md` 约束跨页面的视觉、布局、组件、交互和降级语义。
3. `pages/<page-id>.md` 只补充当前页面的局部规则，不能覆盖全局规则。
4. 页面例外只有在 `UI-SPEC.md` 以 `EXC-*` 登记为 `approved`，且被页面文件明确引用时才有效。

UI 仓库根 `AGENTS.md`、`docs/`、`web/`、未被页面引用的 `assets/` 和本仓库
Skill references 均不是 UI 规则的替代来源。页面明确引用的图片或研究材料也只用于辅助理解，
不能复制到本仓库，也不能补充正式交付中缺失的布局、行为、状态、数据或验收条件。

## UI 实施门禁

开始任何 UI 实施前必须：

1. 明确本次变更对应的稳定 `page-id`。
2. 读取 `UI-SPEC.md`，确认 `status: approved` 并记录 `ui-spec-version`。
3. 读取对应的 `pages/<page-id>.md`，确认 `status: approved`。
4. 确认页面 `ui-spec-version` 与全局版本字符串完全相等。
5. 校验页面引用的所有规则 ID、组件 ID 和 `EXC-*` 均存在且有效。
6. 确认布局、数据、状态、焦点、键鼠操作、终端降级和验收条件没有待猜测项。

任一正式文件缺失、仍为 `draft`、版本不相等、页面覆盖全局规则、例外未批准或关键行为未定义时，UI 交付尚未就绪：不得自行读取分散研究文档补全、不得复制旧实现推断新设计、不得静默创造第三套规则。应记录缺口并等待正式交付修正。与 UI 无关的工程工作可以继续。

若正式 UI 交付与本仓库已确定的技术或架构约束发生实质冲突，列出双方规则、证据和影响并请求裁决；不得以任一侧静默覆盖另一侧。

## UI 合同到实现的映射

- 全局 token、焦点、键位、公共状态和降级语义应落到共享 theme、基础组件、交互原语和能力探测中，不得在业务页面复制。
- 页面结构、数据合同、状态矩阵和操作表应落到对应 feature、typed props、状态模型与测试。
- 页面合同中的验收条件必须逐项映射为自动测试或明确的人工运行验收；不能只断言组件挂载成功。
- UI 改动必须在测试或变更说明中记录 `page-id`、`ui-spec-version`、使用的规则/例外 ID，以及未自动化的验收项。
- 全局规范版本变化时，按其“受影响页面”清单审计共享组件和已实现页面；不能只修改当前页面。

运行时字符帧属于实现测试资产，只能保存在 `tests/` 下，并应能追溯到对应
`page-id` 与 `ui-spec-version`。不得创建 `design/` 或其他本地设计交付目录。

## 实现要求

所有 UI 工作必须使用仓库内 `.agents/skills/devkit-tui-implementation/`，并同时确认：

1. Intent → Analyze → Execute → Verify 的产品闭环是否成立。
2. React + OpenTUI 0.5.1 是否能真实实现。
3. 内容属于全局基础能力、通用组件还是当前业务页面。
4. 160×50、58×32、SSH、ANSI 16 色、`NO_COLOR` 和低能力终端是否可用。

所有鼠标交互必须提供键盘等价路径。组件需要覆盖 loading、empty、loaded、failed、
disabled 和 error 等适用状态。禁止在 render 期间使用 `Math.random()`。

## 架构边界

- `src/domain/` 只包含纯 TypeScript 业务模型和端口使用的契约，不依赖 React/OpenTUI。
- `src/data/ports/` 定义前端数据端口；功能层只能依赖端口，不直接依赖 adapter。
- `src/data/adapters/mock/` 是当前默认的异步实现；Mock 必须确定、可取消、可切换场景。
- `src/data/fixtures/` 不得由组件直接引用。
- `src/components/charts/` 是独立复制边界，只能依赖 React、OpenTUI 和目录内部文件。
- 真实后端联调通过新增 Gateway adapter 完成，不改变页面和 domain 契约。

## 工程质量

- TypeScript 必须保持 strict，并开启 `noUncheckedIndexedAccess`、
  `exactOptionalPropertyTypes`、`noImplicitOverride`、`useUnknownInCatchVariables`。
- 提交前运行格式检查、lint、typecheck、单元测试、OpenTUI 运行时测试和相关打包检查。
- UI 变更至少验证 160×50、58×32、动态 resize、纯键盘、ANSI 16 色与 `NO_COLOR`；按页面合同补充其他验收。
- 异步边界统一接受 `AbortSignal`，失败统一使用 typed `AppError`，不得吞掉异常。
- 不得提交密钥、真实凭据、构建产物、测试覆盖率目录或临时文件。
