# Kunpeng DevKit AI — 方案 B 视觉与交互规格

> **方案名**：Charm Flow  
> **版本**：0.1  
> **阶段**：Launch 原型规格  
> **日期**：2026-08-12  
> **实现方向**：Go + Bubble Tea v2 + Lip Gloss v2 + Bubbles v2  
> **基准背景色**：`#181822`

---

## 0. 文档目的

本文档定义 Kunpeng DevKit AI 的 **方案 B：Charm Flow**。第一阶段只实现 Launch 开场页面，但页面必须具备真实 TUI 的键盘交互、焦点状态、终端尺寸适配和颜色降级能力，可以作为后续工作台的应用骨架。

方案 B 不是方案 A 的换肤版本。两套方案使用相同的产品内容，但通过不同的信息组织、视觉重心和运动语言形成可比较的设计方向：

| 维度 | 方案 A：Kunpeng Native | 方案 B：Charm Flow |
|---|---|---|
| 感受 | 工业、系统启动、硬件原生 | 轻盈、友好、现代开发者工具 |
| 框架 | Python + Textual | Go + Bubble Tea v2 |
| 首屏主角 | 品牌标识与启动日志 | AI 任务输入与建议动作 |
| 空间 | 大型居中启动画面 | 左品牌、右交互的紧凑卡片 |
| 背景 | 字符半调场、边缘闪烁 | 纯色底、克制的局部装饰 |
| 动效 | Boot sequence | 状态反馈、短促入场、Spinner |

### 0.1 第一阶段范围

包含：

- Launch 首屏的完整静态布局
- Kunpeng 品牌区
- 主任务输入框
- 三个建议动作
- Runtime / MCP / ARM64 状态摘要
- 键盘导航、鼠标点击和窗口尺寸响应
- 提交后的短暂 Loading 与反馈状态
- True Color、256 色、无颜色环境的降级
- 可复现的 VHS 演示脚本

不包含：

- 真实项目扫描
- 真实 MCP 连接与能力安装
- 登录、账号与网络状态
- Plan、Workspace、Diff、诊断等后续页面
- 方案 A 的全屏半调背景
- 完整的多页面路由

---

## 1. 设计目标

### 1.1 产品目标

用户进入应用后，应在 3 秒内理解三件事：

1. 这是 Kunpeng DevKit AI。
2. 可以直接描述一个开发任务。
3. 当前环境已准备好，并且有可立即执行的建议动作。

### 1.2 视觉目标

- **Prompt-first**：主输入框是全页第一视觉焦点。
- **Calm by default**：没有操作时页面保持稳定，不用持续动画制造活跃感。
- **Color with purpose**：颜色用于身份、焦点和状态，不用于填满空间。
- **Terminal honest**：设计必须由终端单元格、ANSI 色彩和标准字符真实实现。
- **Charm-like, not copied**：吸收 Charm 的轻巧边框、彩色层级和即时反馈，但保留 Kunpeng 的品牌身份。

### 1.3 非目标

- 不模拟网页卡片阴影、毛玻璃或模糊。
- 不把所有内容都装进完整边框。
- 不做消费级聊天机器人欢迎页。
- 不用大段 ASCII 艺术压过核心交互。
- 不依赖终端图形协议展示 Logo。

---

## 2. 设计原则

### P1. 一个首要动作

首屏只允许一个最高优先级动作：**输入任务并提交**。建议动作是输入的快捷方式，不与输入框竞争。

### P2. 状态驱动动效

动效只发生在：进入、聚焦、提交、运行、成功或失败。禁止全屏随机闪烁和永久循环的装饰动画。

### P3. 留白也是组件

页面通过终端空行和列间距建立节奏。不得为了“看起来丰富”而填满背景或增加无意义面板。

### P4. 选中比边框更重要

选中态采用“左侧彩色指示符 + 局部底色 + 主文字提亮”。只有输入框使用完整强调边框。

### P5. 品牌红不承担错误语义

Kunpeng Red 只用于 Logo 与品牌名。错误使用独立的 danger pink，避免同屏歧义。

---

## 3. 信息架构

Launch 页面由五个区域组成：

