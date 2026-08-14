---
document-type: global-ui-spec
status: draft
ui-spec-version: 0.2.0
updated-at: 2026-08-14
applies-to: Kunpeng DevKit AI native TUI
---

# Kunpeng DevKit AI 全局 UI 规范

> 本文件是供后续实现使用的全局 UI 契约。当前状态为 `draft`：规则已从**已运行的实现**中反向固化，但尚未经过人工复审，不属于已生效的正式规范。

## 本版来源与方法

0.1.0 是一份只有章节骨架、正文全是「待汇总」的占位交付。0.2.0 换了一条路子：**不从研究文档里挑结论，而是从已经跑通的实现里反向固化**。

依据是 `tui/`（React 19 + `@opentui/core` 0.5.1，十幕业务闭环可运行，77 个测试通过）。每条规则都对应实现里一个**可被测试断言的位置**，并在规则后用 `→` 标注来源文件。这样做的代价和收益都要写清楚：

- **收益**——规则不会写出实现不了的东西，因为它们本来就是实现里跑着的；每条都能直接转成测试。
- **代价**——实现没覆盖到的地方，规范也就是空的。这些缺口在 §12 集中列出，**不要当成「已批准的省略」**，它们只是还没做。

`docs/` 与 `web/` 仍是研究与评审材料，不因为本版而升格为契约；两者冲突时以本文件为准，并回头修正 `docs/`。

## 使用与版本规则

- `status: approved` 后，本文件才是跨页面 UI 规则的唯一事实源。
- `pages/<page-id>.md` 只能补充页面局部设计，不能覆盖本文件。
- 每项稳定规则使用可引用 ID：`VIS-*`、`LAYOUT-*`、`COMP-*`、`STATE-*`、`INT-*`、`KEY-*`、`CAP-*`。
- 修改规则语义、默认值或兼容行为时提升 `ui-spec-version`，并列出受影响页面。
- 页面 `ui-spec-version` 必须与本文件完全相等，不使用版本范围。全局版本变化后必须检查并更新所有页面。
- 只有本文件和目标页面文件均为 `approved`、版本完全相等且规则无冲突时，正式交付才完整有效。
- 页面引用的图片和研究材料均为非规范性辅助信息；所有实现要求必须完整写在本文件或目标页面文件中。

---

## 1. 产品体验与信息层级

| ID | 规则 |
|---|---|
| `EXP-01` | 产品形态是**独立常驻的原生 TUI 进程**，全屏接管终端，自有事件循环。不得引入 HTTP Server、Service 进程，或任何依赖 IDE 宿主的运行方式。 |
| `EXP-02` | 每个任务必须构成 **Intent → Analyze → Execute → Verify** 闭环。只做其中一段的界面不完整：给了分析必须给下一步动作，给了动作必须给验证结果。 |
| `EXP-03` | 信息层级自外向内固定为 **Shell（外壳）→ Task（任务）→ Canvas（画布）→ Primitive（图元）**。跨层直接引用是违规。 |
| `EXP-04` | 界面分 **Chrome 层**与 **Canvas 层**。判据：用户在这块内容上做的是「选择 / 导航 / 切换 / 确认」→ Chrome 层，必须是有状态的真组件；做的是「看数值 / 比大小 / 找异常」→ Canvas 层，回到字符网格。同一面板内两者混合时按子区域分别处理。 |
| `EXP-05` | AI 的结论与数据本身**分属两个视觉系统**，不得共用色彩通道。数据用域色阶，AI 判断用语义色，且必须可整层关闭。 |

→ `AGENTS.md`、`src/features/migration-flow/`、`docs/FRAMEWORK.md`

---

## 2. 全局 Shell 与布局

| ID | 规则 |
|---|---|
| `LAYOUT-01` | Shell 固定由六个区域组成：Header（品牌 + Tab 条 + 环境 chip）、Dock（左侧任务 / 工程树 / 工具）、Canvas（主画布）、Inspector（右侧副画布）、Console（Agent 控制台）、Keybar + StatusBar（底部两行）。 |
| `LAYOUT-02` | Dock 从 Header 下沿**通到底**，不被 Console 截断。 |
| `LAYOUT-03` | Canvas 外尺寸减去左右框线与内边距（各 2 列）才是图元可用宽；行方向只减上下框线，**标题排在上框线里，不另占一行**。 |
| `LAYOUT-04` | Console 默认高度随宽度档位变化（见 §8），展开态在默认值上 **+3 行**。 |
| `LAYOUT-05` | 溢出一律靠**滚动 + 截断**处理，不得靠缩小字符或改变行高（终端没有这两个自由度）。 |

