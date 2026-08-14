---
name: devkit-tui-implementation
description: 根据相邻 DevKit UI 仓库中已批准且版本匹配的 UI-SPEC.md 与页面合同，实现、重构或评审 Kunpeng DevKit AI 的 React + OpenTUI 界面。用于页面、Shell、基础组件、统计图表、主题 token、状态、键鼠交互、宽窄屏适配、SSH/低能力终端降级、运行时字符帧和 UI 验收工作。
---

# DevKit TUI 实现与验收

把当前仓库视为纯实现现场，把相邻 `DevKit` 仓库的正式 UI 交付视为 UI 事实源。本仓库不得保存 UI 规范、页面合同、线框、参考图或其他设计产物。

## 建立上下文

1. 从当前文件向上定位实现仓库根目录，完整读取所有适用的 `AGENTS.md`。
2. 读取 [references/current-rules.md](references/current-rules.md) 作为执行检查表，读取 [references/formal-project.md](references/formal-project.md) 获取稳定工程边界；两者均不能替代实时 UI 交付。
3. 在实现仓库同级目录查找 `DevKit/kunpeng-devkit-ai-tui/UI-SPEC.md`；找不到时使用用户明确提供的 UI 仓库位置。不得写死个人盘符、用户名或机器专属路径。
4. UI 任务先从需求确定稳定 `page-id`。读取 `UI-SPEC.md`，再读取对应 `pages/<page-id>.md`；共享能力变更还要读取全局规范列出的所有受影响页面。
5. 只在页面文件明确引用时查看 UI 仓库中的图片或研究材料，把它们视为非规范性辅助信息，不复制到实现仓库。
6. 检查已有 theme、基础组件、状态模型、Gateway、运行时帧和测试，优先复用，禁止在业务页面复制基础能力。

## UI 交付门禁

开始 UI 实施前同时满足：

- `UI-SPEC.md` 存在且 `status: approved`。
- 目标页面文件存在且 `status: approved`。
- 页面 `ui-spec-version` 与全局版本字符串完全相等。
- 页面引用的规则 ID、组件 ID 均存在。
- 页面引用的每个 `EXC-*` 已在全局例外表中批准。
- 页面合同已经定义布局、数据、状态、焦点、键鼠操作、终端降级和可验证验收条件。

任一条件不满足时，不读取 `docs/`、`web/`、历史实现或本 Skill references 来猜测缺失设计。报告确切缺口并停止 UI 实施；与 UI 无关的工程工作仍可继续。

## 规则边界与冲突

- 用户本次明确要求优先。
- 实现仓库 `AGENTS.md` 约束代码、架构、构建、测试和仓库工作流。
- 已批准的 `UI-SPEC.md` 约束全局 UI。
- 已批准的目标页面文件补充页面局部 UI，但不能覆盖全局规则。
- UI 仓库根 `AGENTS.md`、`docs/`、`web/` 和本 Skill references 不参与正式 UI 规则裁决。

实现约束与正式 UI 交付发生实质冲突时，列出双方规则、证据、影响范围和可选处理，等待人工裁决；不要静默覆盖或创造第三套规则。除非用户明确要求，不修改 UI 仓库。

固定使用 TypeScript 5.9、React 19、`@opentui/core` 0.5.1、`@opentui/react` 0.5.1 与 Bun。正式交付若出现 Textual、TCSS、Web-only 或当前 OpenTUI 无法兑现的要求，按冲突流程处理，不自行翻译成未经批准的替代设计。

## 实施工作流

### 1. 建立可追溯映射

- 记录 `page-id`、`ui-spec-version`、使用的规则 ID、组件 ID 和例外 ID。
- 把全局 token、焦点、键位、公共状态和降级语义映射到共享 theme、组件和交互原语。
- 把页面区域、数据合同、状态矩阵、操作表和验收条件映射到 feature、typed props、状态模型与测试。
- 全局规范版本变化时，根据其受影响页面清单审计共享组件和所有相关页面。

不要在实现仓库创建或保存任何 UI 设计产物。运行时字符帧只作为测试快照保存在 `tests/` 下，并必须能追溯到正式页面和全局版本。

### 2. 按 Chrome / Canvas / Data 分层

- Chrome 放导航、选择、切换和确认，使用真实 OpenTUI 组件与完整焦点态。
- Canvas 放曲线、热力、Trace、Gauge、Diff、日志和代码，使用受 viewport 限制的字符网格或缓冲原语。
- Data 通过 typed Gateway port 输入；默认 Mock adapter 异步、可取消、确定性。组件不得直接导入 fixture，render 期间禁止 `Math.random()`。
- 不启动 Service，不让 UI 依赖 HTTP。后端联调只新增实现同一 Gateway 的 adapter。
- 使用终端 display width 处理 CJK、Braille、emoji 和截断；所有尺寸、坐标和比例结果必须 clamp。

### 3. 完整兑现合同

- 实现合同中所有适用的 `default / focused / selected / disabled / loading / loaded / empty / error / failed / cancelled` 状态。
- 每个 click、hover、wheel、drag 都提供键盘等价；保留合同规定的返回、中断和高风险确认语义。
- 颜色、边框、间距、字符和组件变体只能来自全局规范定义的语义规则；业务页面不得发明裸样式。
- 无法实现的合同项必须回到冲突流程，不能用“接近效果”静默替代。

### 4. 验证真实终端输出

至少验证：

- format check、lint、typecheck、相关单测、集成测试、OpenTUI render 测试与 Bun 构建。
- 页面合同中的每一条验收条件，并记录自动化或人工验收方式。
- 160×50、58×32 和动态 resize；不出现越界、负尺寸或 CJK 半字符截断。
- 合同要求的 loading、empty、error、极值、长标签和超量数据场景。
- TrueColor、ANSI 16、`NO_COLOR`、Braille/Unicode 缺失、SSH 与纯键盘路径。
- 视觉改动捕获真实 OpenTUI 字符帧和颜色 span，并对照正式字符帧；组件挂载成功不能替代视觉复验。

在测试或变更说明中记录 `page-id`、`ui-spec-version`、规则/例外 ID、测试结果和未自动化验收项。

## 更新本 Skill

交付路由或工程规则变化时：

1. 重新读取实现仓库 `AGENTS.md` 和 UI 仓库正式交付。
2. 更新对应 reference；不要把全局 UI token 或页面细节复制进 reference。
3. 只有触发范围、工作流或文档路由变化时才改 `SKILL.md`。
4. 名称、description 或默认提示变化时，重新生成 `agents/openai.yaml`。
5. 运行 Skill Creator 的 `quick_validate.py`，再用一个不携带预期答案的真实任务做前向验证。