```text
Launch
├── Brand
│   ├── Kunpeng mark
│   ├── KUNPENG / DEVKIT AI
│   └── ARM64 READY badge
├── Prompt
│   ├── field label
│   ├── text input
│   └── submit hint
├── Actions
│   ├── Migrate a project
│   ├── Scan workspace
│   └── Resume nginx migration
├── Environment status
│   ├── Runtime ready
│   ├── 2/4 MCP tools
│   └── ARM64 toolchain
└── Key help
    ├── ↑↓ navigate
    ├── enter select
    ├── ctrl+p commands
    └── ctrl+q quit
```

信息层级从高到低：

1. Prompt 当前焦点和用户输入
2. 建议动作的当前选中项
3. Kunpeng 品牌身份
4. 环境是否可用
5. 快捷键提示

---

## 4. 页面布局

### 4.1 基准终端

| 项目 | 规格 |
|---|---|
| Canonical viewport | `156 × 48` cells |
| 舒适范围 | `120–180 × 36–55` |
| 最小可用 | `96 × 30` |
| 极窄降级 | `< 96` 列，切为单列 |
| 不支持 | `< 72` 列或 `< 24` 行，显示尺寸提示页 |
| 主内容最大宽度 | `104` 列 |
| 主内容水平位置 | 视觉居中 |

“视觉居中”允许比数学中心向上偏 1–2 行，使底部帮助栏不会把主内容顶高。

### 4.2 宽屏双列布局

适用于 `width >= 112`：

```text
                        KUNPENG DEVKIT AI

            ┌─ Brand ─────────┐    ╭─ Ask DevKit AI ───────────────────────╮
            │  Kunpeng mark   │    │  Describe a task…                    │
            │  KUNPENG        │    ╰────────────────────────────── enter ↵─╯
            │  DEVKIT AI      │
            │  ARM64 READY    │      Start with an action
            └─────────────────┘      ┃ ✦  Migrate a project
                                     │    Analyze and create an ARM64 plan
                                     │
                                     │ ◇  Scan workspace
                                     │    Detect toolchains and MCP tools
                                     │
                                     │ ↗  Resume nginx migration       82%
                                     │    Updated 3 days ago · 2 to review

                                     ● Runtime ready  ·  2/4 MCP  ·  ARM64
                                     ↑↓ navigate  enter select  ctrl+p commands
```

实现时不显示示意图中的 `Brand` 标题和外框。左区主要依靠留白建立边界，右区只有 Prompt 使用完整边框。

#### 网格规格

| 区域 | 宽度 | 说明 |
|---|---:|---|
| 左品牌列 | 28 cells | 固定宽，禁止内容换行 |
| 列间距 | 6 cells | `width < 128` 时降到 4 |
| 右交互列 | 68 cells | Prompt 和动作列表同宽 |
| 总内容宽 | 102 cells | 不含外部留白 |
| Prompt 高度 | 3 rows | 上下边框 + 1 行输入 |
| 动作列表 | 9–11 rows | 每项 2 行，项目之间 1 行 |
| 状态摘要 | 1 row | 超宽内容优先隐藏低优先项 |
| 帮助栏 | 1 row | 与状态摘要间隔 1 行 |

### 4.3 单列布局

适用于 `72 <= width < 112`：

```text
              [mark]  KUNPENG DEVKIT AI   ARM64 READY

        ╭─ Ask DevKit AI ─────────────────────────────╮
        │  Describe a task…                           │
        ╰──────────────────────────────────── enter ↵─╯

          Start with an action
        ┃ ✦  Migrate a project
        │    Analyze and create an ARM64 plan

        │ ◇  Scan workspace
        │    Detect toolchains and MCP tools

          ● Runtime ready · 2/4 MCP · ARM64
          ↑↓ navigate · enter select · ctrl+p commands
```

规则：

- 品牌区改为单行 compact mark，不使用 13 行完整标识。
- Resume 动作在垂直空间不足时只保留一行。
- 状态摘要优先保留 `Runtime ready`，其次 `MCP`，最后 `ARM64`。
- 帮助栏优先保留 `enter` 与 `ctrl+q`。

### 4.4 尺寸不足页

```text
╭─ Kunpeng DevKit AI ─────────────────╮
│ Terminal is too small               │
│ Current 68×20 · Required 72×24      │
│ Resize the window to continue.      │
╰─────────────────────────────────────╯
```

此页不显示动画，不截断关键数字；终端恢复到最低尺寸后自动返回 Launch。

---

## 5. 色彩系统