→ `src/components/ui/shell.tsx`、`src/platform/terminal/layout.ts`

---

## 3. 视觉 Token

**只收当前有效结论。推导过程与已推翻方案见 `docs/VISUAL.md`，那份文档不是契约。**

### 3.1 表面 `VIS-SURFACE`

```
--background-outer   #0B0B0B   应用最外层
--background         #101010   应用底
--background-elevated #141414  面板底
--surface-1          #161616   卡片
--surface-2          #1C1C1C   表头 / 工具栏
--surface-3          #262626   hover
--surface-4          #313131   选中 / 节点高亮
```

### 3.2 前景 `VIS-FG` —— 预合成实色，终端无 alpha

以 `#1C1C1C` 档为基准（其余表面档见 `docs/VISUAL.md` §1.2 全表）：

```
foreground  #E7E7E7   (on surface: #E8E8E8)
secondary   #9F9F9F   (on surface: #A4A4A4)
muted       #707070   (on surface: #777777)
disabled    #555555
```

| ID | 规则 |
|---|---|
| `VIS-FG-01` | **disabled 档不得用于正文**。拍平后对比度约 2.2:1，终端无字体抗锯齿加持，比 Web 更难读。disabled 只用于分隔线与装饰字符；不可用文本最低使用 muted 档。 |

### 3.3 语义与品牌 `VIS-SEM`

```
--primary        #0077FF   填充 / 边框 / 焦点底色
--primary-text   #3D98FF   一切文本 / 链接 / 图标
--accent         #7C8DB8   元数据 / ID / 次级强调
--success        #04D793   ✓ 完成 / 通过
--warning        #FFAA3B   ⚠ 风险 / 待处理 / 非致命异常
--danger         #FF4B7B   ✕ 失败 / Critical / 高危操作
--kunpeng        #ED1C24   身份标识专用
--kunpeng-2      #C9C9C9   标识次色
```

| ID | 规则 |
|---|---|
| `VIS-SEM-01` | **颜色三分工**：Kunpeng 红 `#ED1C24` 只做身份；品牌蓝 `#0077FF` 只做交互；错误红 `#FF4B7B` 只做语义。判据：看到红色时该想到「华为鲲鹏」还是「出事了」？两种含义同屏出现即违规。 |
| `VIS-SEM-02` | **品牌蓝不得用于文本**。`#0077FF` 在 `#1C1C1C` 上对比度 4.12，不达 AA。一切文本 / 链接 / 图标改用 `#3D98FF`（5.79–6.46，全部达标）。 |
| `VIS-SEM-03` | **强调色配额**：蓝 = 当前对象，或当前唯一推荐动作。其余一律中性。评审判据：遮住所有蓝色，还能说清「我现在选中的是什么」吗？能，说明蓝铺多了。 |
| `VIS-SEM-04` | 状态不得**仅**由颜色承载，必须同时有字符或位置差异（见 `A11Y-02`）。 |

### 3.4 状态叠加 `VIS-STATE` —— 预合成（基于 surface-2）

```
base      #1C1C1C
hover     #202020
selected  #18293C
focus     #162E49
info-bg   #142538    warning-bg #382A18    danger-bg #351B24
```

### 3.5 边框 `VIS-BORDER`

```
--border-subtle #242424    --border #2D2D2D    --border-strong #3B3B3B
--decoration    #1E2529    背景字符场 / 装饰
```

| ID | 规则 |
|---|---|
| `VIS-BORDER-01` | 终端无阴影，层级一律用**边框强度 + 表面步进**表达，不得模拟投影。 |

### 3.6 数据色阶 `VIS-RAMP` —— 域色映射