### 5.1 核心色板

背景色由本方案锁定为 `#181822`。

| Token | Hex | 用途 |
|---|---|---|
| `bg.base` | `#181822` | 全屏唯一基础背景 |
| `bg.surface` | `#20202B` | 输入框、选中动作的局部表面 |
| `bg.surface_hover` | `#282836` | 鼠标 hover |
| `bg.surface_active` | `#303043` | press / 强选择状态 |
| `border.subtle` | `#343445` | 非焦点分隔、Prompt 默认边框 |
| `border.strong` | `#54546A` | 非彩色强边框 |
| `text.primary` | `#F4F4F5` | 标题、输入、当前动作 |
| `text.secondary` | `#B0AFBE` | 正文说明、状态 |
| `text.muted` | `#77778A` | 标签、快捷键、时间信息 |
| `text.disabled` | `#555568` | 非交互装饰字符 |
| `brand.kunpeng` | `#ED1C24` | Kunpeng 标识，不作错误色 |
| `brand.mark_secondary` | `#C9C9C9` | Kunpeng 标识第二色 |
| `accent.pink` | `#FF5FA2` | Charm 气质的辅助高光 |
| `accent.purple` | `#9B7BFF` | 主焦点、当前选择、链接 |
| `accent.cyan` | `#5DE4E7` | Runtime / 工具环境信息 |
| `state.success` | `#73DACA` | ready、完成、连接成功 |
| `state.warning` | `#FFC777` | 部分加载、需确认 |
| `state.danger` | `#FF6B8A` | 错误与不可执行 |

### 5.2 色彩角色

| 对象 | 默认 | Focus / Selected | Disabled / Error |
|---|---|---|---|
| Prompt border | `border.subtle` | `accent.purple` | danger 时 `state.danger` |
| Prompt label | `text.muted` | `accent.pink` | `text.disabled` |
| 输入文本 | `text.primary` | `text.primary` | `text.disabled` |
| 当前动作指示符 | 无 | `accent.purple` | `text.disabled` |
| 动作图标 | `text.muted` | `accent.pink` | `text.disabled` |
| 状态圆点 | 语义色 | 语义色 | `text.disabled` |
| Logo | 品牌双色 | 不响应焦点 | 不降灰 |

### 5.3 强调色配额

同一时刻只允许：

- 一个紫色完整边框：当前 Prompt 焦点；或
- 一个紫色左侧动作指示符：当前 Actions 焦点。

当焦点从 Prompt 移到 Actions，Prompt 边框必须退回 `border.subtle`。不得让两个区域同时看起来处于键盘焦点。

Pink 只用于小面积图标、标签或进度头部；Cyan 只用于环境状态。整块卡片不得使用 Pink、Purple 或 Cyan 填充。

### 5.4 终端颜色降级

| 环境 | 策略 |
|---|---|
| True Color | 使用上述完整色值 |
| ANSI 256 | 映射到最接近色，确保 foreground/background 不合并 |
| ANSI 16 | 焦点依赖粗体、反色和 `┃`，状态同时使用符号 |
| `NO_COLOR` | 移除色彩；保留边框、粗体、符号和选中底反转 |

状态不能只靠颜色：

- Ready：`●` 或 `✓`
- Warning：`▲` 或 `!`
- Error：`×`
- Running：Spinner 帧

---

## 6. 字体与字符语言

### 6.1 字体假设

应用无法控制终端字体。推荐演示环境使用：

1. JetBrains Mono
2. SF Mono
3. Sarasa Term SC（中文演示优先）

所有布局必须按单元格宽度计算，不按字节数或 rune 数计算。中英文混排必须通过 `go-runewidth` 等等宽测量逻辑验证。

### 6.2 字符层级

| 层级 | 表达 |
|---|---|
| Product name | Bold + uppercase + `text.primary` |
| Section label | `text.muted`，首字母大写，不做全字间插空 |
| Primary content | `text.primary` |
| Description | `text.secondary` |
| Metadata | `text.muted` |
| Shortcut key | key 用 `text.secondary`，说明用 `text.muted` |

方案 B 不沿用方案 A 的五行超宽点阵字标。`KUNPENG DEVKIT AI` 使用普通终端字形与粗体，以减轻启动页重量。

### 6.3 边框字符