```
copy-blue     #052C75 #094CCD #3C7CF6 #76A3F9 #B1CAFC     CPU
l0a-violet    #3F0675 #6E0ACD #9B3CF6 #B977F9 #D7B1FB     NPU
accum-orange  #773303 #A44604 #D15905 #F96A06 #FA8838 #FBAB74 #FDCFAF   Memory
mte-amber     #713F12 #CA8A04 #F4CB22 #FBDC59 #FDEB9D     I/O
ub-green      #4D7209 #86C70F #B3F141 #CAF57A #E1F9B3
```

| ID | 规则 |
|---|---|
| `VIS-RAMP-01` | 高亮色阶**只用于数据可视化**，不得用于 UI 面板背景或文本。 |
| `VIS-RAMP-02` | 顺序型数据（热力、密度、强度）用**单一色阶内取档**；分类型数据（泳道身份）用**不同色阶**。两者不得混用同一通道。 |
| `VIS-RAMP-03` | 禁止自造调色板。需要新色先在本节登记。第三类分类色使用 l0a-violet，不使用未登记的 cyan。 |
| `VIS-RAMP-04` | 域色阶不上文字，只上色块与点阵。 |

### 3.7 间距 `VIS-SPACE` —— 双轴

终端单元格非正方，4px 基准间距拆成列 / 行两轴：

```
x1 0  x2 1  x3 2  x4 2  x5 3  x6 3      （列）
y1 0  y2 0  y3 0  y4 1  y5 1  y6 2      （行）
```

→ `src/theme/tokens.ts`

---

## 4. 排版与字符宽度

| ID | 规则 |
|---|---|
| `TYPE-01` | 全等宽单一字号。层级**不由字号编码**，改由「粗细 + 色阶 + 大写字距 + 缩进」四者组合编码。 |
| `TYPE-02` | 所有布局计算必须使用 **display width** 而非字符数：CJK 与全角标点按 2 列计，组合字符与零宽字符按 0 列计。 |
| `TYPE-03` | Braille（`U+2800`–`U+28FF`）按 1 列计，但**必须在能力探测确认可用后才使用**（见 `CAP-04`）。 |
| `TYPE-04` | emoji 宽度在终端间不一致，**不得用于任何参与列对齐的位置**；状态标记使用 `✓ ✕ ⚠ ● ○ ▶ ⏸` 等确定单宽字符。 |
| `TYPE-05` | 截断统一在**尾部**，用单字符省略号 `…`；路径类字段允许中段截断，但必须保留首段与文件名。 |
| `TYPE-06` | 数值与单位之间固定一个空格，同列数值**右对齐**，单位左对齐。 |

→ `src/components/ui/primitives.tsx`

---

## 5. 通用组件契约

### 5.1 契约字段 `COMP-01`

每个可复用组件必须声明：`states`（适用状态集合）、`tier`（首选渲染层）、`degradation`（有序降级路径）、`keyboardPath`（键盘等价操作）、`tokens`（使用的 token）。

```ts
type RenderTier = "T0" | "T1" | "T2" | "T3" | "T4";
type SemanticTone = "neutral" | "success" | "warning" | "danger" | "accent";
```

### 5.2 组件清单 `COMP-02`

二十二个通用组件，跨页面复用，页面不得自造同义组件：

Agent Timeline · Plan Card · Evidence List · Diagnosis Graph · Diff View · Metric Visualization · Sparkline · Trace View · Knowledge Card · Command Palette · Approval Bar · Tool Card · Summary Card · Selector Popup · Side Block · Collapsible Op Row · Context Gauge · Live Canvas · Heatmap Grid · Sortable Table · Split Container · Overlay

| ID | 规则 |
|---|---|
| `COMP-03` | **Chrome 层组件必须具备 hover / selected / focus / disabled 四态**，不得用无状态文本行冒充。 |
| `COMP-04` | 选中态 = `VIS-STATE` 的 `selected` 底色 **+ 左侧 2 列强调条**，两者必须同时出现（非颜色语义要求）。 |
| `COMP-05` | 组件不得在业务页面里被复制改写。需要新样式先确认无可用组件，再进本清单。 |

→ `src/components/ui/component-library.tsx`、`src/components/ui/types.ts`

### 5.3 图元尺寸判决 `COMP-SIZE`

**十七种画法**。「画得下」和「读得出」不是一回事——低于最小尺寸**不缩着画，直接退成 fallback 形态**。判决集中在一处纯函数，不由各 widget 自行决定。

| 组 | 图元 | 最小 | 推荐 | 纵横比 列÷行 | 收缩 | 画不下 → 退成 |
|---|---|---|---|---|---|---|
| 比大小 | Metric Bar | 10×1 | 20×1 | 恒 1 行 | ① | 数值 + 单位 |
| | Ranking | 24×4 | 34×11 | 每行恒 1 行 | ③ | Top-1 + 数值，尾部标 `… N more` |
| | Grouped Bar | 17×3 | 26×4 | 行 = 系列数 + 1 | ② | 各自独立的 Metric Bar |
| | Before / After | 24×1 | 32×1 | 恒 1 行 | ② | `120ms → 70ms (−42%)` 纯文本 |
| 看趋势 | Line | 20×3 | 40×6 | 5 – 24 | ③ | Sparkline |
| | Area | 20×2 | 40×5 | 5 – 24 | ② | Sparkline |
| | Sparkline | 8×1 | 20×1 | 恒 1 行 | ① | 当前值 + 峰值 |
| | Mirrored Area | 20×2 | 40×4 | 5 – 24，**行数必为偶数** | ② | 两行数值 ↑ / ↓ |
| 找位置 | Scatter | 16×8 | 24×12 | **恒 2.0** | ③ | 不画，退成 bound 判定文字 |
| | Flame | 30×3 | 60×8 | 行 = 栈深，**宽度不封顶** | ④ | Top-N 自耗时表 |
| | Timeline | 30×3 | 56×6 | 行 = 泳道数，**宽度不封顶** | ④ | 每泳道一行占用百分比 |
| 看余量 | Waterline | 3×4 | 3×8 | **0.25 – 0.8** | ① | `38.2 / 64 GiB` 纯文本 |
| | Progress | 12×1 | 28×1 | 恒 1 行 | ① | 百分比数字；未知进度用 `⠹` + 已耗时 |
| | Segmented | 16×2 | 30×2 | 恒 2 行（含图例） | ① | 各段数值列表 |
| 读单值 | Pixel Number | 11×5 | 19×5 | 行恒 5 | ① | 常规字号数字 |
| | Stat | 18×1 | 32×1 | 恒 1 行 | ① | 值 + delta 一行文本 |
| 看分布 | Heatmap | 16×4 | 32×6 | 行列由拓扑定 | ④ | 按 NUMA 聚合成 4 行 |

| ID | 规则 |
|---|---|
| `COMP-SIZE-01` | **视觉纵横比 = 列 ÷ (2 × 行)**。终端字符格约 1:2，上表所有比例都是原始格子比，换算成视觉比例要再除以 2。按格子数直觉想比例会稳定地想扁一倍。 |
| `COMP-SIZE-02` | 纵横比越界**不是拒画，是把盒子裁到带内再画**。 |
| `COMP-SIZE-03` | 三条硬约束，越界即失真：**Scatter 锁死 2.0**（两根轴都是数据轴，拉扁就是把斜率画错）· **Waterline 上界 0.8 < 1**（扁了就读成横向 bar，而水位答「还剩多少」、bar 答「占了多少」）· **Mirrored Area 行数必为偶数**（奇数行劈不开上下两半）。 |
| `COMP-SIZE-04` | **收缩优先级按降级损失排，不按重要性排**。① 掉成一行数字、结论零损失 → ② 掉一层仍答同一问题 → ③ 压缩会丢掉比较能力 → ④ 形状即信息，压扁等于没画。同一档内先让推荐面积大的。 |
| `COMP-SIZE-05` | 图元尺寸单位是**字符格**，不与网页 CSS 的 4px 网格对齐。把它们凑成 4 的倍数就是把规格编出来。 |

→ `src/components/charts/primitive-layout.ts`

---

## 6. 公共状态

十个状态，组件按适用性声明子集，**不得自造第十一个**：

```ts
type ComponentState =
  | "default" | "focused" | "selected" | "disabled"
  | "loading" | "empty" | "loaded"
  | "error" | "failed" | "cancelled";
```