- Prompt：圆角边框 `╭ ╮ ╰ ╯ ─ │`
- 普通信息面板：必要时使用直角 `┌ ┐ └ ┘`
- 当前项：`┃`
- 非当前列表轨道：`│`
- 分隔：`·`

若终端不支持 Unicode Box Drawing，降级为 `+ - | >`。

---

## 7. 品牌区规格

### 7.1 宽屏品牌区

内容：

- Kunpeng 两色字符标识
- `KUNPENG`
- `DEVKIT AI`
- `ARM64 READY` 状态胶囊

标识要求：

- 以 `web/demo.html` 中已确认的双色标识为唯一结构来源。
- 允许为方案 B 制作 compact 版本，但只能通过等比例抽样或重新建立明确像素网格，不能自由手绘近似。
- 红色上翼使用 `brand.kunpeng`。
- 灰色下翼使用 `brand.mark_secondary`。
- 禁止 glow、阴影和循环闪烁。
- 标识与字标左对齐，字标不穿插在标识内部。

`ARM64 READY`：

```text
● ARM64 READY
```

- `●` 使用 `state.success`
- 文字使用 `text.secondary`
- 可以使用 `bg.surface` 作为轻量胶囊底色
- 只表达运行目标身份，不代表整个环境所有能力都完成加载

### 7.2 Compact 品牌区

窄屏使用 1–2 行版本：

```text
[mark] KUNPENG DEVKIT AI  ·  ● ARM64
```

当宽度不足时，依次隐藏：`READY`、分隔符、文字 Logo 中的 `KUNPENG`；最小仍保留 `[mark] DEVKIT AI`。

---

## 8. Prompt 组件

### 8.1 内容

默认标签：`Ask DevKit AI`

默认 placeholder：

```text
Describe a migration, build, diagnosis, or optimization task…
```

宽度不足时使用：

```text
Describe a task…
```

右侧提交提示：`enter ↵`。输入内容接近右侧提示时，提示隐藏，不能覆盖用户文本。

### 8.2 状态

| 状态 | 表现 |
|---|---|
| Idle | subtle 边框、muted label、显示 placeholder |
| Focus | purple 边框、pink label、正常光标闪烁 |
| Typing | 与 Focus 相同，placeholder 消失 |
| Submitted | 输入锁定 250–600ms，label 变为 `Starting task` |
| Loading | 左侧出现 Spinner，提交提示消失 |
| Success | `✓ Task ready`，随后进入下一状态占位反馈 |
| Error | danger 边框，下一行显示简短错误；输入仍可编辑 |
| Disabled | muted 边框与文本，不接收焦点 |

### 8.3 输入行为

- 支持中文输入法、粘贴、左右移动、Home/End、Option/Ctrl 单词移动（以终端可识别键为准）。
- Enter 提交非空内容。
- 空内容 Enter 不报错，只触发一次 120ms 的边框强调反馈。
- Esc：有内容时清空；空内容时移除输入焦点并选中第一个建议动作。
- `Ctrl+U` 清空当前输入。
- 粘贴多行内容时转换为单行，换行替换为一个空格。
- 首阶段最大输入长度为 500 个显示字符；超出时给出本地提示，不崩溃。

### 8.4 光标

- 使用终端原生/组件光标能力。
- Blink 周期遵循终端或 Bubbles textinput 默认值。
- 页面中不得同时存在第二个装饰性闪烁光标。

---

## 9. 建议动作组件

### 9.1 数据模型

| ID | 图标 | 标题 | 描述 | 动作 |
|---|---|---|---|---|
| `migrate` | `✦` | Migrate a project | Analyze dependencies and create an ARM64 plan | 将迁移任务写入 Prompt |
| `scan` | `◇` | Scan workspace | Detect toolchains, dependencies, and MCP tools | 将扫描任务写入 Prompt |
| `resume` | `↗` | Resume nginx migration | Updated 3 days ago · 82% · 2 to review | 进入恢复任务占位反馈 |

第一版的实际 Prompt 文案：

- Migrate：`Migrate the current project to Kunpeng ARM64`
- Scan：`Scan the current workspace for Kunpeng compatibility`
- Resume：`Resume the nginx migration task`

### 9.2 状态表现

```text
┃ ✦  Migrate a project
│    Analyze dependencies and create an ARM64 plan
```