| ID | 规则 |
|---|---|
| `STATE-01` | 任何发起异步的组件必须同时定义 `loading` / `loaded` / `empty` / `error` 四态，缺一不可。 |
| `STATE-02` | `loading` 必须可中断，且中断路径要在 keybar 上可见（`Esc`）。 |
| `STATE-03` | `error` 与 `cancelled` 必须区分**可重试**与**不可重试**：可重试提供 `R`，不可重试只提供 `Esc` 返回。 |
| `STATE-04` | `empty` 不得只显示空白，必须说明「为什么空」以及「下一步能做什么」。 |
| `STATE-05` | 失败信息使用 typed error，**不得吞掉异常**，也不得把原始堆栈直接贴给用户。 |
| `STATE-06` | 状态切换不得丢失用户已输入内容与滚动位置。 |

→ `src/shared/app-error.ts`、`src/features/migration-flow/`

---

## 7. 焦点与交互

### 7.1 焦点模型

| ID | 规则 |
|---|---|
| `INT-01` | 焦点环固定顺序：宽屏 `dock → tabs → canvas → console → prompt`；窄屏去掉 `dock`。`Tab` 前进，`Shift+Tab` 后退，**循环不断头**。 |
| `INT-02` | 焦点必须可见，且不得**仅**用颜色表示。 |
| `INT-03` | **所有鼠标交互必须有键盘等价路径。** 没有键盘路径的功能不得上线。 |
| `INT-04` | 高风险操作（应用补丁、写文件、覆盖配置）必须经确认层，且确认层默认停在**非破坏性**选项上。 |

### 7.2 全局键位 `KEY-*`

| 键 | 作用 | 作用域 |
|---|---|---|
| `Ctrl+P` | 命令面板 | 全局 |
| `F1` / `?` | 快捷键帮助 | 全局 |
| `Esc` | 关浮层 → 中断加载 → 返回上一屏 → 退出 | 全局，按此优先级 |
| `Ctrl+C` | 退出 | 全局 |
| `Tab` / `Shift+Tab` | 焦点前进 / 后退 | 全局 |
| `Ctrl+B` | 折叠 / 展开 Dock | 工作台 |
| `Ctrl+I` | 显示 / 隐藏 Inspector | 工作台 |
| `Ctrl+J` | 展开 / 收起 Console | 工作台 |
| `↑` `↓` / `k` `j` | 列表导航 | 列表焦点内 |
| `Enter` | 当前推荐动作 | 上下文 |
| `R` | 重试 | `error(retryable)` / `cancelled` |

| ID | 规则 |
|---|---|
| `KEY-01` | 上表键位**全局保留**，页面不得重新绑定。 |
| `KEY-02` | 页面局部键位只能使用单字母，且必须在 keybar 中显示；与上表冲突的一律无效。 |
| `KEY-03` | keybar 最多显示 6 项；宽度 < 80 时压到 4 项，优先丢弃全局项、保留上下文项。 |

→ `src/app/App.tsx`、`src/components/ui/keybar.tsx`

---

## 8. 响应式与 Resize

**六档宽度断点。窄屏 = `< 80` 列，宽屏 = `≥ 160` 列，中间四档是渐进降级。**

| 宽度 | mode | Dock | 副画布 | Inspector | Console | 最窄 Canvas | 图元可用宽 |
|---|---|---|---|---|---|---|---|
| ≥ 160 | `wide-three` | 27 列展开 | ✓ | ✓ | 8 行 | 28 列 | 24 列 |
| 140–159 | `wide-two-inspector` | 25 列展开 | ✓ | ✓ 细条 | 8 行 | 45 列 | 41 列 |
| 120–139 | `two-canvas` | 23 列展开 | ✓ | ✕ | 7 行 | 38 列 | 34 列 |
| 100–119 | `collapsed-dock` | 3 列折叠 | ✓ | ✕ | 7 行 | 39 列 | 35 列 |
| 80–99 | `single-canvas` | 3 列折叠 | ✕ | ✕ | 6 行 | 77 列 | 73 列 |
| < 80 | `narrow` | 隐藏 | ✕ | ✕ | 5 行 | 40 列 | 36 列 |