| 状态 | 轨道 | 图标 | 标题 | 背景 |
|---|---|---|---|---|
| Idle | 空格或 `│` muted | muted | secondary | transparent |
| Hover | `│` secondary | secondary | primary | `bg.surface_hover` |
| Selected | `┃` purple | pink | primary bold | `bg.surface` |
| Pressed | `┃` purple | pink | primary bold | `bg.surface_active` |
| Disabled | `│` disabled | disabled | disabled | transparent |

列表项不使用完整四边框。背景只覆盖右侧动作列宽度，不延伸到整屏。

### 9.3 导航

- Prompt 聚焦时，`Down` 进入 Actions 并选中第一项。
- Actions 聚焦时，`Up/Down` 循环或钳制导航；第一版采用**钳制**，到边界不跳转。
- 第一项按 `Up` 返回 Prompt。
- Enter 激活当前动作。
- Tab 在 Prompt → Actions → Prompt 之间循环。
- 鼠标 hover 只改变 hover，不自动夺取键盘焦点。
- 鼠标点击同时设置选中并激活动作。

### 9.4 激活反馈

Migrate 与 Scan：

1. 将对应文案填入 Prompt。
2. 焦点回到 Prompt。
3. 光标位于文字末尾。
4. 不自动提交，允许用户继续编辑。

Resume：

1. 当前项短暂显示 Spinner。
2. 状态摘要显示 `Restoring session…`。
3. 600–900ms 后显示 `✓ Session restored`。
4. 第一阶段停留在 Launch 并显示占位反馈，不进入未实现页面。

---

## 10. 环境状态摘要

默认内容：

```text
● Runtime ready  ·  2/4 MCP tools  ·  ARM64 toolchain
```

### 10.1 状态规则

- Runtime ready：success。
- `2/4 MCP tools`：warning，因为只有部分能力装载。
- ARM64 toolchain：cyan，作为环境信息而不是成功结论。
- 分隔符使用 `text.disabled`。
- 状态只显示摘要，不在 Launch 展开五行 boot log；详情留给后续命令或状态页。

### 10.2 可变状态

| 场景 | 文案 |
|---|---|
| 初始化 | Spinner + `Checking local runtime…` |
| 正常 | `● Runtime ready` |
| 部分工具 | `▲ 2/4 MCP tools` |
| 无工具 | `× MCP tools unavailable` |
| Resume | Spinner + `Restoring session…` |
| Submit | Spinner + `Preparing task…` |

状态更新不得导致整个主内容横向跳动；为 Spinner/状态符号预留固定 2 cells。

---

## 11. 快捷键帮助

默认：

```text
↑↓ navigate   enter select   ctrl+p commands   ctrl+q quit
```

规则：

- key 使用 `text.secondary`，动作说明使用 `text.muted`。
- 不为每个快捷键绘制胶囊边框，保持轻量。
- 根据焦点上下文改变：Prompt 聚焦时 `enter submit`，Actions 聚焦时 `enter select`。
- `Ctrl+P` 第一阶段可以打开简单命令列表，若暂不实现则不显示该提示。
- `Ctrl+Q` 始终退出；也支持 `q` 退出仅限没有输入焦点的状态。

---

## 12. 背景与装饰

### 12.1 背景

- 全屏背景严格使用 `#181822`。
- 不绘制方案 A 的 `· - + #` 半调场。
- 不使用扫描线、噪点或全屏星点。
- 组件未覆盖处保持同一背景色，避免出现矩形色块断层。

### 12.2 可选静态装饰

为了保留 Charm 的轻松感，可在宽屏下使用最多两处静态装饰：

```text
  ·                                         ✦
```

约束：

- 只出现在主内容外部。
- 使用 `text.disabled`。
- 总数不超过 4 个字符。
- 不闪烁、不移动、不随机重排。
- 在 `< 128` 列自动隐藏。

第一版建议默认关闭，待主体视觉确认后再评估。

---

## 13. 动效规格

### 13.1 入场时序

总时长控制在 600ms 内：

| 时间 | 事件 |
|---:|---|
| 0ms | 清屏，绘制 `bg.base` |
| 60ms | Brand 出现 |
| 140ms | Prompt 出现并获得焦点 |
| 240ms | Actions 出现 |
| 340ms | Environment status 出现 |
| 420ms | Key help 出现 |

终端不支持真正透明度渐变。实现可采用“分段出现”或由 muted 色切换到目标色，禁止模拟高频抖动。

### 13.2 Spinner

默认优先使用 Bubbles Spinner 的轻量帧组。推荐：

```text
⣾ ⣽ ⣻ ⢿ ⡿ ⣟ ⣯ ⣷
```

Braille 不可用时降级：

```text
| / - \
```

- 速度：约 80–100ms/frame。
- 同一页面最多一个活动 Spinner。
- Spinner 必须对应真实或模拟的短暂状态，空闲时不运行。

### 13.3 选择反馈

- 键盘切换时即时更新，不做延迟。
- 不使用逐行滑动动画，以免在 SSH 中产生重绘拖影。
- 可选 Harmonica 动效仅用于后续进度值，不用于列表焦点。

### 13.4 Reduced motion

提供 `--no-animation` 或环境配置：

- 入场所有区域第一帧同时出现。
- Spinner 仍可运行，因为它表达状态；若完全禁用，则改为静态 `…`。
- 光标闪烁遵循终端设置。

---

## 14. 交互状态机

```text
BOOT
  └─> PROMPT_FOCUSED
        ├─ type ───────────────> PROMPT_EDITING
        ├─ down/tab ───────────> ACTIONS_FOCUSED
        └─ enter(non-empty) ───> SUBMITTING

ACTIONS_FOCUSED
  ├─ up/down ──────────────────> ACTIONS_FOCUSED(index±1)
  ├─ up(first) / tab ──────────> PROMPT_FOCUSED
  ├─ enter(migrate/scan) ──────> PROMPT_EDITING(prefilled)
  └─ enter(resume) ────────────> RESTORING

SUBMITTING
  ├─ success ──────────────────> READY_FEEDBACK
  └─ error ────────────────────> PROMPT_ERROR

RESTORING
  ├─ success ──────────────────> READY_FEEDBACK
  └─ error ────────────────────> ACTION_ERROR
```

第一阶段 `READY_FEEDBACK` 不跳页，在 Prompt 下方显示：

```text
✓ Task captured · Workspace view is the next implementation step
```

2.5 秒后反馈变为 muted，但不自动消失，便于截图验收。

---

## 15. 文案规格

### 15.1 第一版界面语言

方案 B 第一版使用英文 UI，以贴近 Charm 的产品气质并减少 CJK 宽度对视觉原型的干扰。用户输入完整支持中文。

后续需要中文界面时，所有文案从代码抽离，不将中英文条件写入 View 渲染函数。

### 15.2 Tone of voice

- 简短、主动、具体。
- 不说“欢迎使用”。直接给出任务入口。
- 不使用夸张 AI 文案，如 “Unlock infinite possibilities”。
- 状态描述事实，不拟人化。
- 错误说明下一步，而不仅是失败结论。

示例：

| 不推荐 | 推荐 |
|---|---|
| Something went wrong | MCP tools unavailable · press `r` to retry |
| Let AI work its magic | Preparing an ARM64 migration plan… |
| Welcome back! | Resume nginx migration · updated 3 days ago |

---

## 16. 可访问性与可用性

- 所有操作可只用键盘完成。
- 不以颜色作为唯一状态编码。
- 当前焦点必须至少由两个信号表达：边框/轨道、粗体、底色三选二。
- 主文字与 `#181822` 背景保持高对比。
- muted 文本只承载辅助信息，不承载唯一关键指令。
- 鼠标是增强能力，不是必需路径。
- 中文双宽字符、Emoji 与组合字符不得破坏右侧边框。
- 输入内容滚动时保证光标始终可见。
- Resize 期间不得 panic、残留旧帧或输出滚动历史。

---

## 17. 技术实现规格

### 17.1 技术栈

采用 Charm v2 模块路径：

```go
charm.land/bubbletea/v2
charm.land/lipgloss/v2
charm.land/bubbles/v2
```

职责划分：

- Bubble Tea：Elm Architecture、事件、窗口 Resize、命令与渲染循环。
- Lip Gloss：样式、边框、Join、宽高约束和颜色降级。
- Bubbles textinput：Prompt 输入与光标。
- Bubbles spinner：提交和恢复状态。
- Bubbles help/key：如能保持视觉轻量则使用，否则自定义一行 help view。
- VHS：固定尺寸录制演示。

### 17.2 目录建议

为避免与方案 A 的 Python 文件混杂，方案 B 放入独立目录：