| ID | 规则 |
|---|---|
| `LAYOUT-BP-01` | 断点判定**只依据宽度**。高度不参与档位切换，只用于单个区域的行数裁剪。 |
| `LAYOUT-BP-02` | 所有屏幕的 compact 判定必须落在上表边界上，**不得自选中间值**。 |
| `LAYOUT-BP-03` | **全链路最窄的 Canvas 出现在最宽的终端上**——160 列三分屏的第三栏只有 28 列、图元可用 24 列，Flame 与 Timeline 在这一栏放不下，必须退 fallback。设计三分屏时先算这一栏。 |
| `LAYOUT-BP-04` | 整屏降级链（给几个 Canvas、每个多宽）与图元级判决（每个 Canvas 里那张图怎么缩）必须对得上，由同一份单测同时压，否则会出现「整屏还在给栏，图元级已全线拒画」的空栏。 |
| `LAYOUT-BP-05` | 必须支持**动态 resize**：拖动窗口时逐档切换，不得要求重启。 |
| `LAYOUT-BP-06` | 验收基线尺寸为 **160×50** 与 **58×32**，两者都必须可用。 |

→ `src/platform/terminal/layout.ts`

---

## 9. 终端能力与降级

### 9.1 探测维度 `CAP-*`

```ts
{ colorMode: "truecolor" | "ansi16" | "none";
  unicode: boolean; braille: boolean; mouse: boolean;
  ssh: boolean; animations: "full" | "reduced" | "none" }
```

| ID | 规则 |
|---|---|
| `CAP-01` | 能力**在启动时探测一次并写入会话**，不得在每次渲染前试探。 |
| `CAP-02` | `NO_COLOR` 或 `TERM=dumb` → `colorMode: "none"`。此时**所有语义必须仍能读出**，靠字符与位置承载。 |
| `CAP-03` | 非 truecolor 终端降到 ANSI 16 色映射；色阶塌缩后**顺序关系必须保留**（暗→亮的相对次序不得倒置）。 |
| `CAP-04` | Braille 不可用时退到块字符（T2 → T1），密度下降但趋势方向必须保留。 |
| `CAP-05` | 检测到 SSH 时自动进入 `animations: "reduced"`，并按低带宽预算限制重绘区域。 |
| `CAP-06` | 无鼠标环境下所有功能必须仍然完整可达（由 `INT-03` 保证）。 |
| `CAP-07` | 每一条降级都必须声明 `preserves`：降级后仍必须保留的非颜色语义。**没有 `preserves` 的降级不算降级，算功能删除。** |

### 9.2 降级原因枚举

`no-color` · `ansi16` · `no-unicode` · `no-braille` · `no-mouse` · `ssh` · `reduced-motion` · `insufficient-space`

### 9.3 渲染分层

| 层 | 手段 | 状态 |
|---|---|---|
| T0 | 纯文本 | ✓ 已实现 |
| T1 | 块字符 / 半块 | ✓ 已实现 |
| T2 | Braille（2×4 = 8 倍密度） | ✓ 已实现 |
| T3 | 真彩热力 | ✓ 已实现 |
| T4 | 交互式（可选中 / 可排序 / 可钻取） | ✓ 已实现 |
| T5 | 终端图形协议（Kitty / Sixel / iTerm2） | ✕ **未实现，见 §12** |

→ `src/platform/terminal/capabilities.ts`、`src/components/ui/types.ts`

---

## 10. 动效与性能

| ID | 规则 |
|---|---|
| `MOTION-01` | **动效只服务于功能，禁止装饰性循环动画。** 允许：状态转换提示、加载指示、焦点移动。禁止：呼吸灯、常驻粒子、纯装饰渐变流动。 |
| `MOTION-02` | 时长按 **30fps 帧数**计，不使用毫秒 easing 曲线。 |
| `MOTION-03` | `animations: "reduced"`（含全部 SSH 会话）下只保留状态转换的**首末帧**，取消中间过渡。`"none"` 下全部取消。 |
| `MOTION-04` | **禁止在 render 期间使用 `Math.random()`。** 需要随机形态的背景场必须由确定性种子在挂载时一次生成，否则输出不可测试。 |
| `MOTION-05` | 重绘范围限制在发生变化的区域；全屏重绘只允许在档位切换与 resize 时发生。 |