```text
demo/go-charmbracelet/
├── cmd/devkitai/main.go
├── internal/app/
│   ├── model.go
│   ├── update.go
│   ├── view.go
│   └── messages.go
├── internal/components/
│   ├── brand.go
│   ├── prompt.go
│   ├── actions.go
│   ├── environment.go
│   └── keyhelp.go
├── internal/theme/
│   ├── colors.go
│   └── styles.go
├── internal/layout/
│   └── launch.go
├── testdata/
│   └── golden/
├── demo.tape
├── go.mod
└── README.md
```

### 17.3 Model 最小字段

```go
type FocusArea int
const (
    FocusPrompt FocusArea = iota
    FocusActions
)

type Phase int
const (
    PhaseBoot Phase = iota
    PhaseReady
    PhaseSubmitting
    PhaseRestoring
    PhaseFeedback
    PhaseError
)

type Model struct {
    width, height int
    focus         FocusArea
    phase         Phase
    selected      int
    input         textinput.Model
    spinner       spinner.Model
    feedback      string
    noAnimation   bool
    darkBackground bool
}
```

具体字段可在实现时调整，但焦点与业务 Phase 必须分离，避免“选中项”和“正在运行状态”混在一个枚举中。

### 17.4 View 规则

- `View()` 必须是确定性的纯渲染，不启动 I/O。
- 所有动态宽度先计算可用 cells，再渲染内容。
- Join 后必须校验最终宽高，禁止凭空格手调到“看起来差不多”。
- 背景色需要覆盖每一个输出 cell，包括 padding 与空白行。
- 应用使用 Alternate Screen。
- Resize 后在下一帧完整重排，不保留旧布局缓存。
- 终端背景检测由 Bubble Tea 请求并在收到响应后设置主题；若无法检测，本方案默认按 dark 渲染。

### 17.5 性能目标

- Idle 状态不持续 Tick，除光标组件自身行为外不重绘全屏。
- Spinner 运行时 Tick 不高于 12.5 FPS。
- Canonical viewport 本地按键到视觉响应目标 `< 50ms`。
- SSH 低带宽下避免全屏装饰动画和大面积颜色变化。
- Resize 连续触发时不能积压异步命令。

---

## 18. 测试与验收

### 18.1 视觉验收

Canonical `156×48` 必须满足：

- 主内容整体水平居中，视觉中心不偏左。
- 背景所有区域均为 `#181822`，无额外矩形底色断层。
- Prompt 是第一视觉焦点。
- 左品牌区不高于右侧核心内容，不抢占主输入框。
- Kunpeng Logo 结构准确，红灰分区正确，无错位。
- 当前焦点只有一个。
- 动作列表没有三张厚重的完整边框卡片。
- 底部状态与快捷键对齐、不换行。
- 页面静止 3 秒时只有输入光标可能闪烁。

### 18.2 响应式验收尺寸

至少验证：

| 尺寸 | 预期 |
|---|---|
| `156×48` | Canonical 双列 |
| `120×36` | 紧凑双列 |
| `100×32` | 单列 |
| `80×24` | 最小单列 |
| `68×20` | 尺寸不足提示 |

每个尺寸检查：无截断关键内容、无越界、无边框断裂、无双宽字符错位。

### 18.3 交互验收

- 启动后 Prompt 自动聚焦。
- 可输入中文并正确删除。
- Down 进入动作列表，Up 返回 Prompt。
- 三个动作均可激活。
- Migrate/Scan 填入 Prompt 且不自动提交。
- Resume 显示短暂 Spinner 和成功反馈。
- Enter 提交非空任务。
- Esc 与 Ctrl+U 清空输入。
- Ctrl+Q 退出并恢复终端。
- Resize 保留输入内容、选中项和 Phase。
- 鼠标点击不会造成键盘焦点状态不同步。

### 18.4 降级验收

- `NO_COLOR=1` 下仍能识别焦点、状态和选择。
- `TERM=xterm-256color` 下没有文字与背景融为一体。
- Box Drawing 不可用时 ASCII 边框闭合。
- Braille Spinner 不可用时回退到 ASCII Spinner。

### 18.5 自动化建议

- Update 状态机单元测试。
- 各 viewport 的 golden snapshot。
- 中英文与超长输入宽度测试。
- `go test ./...`。
- `go vet ./...`。
- 最终使用 VHS 在 `156×48` 录制启动、导航、填入、提交完整路径。

---

## 19. VHS 演示脚本目标

最终演示控制在 12–16 秒：

1. Launch 入场。
2. Prompt 输入 `migrate nginx to Kunpeng ARM64`。
3. 清空输入。
4. Down 选中 Migrate。
5. Down 选中 Scan。
6. Enter 填充 Scan 文案。
7. Enter 提交。
8. Spinner → success feedback。

录制要求：

- 固定 `156×48`。
- 固定推荐字体与字号。
- 输出 GIF 和 MP4。
- 不录入真实用户名、路径或机器信息。
- 首尾各停留至少 800ms，便于评审观察。

---

## 20. 与后续页面的接口

Launch 提交后，未来进入 Workspace 页面。第一阶段虽然不实现，但应预留以下数据：

```text
LaunchResult
├── source: typed | suggestion | resumed
├── prompt: string
├── action_id: optional string
├── session_id: optional string
└── submitted_at: time
```

建议后续页面顺序：

1. Plan：AI 拆解任务与工具调用计划。
2. Workspace：左侧工程/任务 Dock，右侧主 Canvas。
3. Review：hunk 级接受/拒绝。
4. Diagnose：构建失败到证据与修复。
5. Optimize：性能数据、瓶颈和建议。

Launch 的视觉 token 应进入共享 theme，但 Launch 的双列营销式布局不得直接复用为工作台布局。

---

## 21. 设计决策记录

### D01. 背景使用 `#181822`

这是方案 B 的固定基础色。相比纯黑，它能支撑紫、粉、青三种强调色，同时与方案 A 的硬朗黑色启动屏明显区分。

### D02. 使用 Go 原生 Charm 栈

方案 B 的价值不仅是视觉差异，也包括 Bubble Tea 的 Elm Architecture 与 Charm 组件手感。若继续用 Textual 模拟，只能得到 Charm-like 皮肤，难以验证真实交互体验。

### D03. Prompt 取代 Logo 成为首屏主角

DevKit AI 的核心价值是“描述任务并开始工作”。Logo 缩小后仍能建立身份，同时让页面更直接。

### D04. 移除持续背景动画

Charm Flow 的活力来自状态反馈、色彩和响应速度。持续字符闪烁会分散输入注意力，并增加 SSH 重绘成本。

### D05. 第一版使用英文 UI

用于建立 Charm 风格的紧凑节奏，同时保留完整中文输入能力。国际化结构从第一版预留。

---

## 22. 实施顺序

1. 建立 `demo/go-charmbracelet` Go module 与基础 Bubble Tea app。
2. 定义 theme tokens 和颜色降级。
3. 实现响应式 Launch layout。
4. 实现准确的 compact Kunpeng brand。
5. 接入 Bubbles textinput。
6. 实现 Actions 焦点、导航和鼠标行为。
7. 实现状态摘要、Spinner 和模拟反馈。
8. 添加尺寸降级页与无色模式。
9. 添加状态机测试与 viewport golden tests。
10. 在 canonical viewport 做最终终端 smoke test。
11. 编写 VHS tape 并输出评审演示。

---

## 23. 第一阶段 Definition of Done

以下条件全部满足，Launch 原型才算完成：

- 使用 Go + Bubble Tea v2 独立运行。
- 背景准确为 `#181822`。
- Canonical viewport 与五档响应尺寸通过验收。
- 品牌标识结构经过设计截图核对。
- Prompt、Actions、状态摘要、帮助栏全部实现。
- 键盘路径完整，中文输入正常。
- 提交与 Resume 有真实状态变化而非静态截图。
- 无全屏持续动画；Idle 时视觉稳定。
- True Color、256 色、NO_COLOR 均可辨识。
- 测试、vet、VHS 演示和最终截图均通过。

---

## 24. 参考

- Charmbracelet：<https://github.com/charmbracelet>
- Bubble Tea：<https://github.com/charmbracelet/bubbletea>
- Lip Gloss：<https://github.com/charmbracelet/lipgloss>
- Bubbles：<https://github.com/charmbracelet/bubbles>
- VHS：<https://github.com/charmbracelet/vhs>
- 方案 A 视觉规范：`docs/VISUAL.md`
- 原始交互 Demo：`web/demo.html`