→ `src/components/ui/landing-field.ts`

---

## 11. 可访问性

| ID | 规则 |
|---|---|
| `A11Y-01` | **纯键盘可完成全部任务**，无例外（`INT-03`）。 |
| `A11Y-02` | **非颜色语义**：任何靠颜色表达的状态必须同时有字符或位置差异。验证方法——`NO_COLOR=1` 跑一遍，信息不得丢失。 |
| `A11Y-03` | 正文对比度 ≥ 4.5:1。品牌蓝文本违规，改用 `#3D98FF`（`VIS-SEM-02`）。 |
| `A11Y-04` | 焦点在任何色彩模式下都必须可见。 |
| `A11Y-05` | 出错必须给**恢复路径**，不能只报错。 |
| `A11Y-06` | 敏感输入（口令、密钥）走 masked 输入，且**不进入上下文**。 |

---

## 12. 全局禁止项与已知缺口

### 12.1 禁止项

| ID | 禁止 |
|---|---|
| `NG-01` | 裸颜色字面量。一切颜色必须走 §3 token。 |
| `NG-02` | 页面私有 token。跨页面的值只能进本文件。 |
| `NG-03` | 手拼框线。框线由组件绘制，不在业务代码里拼字符。 |
| `NG-04` | 与 §7.2 冲突的快捷键。 |
| `NG-05` | 仅靠颜色表达的状态。 |
| `NG-06` | 无降级路径的高能力字符（Braille / 特殊块 / emoji）。 |
| `NG-07` | render 期间的不确定性（随机、当前时间、未排序遍历）。 |
| `NG-08` | 自造调色板（`VIS-RAMP-03`）。 |
| `NG-09` | 把实现不了的视觉效果留给后续阶段解释——高斯模糊、自由定位、亚像素粒子一律不进设计。 |

### 12.2 已知缺口 —— **不是已批准的省略，是还没做**

| 缺口 | 影响 | 处理 |
|---|---|---|
| **T5 终端图形协议未实现** | 高密度标识只能走 T1–T3 | 需先验证目标环境的实际可用比例；在此之前所有设计不得依赖 T5 |
| **`pages/` 下无任何页面合同**（只有 `_TEMPLATE.md`） | 页面级布局、数据、状态、验收条件均无正式来源，现有实现依据的是 `docs/` 研究材料 | 按 `_TEMPLATE.md` 补齐，每页一份 |
| **真实后端未接** | 全部数据来自确定性 Mock | 通过新增 Gateway adapter 完成，不改变页面与 domain 契约 |
| **Braille 在中文等宽字体下的对齐未验证** | T2 图元在 CJK 环境可能错位 | 需在目标终端实测后回写 `CAP-04` |
| **本文件仍为 `draft`** | 正式 UI 交付未就绪 | 需人工复审后改 `approved` |

---

## 13. 版本、例外与冲突处理

- 页面声明的 `ui-spec-version` 必须与本文件完全相等。
- 全局版本变化后必须检查所有页面、更新版本声明，并把受影响页面改为 `draft` 直至人工复审。
- 页面不得自行覆盖全局规则。例外必须同时满足：具有 `EXC-*` ID、登记在下表、状态为 `approved`、被目标页面明确引用。
- UI 交付与已知技术约束冲突时，必须列出规则、技术约束和影响，交由人工裁决；裁决完成前保持 `draft`，**不得以任一侧静默覆盖另一侧**。

### 页面例外登记表

| 例外 ID | 页面 | 被覆盖规则 | 理由与范围 | 状态 | 退出条件 |
|---|---|---|---|---|---|
| 暂无 | — | — | — | — | — |

---

## 14. 受影响页面

| 全局版本 | 状态 | 受影响页面 | 说明 |
|---|---|---|---|
| 0.1.0 | draft | — | 初始交付结构，正文全为占位 |
| 0.2.0 | draft | 全部（尚无页面文件） | 从已运行实现反向固化 §1–§12。`pages/` 下仍无页面合同，补页时需逐条引用本文件规则 ID |
