# Kunpeng DevKit AI — TUI 竞品分析 · 框架 / 交互 / 布局

> UX 视角 · 8 竞品 · 22 触点 · 2026-08 · for Kunpeng DevKit AI
> 方法：四阶段流水线（规划 → 搜集 → 分析 → 可视化）；旅程地图 4 行结构；触点维度单一性拆分

---

## 1. TUI 分辨率模型：Cell 是区别于 GUI 的根本约束

> 现代 TUI 不能再简单分成"低分辨率字符界面"和 GUI 两类。更准确的做法，是看它的**主 UI plane 到底用什么分辨率表达**。

TUI 产品通常没有固定的"1920×1080"分辨率——它跟着 Terminal 窗口变化，例如当前可能是 `160 cols × 48 rows`。现代图形协议则可能让其中某个区域额外获得 pixel resolution。

### 1.1 三档分类

| 类型 | 代表产品 | 主界面分辨率 | 图形分辨率 |
|---|---|---|---|
| 纯 Cell TUI | OpenCode · Lazygit | `columns × rows` | 基本没有独立 pixel plane |
| Sub-cell TUI | btop | 仍是 `columns × rows` | 用 Braille/block 把一个 cell 再细分 |
| Hybrid TUI | Yazi + Kitty/WezTerm/iTerm2 | UI 是 `columns × rows` | 图片区域可以是真实 raster pixels |

---

### 1.2 纯 Cell TUI · OpenCode：设计语言 GUI-like，空间分辨率仍是 Cell

OpenCode 官方明确把自己的终端界面称为 TUI，使用 OpenTUI 作为底层 UI core——支持 component、layout 等现代 UI 抽象，但最终仍然是在 terminal 中绘制。

假设 Terminal 窗口 1440×900 px，字体 cell 约 9×18 px，那么 OpenCode 真正拥有的布局坐标大约是 **160 columns × 50 rows**。

它看到的不是：

```text
input:  x = 183 px,  y = 764 px,  width = 1034 px,  height = 72 px
```

而更类似：

```text
input:  column = 18,  row = 42,  width = 124 cells,  height = 4 rows
```

所以类似这样的布局：

```text
┌ Sessions ─────────┬─────────────────────────────────┐
│ session A         │                                 │
│ session B         │ Explain this function           │
│                   │                                 │
│                   │ ● Read src/main.ts              │
│                   │ ● Edited src/api.ts             │
│                   │                                 │
├───────────────────┴─────────────────────────────────┤
│ Ask anything...                                    │
└─────────────────────────────────────────────────────┘
```

看起来有 panel、border、input、status、scroll、selection、color hierarchy——但这些东西的边缘仍然只能落在 **column 73 / 74 / 75**，不能落在 `73.4 columns`。

OpenCode 甚至同时有 Desktop App，恰好说明：**同一个产品逻辑，可以有 TUI frontend 和真正的 GUI frontend。** 设计语言越来越 GUI-like，但空间分辨率仍然是纯 Cell TUI。

**Cell Grid 整数列约束示意：**

```text
Column:  71   72   73   74   75   76   77
         │    │    │    │    │    │    │
  row 1  │ A  │ B  │ C  │ D  │ E  │ F  │   ← border 可落 col 73/74/75
         │    │    │  ╎  │  ╎  │  ╎  │    │
  row 2  │    │    │  ╎  │  ╎  │  ╎  │    │   ← UI 边缘 = 整数 column
         │    │    │  ╎  │  ╎  │  ╎  │    │
  row 3  │    │    │  ✕  │  ✓  │  ✕  │    │   ← ✕=col 73.4 不可落 ✕

  1440×900 px window ÷ 9×18 px/cell = 160 cols × 50 rows
```

> **关键判断**：设计语言可以越来越 GUI-like，但 **geometry resolution 仍是纯 Cell**。UI 边缘只能落在整数 column——这就是 Cell TUI 区别于 GUI 的根本约束。

---

### 1.3 纯 Cell TUI · Lazygit：典型的"第一代现代 TUI"

Lazygit 是另一个纯粹的例子——大量信息通过几个 panel 组织：

```text
┌ Status ─────────┬ Files ────────────────┐
│ repo            │ M main.go             │
├ Branches ───────┤ M README.md           │
│ main            │                       │
│ feature-x       ├───────────────────────┤
├ Commits ────────┤ Diff                  │
│ abc123 ...      │ - old                 │
│ def456 ...      │ + new                 │
└─────────────────┴───────────────────────┘
```

这里所有 panel border、divider、list row、diff line、selected state 基本都是字符。如果 Terminal 是 `120 × 40 cells`，那么整个 Lazygit 的**逻辑 UI resolution 就是 120 × 40**。

这句话甚至可以很字面理解：

> 这个应用当前最多拥有 **4,800 个"空间格子"**。

当然每个格子还能携带 glyph、foreground、background、bold、underline……所以不是 4800 个黑白像素，但 **geometry resolution 就是这个量级**。

---

### 1.4 Sub-cell TUI · btop：偷偷把 Cell 再切小

btop 很适合回答"TUI 是不是真的一定低分辨率？"——它依然是字符 TUI，但默认可以使用 **Unicode Braille 字符**画 graph。

为什么 Braille 能做到？一个 Braille 字符内部可以表达 **2×4 = 8 个 dot**：

```text
● ●
● ●
● ●
● ●
```

因此，一个 `40 columns × 10 rows` 的 graph 区域，普通 character grid 来看只有 `40 × 10`，但用 Braille 表达 binary dot pattern，视觉采样网格可以近似变成 **~80 × 40 dots**：

```text
┌────────────────────────────┐
│ ⠀⠀⠀⢀⣀⣤⣶⣿⣿⣶⣤⣀⠀⠀⠀ │
│ ⠀⣠⣾⣿⣿⣿⠟⠉⠀⠀⠙⣿⣷⣄⠀ │
│ ⣴⣿⣿⠟⠉⠀⠀⠀⠀⠀⠀⠀⠀⠙⣿⣿ │
└────────────────────────────┘
```

这已经比 `____----████----` 精细很多。

但这里必须注意：**它仍然不是 pixel graphics。** 程序仍然只是发送 `U+28XX Braille glyph`，Terminal Emulator 再用字体把它 rasterize 出来。所以实际上经历了：

```text
data → 2×4 dot pattern → 选择 Unicode Braille char → Terminal cell → font raster → pixels
```

而不是：

```text
data → drawPixel(x, y)
```

因此我把 btop 称为 **Sub-cell rendering**——比纯 Cell 细，但仍在 glyph 层面。

**两条渲染管线对比：**

```text
╔══════════════════════════════════════════════════════════════╗
║ Braille glyph 路径（6 步间接）         drawPixel 路径（1 步直达） ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  data                           data                         ║
║    ↓                              ↓                          ║
║  2×4 dot pattern                drawPixel(x, y)              ║
║    ↓                              ↓                          ║
║  选 Unicode Braille char         屏幕上的 pixel               ║
║    ↓                                                         ║
║  Terminal cell                                               ║
║    ↓                                                         ║
║  font rasterization                                          ║
║    ↓                                                         ║
║  screen pixels                                               ║
║                                                              ║
║  精度受限于 font rendering          真正的 pixel-addressable    ║
╚══════════════════════════════════════════════════════════════╝
```

---

### 1.5 Hybrid TUI · Yazi：现在最典型的双重分辨率产品 🆕

Yazi 是我认为最值得看的 Hybrid TUI。它本身是 Terminal file manager，但官方直接支持 Kitty Graphics Protocol、Kitty Unicode placeholders、iTerm2 Inline Image Protocol、Sixel、Überzug++、Chafa 用于图片 preview。

于是它可能长这样：

```text
┌──────────────┬─────────────────┬──────────────────────┐
│ directories  │ files           │ preview              │
│              │                 │                      │
│ Documents    │ photo.jpg       │    ┌────────────┐    │
│ Downloads    │ report.pdf      │    │            │    │
│ Pictures     │ model.png       │    │ REAL IMAGE │    │
│              │                 │    │            │    │
│              │                 │    └────────────┘    │
└──────────────┴─────────────────┴──────────────────────┘
```

左边 directories / files / border / selection 仍然是 **Cell resolution**，但右边 preview 可以是真实 raster image。

假设右边 preview 占 `60 columns × 30 rows`，每个 cell `9 × 18 px`，那么 viewport 是 `540 × 540 px`——图片在这个区域里以几百 × 几百 pixel rasterize，而不是 `60 × 30 characters`。

这就出现了一个非常重要的**双重 resolution**：

```text
Yazi UI
├── Layout plane:  160 × 50 cells
└── Image preview plane:  e.g. ~540 × 540 pixels
```

这才是现代 Terminal UI 真正有意思的地方。**位置用 cell 定位，内容用 pixel 渲染。**

| 协议 | 类型 | 支持终端 |
|---|---|---|
| Kitty Graphics Protocol | raster graphics, pixel positioning | Kitty |
| iTerm2 Inline Image | inline image | iTerm2, WezTerm |
| Sixel | bitmap graphics | WezTerm, mlterm |
| Überzug++ | external window overlay | various |
| Chafa | character approximation fallback | any |

**协议降级链（Capability Adaptation）：**

```text
Kitty Graphics ──→ iTerm2 Inline ──→ Sixel ──→ Überzug++ ──→ Chafa ──→ textual fallback
  (raster)          (raster)        (bitmap)    (overlay)     (half-block)   (纯文本)
    最佳              次佳           色深受限      外部窗口      字符近似       最后兜底
```

> 按终端能力自动退化，capability detection 一次查询、全组件复用。这已接近现代 TUI Design System 的 **capability adaptation 问题**。

---

### 1.6 Kitty Graphics Protocol 把这件事推到了更极端

Kitty 官方的 Graphics Protocol 设计目标就是允许 terminal client **render arbitrary raster graphics**，并且可以把 graphics 放到 individual pixel positions：

```text
Terminal
┌──────────────────────────────────────────┐
│ text text text                           │
│                                          │
│          ┌─────────────────────┐         │
│          │   800 × 400 image   │         │
│          │                     │         │
│          └─────────────────────┘         │
│                                          │
│ > _                                      │
└──────────────────────────────────────────┘
```

里面那块已经是真正的 pixel graphics。Kitty 甚至提供 `kitten icat` 直接在 terminal 中显示图片。WezTerm 也同时支持 iTerm2 image protocol、Kitty graphics、Sixel——所以这已经不是 Kitty 一个 terminal 的私有实验。

更极端的情况：Kitty 官方列出的 integrations 里已存在 Terminal PDF/EPUB viewer，Ratatui 生态现在也有统一处理 Kitty/Sixel/iTerm2 image backend 的 widget，2026 年已经有 TUI media player 同时支持 ASCII video、terminal graphics protocol、SDL external window。

> **"Terminal 只能画低分辨率字符"已经不成立。**

---

### 1.7 关键边界：图片是 pixel，布局仍是 cell

这也是最重要的一个细节。假设 Terminal window 1440×900 px，160×50 cells，cell = 9×18 px。TUI 定义一个图片 widget：

```text
x = col 90,  y = row 5,  width = 60 cells,  height = 30 cells
```

那么它先得到一个 `60×9=540px × 30×18=540px` 的 pixel viewport。然后图片内部以 `540 × 540 pixels` 渲染。

也就是说：

```text
位置/布局：Cell resolution
内容：     Pixel resolution
```

Ratatui-image 的文档甚至明确说明，为了做这种映射，它需要查询 terminal window pixel size + row/column count，然后推导 **cell 的 pixel size**。这句话非常能说明现代 TUI 的本质。

---

### 1.8 两层画布模型

所以今天的 Terminal 实际上可以理解成"两层画布"：

```text
┌──────────────────────────────────────────────┐
│ Terminal Emulator                            │
│                                              │
│  TEXT / CELL PLANE                           │
│                                              │
│  ┌───┬───┬───┬───┬───┬───┐                 │
│  │ A │ B │ C │   │   │   │                 │
│  ├───┼───┼───┼───┼───┼───┤                 │
│  │   │   │   │   │   │   │                 │
│  └───┴───┴───┴───┴───┴───┘                 │
│                                              │
│          +                                   │
│                                              │
│  GRAPHICS / PIXEL PLANE                      │
│                                              │
│        ┌─────────────────────┐               │
│        │                     │               │
│        │  arbitrary raster   │               │
│        │      pixels         │               │
│        │                     │               │
│        └─────────────────────┘               │
│                                              │
└──────────────────────────────────────────────┘
```

这个模型比"Terminal = 字符屏幕"已经准确很多。

---

### 1.9 产品谱系：按空间表达能力排列

```text
 Level 1: Character-only            Level 2: Sub-cell graphics         Level 3: Hybrid raster TUI
 ┌─────────────────────┐           ┌─────────────────────┐           ┌─────────────────────┐
 │ Lazygit / OpenCode  │           │ btop                 │           │ Yazi + Kitty         │
 │                     │           │                      │           │                      │
 │  A B C D E F G H    │           │  ⣿⣷⣶⣤⣀⠀           │           │ dir  dir  ┌───────┐ │
 │  I J K L M N O P    │           │  ⠀⣠⣾⣿⣿⣿           │           │ dir  file │ IMAGE │ │
 │  Q R S T U V W X    │           │  ⣴⣿⣿⠟⠉⠀           │           │ file file └───────┘ │
 │                     │           │                      │           │                      │
 │ Cell → glyph+style  │           │ Cell → Braille glyph │           │ Cell UI + real pixels │
 │                     │           │                      │           │                      │
 │ 160×50 logical      │           │ UI: 160×50 cells     │           │ Layout: 160×50 cells │
 │ resolution          │           │ Viz: ~320×200 dots   │           │ Preview: ~540×540 px │
 └─────────────────────┘           └─────────────────────┘           └─────────────────────┘
```

#### Level 1：Character-only

**Lazygit / OpenCode**

```text
Cell → glyph + fg + bg + style
```

- 典型分辨率：~160 × 50 logical cells
- 主要设计对象：Text · List · Panel · Border · Input · Focus · Selection

#### Level 2：Sub-cell graphics

**btop**

```text
Cell → Unicode Braille / Block → simulate subpixels
```

- UI geometry：160 × 50 cells
- 某个 Braille graph 的有效 visual sampling：~320 × 200 dots
- 但还是 glyph

#### Level 3：Hybrid raster TUI

**Yazi + Kitty / WezTerm / iTerm2**

```text
Cell UI + real pixel graphics
```

- Layout：160 × 50 cells
- Preview：540 × 540 px
- 这是现在最明显突破"低分辨率 Terminal"概念的产品形态

---

### 1.10 为什么 AI TUI 没变成"小型 Figma"

因为 pixel graphics 解决的只是 **content rendering resolution**，而没有彻底解决 **UI layout model**。

今天大多数 TUI 仍然是这样的 layout tree：

```text
             Layout System (TUI)                Layout System (GUI)
                  │                                    │
             Cell Grid (离散)                   Continuous Geometry (连续)
                  │                                    │
        ┌─────────┴─────────┐              ┌──────────┼──────────┐
        │                   │              │          │          │
      Text              Image region      Text       Vector     Raster
        │                   │              │          │          │
      Cell                Pixels        sub-pixel   any scale  any size

  位置 = 整数 column              位置 = 任意浮点数
  不能是 317.5px                  可以是 317.5px, 7px radius
```

所以 Yazi 的图片很高清，并不意味着：

- sidebar width = 317.5px ✓
- border radius = 7px ✓
- button x = 32.7px ✓

这些东西突然都可以用了。**它只是把一个 cell-based rectangle 里的内容换成了 pixel graphics。** 这就是目前 TUI → GUI 真正还没有跨过去的边界。

---

### 1.11 TUI Design System 视角：三套 Resolution Token

从 TUI Design System 的角度，建议把"分辨率"不要定义成一个值，而定义成三套 token：

```text
Terminal Capability

① Layout Resolution
   cols × rows
   e.g. 160 × 50 cells

② Cell Resolution
   e.g. 9 × 18 physical px / cell

③ Graphics Resolution
   pixel-addressable?
   none / sixel / iTerm / kitty
```

组件能力才由这三层共同决定。比如：

```text
Image Preview
├─ Kitty  → raster
├─ Sixel  → raster
├─ iTerm2 → raster
├─ Unicode capable → half-block approximation
└─ basic TTY → textual fallback
```

这其实已经很接近一套**现代 TUI Design System 真正应该处理的 capability adaptation 问题**，而不只是"用字符画 GUI"。

---

## 2. 范围

| 派系 | 竞品 | 选入理由 | 贡献维度 |
|---|---|---|---|
| 终端工作台派 | MobaXterm · Zellij | 多会话工作台的两种极端：GUI 停靠面板 vs 可编程 UI 插件 | 框架 · 布局 · 键位 |
| AI Coding TUI 派 | OpenCode · Claude Code | 直接同类；且在渲染架构、Plan、权限上做了完全不同的选择 | Agent 流 · 权限 · 审查 · 上下文 |
| 工程观测派 | btop · k9s · lazygit | 信息密度与图表原语的天花板；选中联动的成熟范例 | 数据密度 · 可视化 · 下钻联动 |
| Hybrid TUI 派 🆕 | Yazi | Cell UI + 真实 pixel graphics 的代表；展示现代 TUI 的双重分辨率边界 | 分辨率模型 · 图片渲染协议 · capability adaptation |

**为什么跨四派**：同派内部差异小，跨派才能暴露行业分歧点——尚未形成统一范式的地方就是创新空间。新增 Yazi 不是因为它是文件管理器，而是它展示了 Cell 布局 + Pixel 渲染共存的真实产品形态，这是理解现代 TUI 能力边界的关键参照。

**空间范式差异（最重要的一句话）**：btop 是多盒同屏全常驻，k9s 是单主视图 + 栈式下钻，lazygit 是侧栏列表 + 主区 detail 联动，Zellij 是无限递归 pane 树，**两个 AI Coding TUI 都放弃了分屏**，而 Yazi 展示了 Cell 布局层与 Pixel 渲染层可以在同一界面中共存。

---

## 3. 用户旅程地图

场景：工程师在一个 TUI 工作台里完成一次完整任务。

| | ① 启动接入 | ② 建立方向感 | ③ 表达意图 | ④ 等待与观察 | ⑤ 审查与决策 | ⑥ 收尾与复用 |
|---|---|---|---|---|---|---|
| **用户行为** | 敲命令、等界面、接上次的活、装能力 | 扫面板、找"现在能按什么"、确认在哪层 | 敲自然语言、引用文件、补参数 | 盯步骤流、展开输出、切去干别的 | 逐条读改动、批准/拒绝、验证、回退 | 导出分享、存布局、复制片段、挂起 |
| **关键触点** | 冷启动前置成本 · 屏幕接管 · 会话恢复 | 提示位置 · 提示作用域 · 位置指示 · 键位体系 · 命令入口 | 输入区形态 · 上下文引用 · 计划先行 · 配置收集时机 | 过程可见性 · 输出折叠 · 并行后台 · 进度用量 · 渲染精度 | diff 粒度 · 权限档位 · 免询问记忆 · 撤销可靠性 · 选中联动 | 布局复用 · 分享导出 · 窄屏降级 · 原生能力保全 |
| **情绪** | 0 中性 | −1 焦虑 | **+1 愉悦 ▲最高** | −1 焦虑 | **−2 沮丧 ▼最低** | −1 焦虑 |
| **摩擦 / 机会** | 摩擦：先建 session ／ 机会：零配置直接进 | 摩擦：键位撞车、不知能按什么 ／ 机会：提示随状态变 | 摩擦：前置大表单 ／ 机会：自然语言 + 用到才问 | 摩擦：日志刷屏、长任务占界面 ／ 机会：折叠 + 后台化 + **Hybrid 模式下 chart 区域升级为 pixel rendering** | 摩擦：500 行 diff 糊脸、权限疲劳、撤销假安全感 ／ 机会：证据链可验证 | 摩擦：复制不出去、布局存不下 ／ 机会：预设循环 + 逃生舱 |

### 情绪最低谷 = 最大设计机会：审查与决策

不是拍脑袋——跨四派八个产品在这一步**全都有具体的、被反复提交的 issue**：

- OpenCode 的 500+ 行 diff 内联无折叠
- **两个 AI TUI 都没有 hunk 级 accept/reject**，粒度是"按工具调用"批准
- Claude Code 的 checkpoint **不覆盖 bash 改动与 subagent 编辑**（官方自陈，等于假安全感）
- 权限确认粒度只有"这次 / 永久"两档

**整个行业在"人怎么高效审查 AI 的产出"上都很弱**——而这恰好是工程领域最不能含糊的一环。

### 情绪最高点 = 标杆：表达意图

自然语言输入 + `@` 引用 + 用到才问的配置收集，是这一代 AI TUI 相对传统工具最明确的体验跃升。要保住这个高点，不要退回表单。

---

## 4. 触点级对比（节选关键项）

完整 22 触点见 `../web/competitive-analysis.html`。以下是判断最明确的几条：

| 触点 | 最优解 | 最差解 | 判断 |
|---|---|---|---|
| 冷启动前置成本 | 除 MobaXterm 外全部零前置 | MobaXterm 先建 Session（地址/协议/凭据） | 零前置是共识 |
| 屏幕接管方式 | Claude Code **双渲染器可切**（滚动追加 / alt-screen） | 其余单一模式 | 可切最优 |
| 提示的作用域 | k9s 由导航栈驱动 · lazygit 由 context 驱动 · Zellij 由模式驱动 | 全局大键位表 | **行业共识模式** |
| 键位体系 | OpenCode leader 键 `ctrl+x` + 2000ms 窗口 | Zellij 独占 8 个 Ctrl 键，与 shell/fzf/vim 撞车 | 独占单 Ctrl 键 = 坑 |
| 命令入口 | k9s `:` + 别名 + ghost-text 补全 | MobaXterm 只有 Ribbon，无搜索式入口 | 模糊搜索 > 视觉罗列 |
| 上下文引用 | MobaXterm SFTP **跟随终端目录**（环境自己跟上） | 手动引用 | 跟随 > 手动 |
| 计划先行 | Claude Code：正式批准对话框 + 计划可外部编辑 + 自动切权限档 | OpenCode：只是权限更严的 agent，无批准流程 | 未形成范式 |
| 配置收集时机 | —— | **没有一个产品把"缺配置"做成一等公民的暂停-补齐-续跑流程** | **空白 = 机会** |
| 输出折叠 | Claude 工具结果默认折叠、MCP 折成一行、`/focus` | OpenCode 完整 diff 无折叠 | 不折叠 = 坑 |
| 渲染精度分档 | btop 三套符号（braille/block/tty）**可按盒子设定**，preset 同时切布局与精度 | AI 派几乎无图表 | **分档 + 打包进 preset** |
| 分辨率档位 🆕 | btop Sub-cell（Braille 把 cell 切细 ~2×）· Yazi Hybrid（Cell 布局 + Pixel 预览） | AI 派纯 Cell——OpenCode/Lazygit 的全部 UI 边缘只能落在整数 column | 分辨率分档是 capability adaptation 的基础 |
| 图形协议降级链 🆕 | Yazi：Kitty → iTerm2 → Sixel → Überzug++ → Chafa → textual fallback | AI 派无图形输出需求 | **按终端能力自动退化的协议链** |
| diff 粒度 | lazygit 行/hunk 级 | 两个 AI TUI **都没有 hunk 级** | **全 AI 行业缺失** |
| 免询问记忆范围 | Claude：bash 前缀→永久按仓库，文件编辑→仅到会话结束 | 只有"这次/永久"两档 | 建议安全前缀是好设计 |
| 撤销可靠性 | OpenCode git snapshot（可 redo）· lazygit reflog | Claude checkpoint 不覆盖 bash/subagent | 部分覆盖 = 假安全感 |
| 选中联动 | lazygit 左选右画（最彻底） | AI 派无（无多面板） | lazygit 是标杆 |
| 布局复用 | Zellij KDL + swap layouts + 远程 URL · btop 9 套 preset | AI 派无 | **预设循环 > 拖拽** |
| 窄屏降级 | lazygit portraitMode auto（≤84 列侧栏转竖排） | k9s 未找到自动降级，列被挤压 | lazygit 最优 |
| 原生能力保全 | Claude `[` 吐回 scrollback（唯一正面回应） | Zellij 要复制得先关边框 | **三派全中的行业级失败** |

---

## 5. 模式识别

### 通用模式（多竞品收敛）

| # | 模式 | 表现 | 反证 / 代价 |
|---|---|---|---|
| M1 | **帮助提示是"当前状态的函数"** | k9s 导航栈驱动 · lazygit context 驱动 · Zellij 模式驱动 · btop 画在盒子边框上 | Zellij 常驻提示条约占 5MB 内存 |
| M2 | **布局可变性用"预设循环"而非"拖拽调整"** | btop `p`/`P` 循环 9 套 · lazygit `+`/`_` 循环三档 | Zellij 支持任意递归但鼠标不能拖拽调尺寸，是高频吐槽 |
| M3 | **命令面板是唯一可扩展的发现性入口** | k9s `:` · OpenCode `ctrl+p` · Claude `/` 统一命令/skill/plugin/MCP | k9s 的 `:xray` 在帮助里都找不到——有面板不等于可发现 |
| M4 | **折叠低信号输出** | Claude 工具结果默认折叠、`/focus` 极简视图 | OpenCode 不折叠 → 500 行糊屏 |
| M5 | **选中联动 master-detail** | lazygit 左选右画 · k9s Pulses 图表 Enter 跳资源列表 | — |
| M6 | **零前置启动** | 除 MobaXterm 外全部 | 先建 Session 是上一代范式遗留 |
| M7 🆕 | **渲染能力按区域退化** | btop 按盒子设定 braille/block/tty · Yazi 按协议链 fallback（Kitty → iTerm2 → Sixel → half-block → textual） | 需要 terminal 支持对应协议，产品需维护 capability detection + fallback 逻辑 |

### 独特设计（可借鉴度高）

| 产品 | 设计 | 借鉴到 |
|---|---|---|
| btop | preset 打包"布局 + 渲染精度"，一键循环 | Workspace 预设同时切渲染精度 |
| btop | **窄屏阻断页可交互**——报错页上按 1-4 现场关盒子 | 错误页即操作页 |
| Zellij | **Swap Layouts**：pane 数变化时自动重排 | Canvas 数变化时自动切预设比例 |
| Zellij | **Unlock-First preset**：承认两类用户互斥，分流而非折中 | 键位方案分档 |
| Claude Code | **`[` 把 alt-screen 对话吐回原生 scrollback** | 必抄 |
| Claude Code | **rewind 双向摘要**（压前半段 / 压后半段） | 大工程迁移必需 |
| OpenCode | **`doom_loop` 权限**：同工具连调 3 次自动询问 | 作为 P10 的触发条件 |
| OpenCode | **父子会话原地导航** | 多 Agent 协作，subagent 不是黑盒 |
| k9s | **Pulses**：gauge 网格，每格都是下钻入口 | Observe 仪表盘 |
| lazygit | **command log**：把每个按键背后的真实命令打出来 | Tool Card 加一行等价 CLI |
| lazygit | **portraitMode 自动重排** | 降级链设计 |
| MobaXterm | **SFTP 跟随终端目录** | 工程树跟随 Agent 上下文（官方标 experimental 且不稳，实现留空间） |
| Yazi 🆕 | **协议降级链**：Kitty → iTerm2 → Sixel → Überzug++ → Chafa → textual | 不同面板按终端能力自动选渲染精度，capability detection 一次查询、全组件复用 |
| Yazi 🆕 | **双重分辨率共存**：左侧文件树是 Cell，右侧预览是 Pixel | DevKit 的 chart / diff / 架构图区域可在 Kitty-capable terminal 上升级为 raster 渲染 |

### 反面教训 · 七个必须绕开的坑

| # | 坑 | 证据 | 约束 |
|---|---|---|---|
| F1 | **全屏接管破坏终端原生复制/搜索** | 三派全中：Claude Code 多 issue（含 CJK 乱码）、lazygit 官方自陈、Zellij 边框挡复制 | 必须提供逃生舱 |
| F2 | **独占单 Ctrl 键与 shell/vim 撞车** | Zellij 拿走 8 个 Ctrl 键，最高频吐槽 | 用 leader 键；提供无冲突预设 |
| F3 | **大 diff 不折叠** | OpenCode 500+ 行糊屏 | 默认折叠 + 摘要优先 |
| F4 | **布局不可存 / 拒绝演进** | OpenCode 多窗口需求 closed as not planned；k9s 无预设 | Workspace 预设第一版就要有 |
| F5 | **窄屏无显式降级** | k9s 列被挤压截断 | 降级链必须显式设计 |
| F6 | **撤销只覆盖一部分 = 假安全感** | Claude checkpoint 官方自陈不追踪 bash 与 subagent | 要么全覆盖，要么显式告知边界 |
| F7 | **静默覆盖用户配置** | btop 退出覆盖 config，用户要求文档明写 | 配置写入需可预期、可版本化 |

---

## 6. 差距矩阵（节选）

| 能力 | 我们（规范） | Claude Code | OpenCode | Zellij | lazygit | Yazi 🆕 | 说明 |
|---|---|---|---|---|---|---|---|---|
| 分屏 + 布局预设 | ✓ P23 + 框架 | ✕ | ✕ not planned | ✓ 最强 | △ screenMode | — | **AI 派空白 = 差异化** |
| 选中联动 | ✓ P22 | ✕ | ✕ | ✕ | ✓ 标杆 | — | **AI 派空白 = 差异化** |
| 数据可视化图元 | ✓ T1–T3 八原语 | ✕ | ✕ | ✕ | △ commit graph | — | **AI 派空白 = 差异化** |
| hunk 级审查 | ✕ 未规划 | ✕ | ✕ | — | ✓ | — | **全 AI 行业缺失 = 机会** |
| 配置补齐流程 | ✓ P27 | △ 权限弹窗 | △ question 权限 | ✕ | ✕ | — | **无人做成一等公民 = 机会** |
| 上下文用量可视化 | ✓ P20 | ✓ `/context` | ✕ 未找到 | — | — | — | Claude 领先 |
| 窄屏降级 | ✓ 六档降级链 | — | ✕ 侧栏挤 | △ | ✓ portrait | — | 我们最完整 |
| 渲染精度分档 🆕 | ✕ 未规划 | ✕ 纯 Cell | ✕ 纯 Cell | ✕ 纯 Cell | ✕ 纯 Cell | ✓ braille + pixel | 目前仅 btop + Yazi 具备 |
| 双重分辨率 🆕 | ✕ 未规划 | ✕ | ✕ | ✕ | ✕ | ✓ Cell + Pixel | Hybrid TUI 能力边界 |

---

## 7. 行业分歧点 = 创新空间

| 分歧 | 各方答案 | 我们的判断 |
|---|---|---|
| **① 分屏要不要** | Zellij 无限递归 ／ OpenCode not planned ／ Claude 走多会话+worktree ／ lazygit 固定分区+缩放 | AI 派放弃分屏的理由是"对话是线性的"。但**工程分析不是线性的**——迁移报告要对着源码看、Trace 要对着算子表看。这是 DevKit 与通用 AI Coding 的本质差异，也是必须做分屏的理由。上限 3 格。 |
| **② 权限：模型判断还是规则匹配** | Claude 分类器模型 + 口头约束当硬约束 ／ OpenCode tree-sitter 解析后纯规则 | 工程场景更需要**确定性与可审计**——"为什么拦了我"必须能解释。倾向规则为主，模型判断作为补充提示而非阻断依据。 |
| **③ Plan：模式还是 Agent** | Claude 一等公民模式（可外部编辑计划） ／ OpenCode 只是权限更严的 agent | 站 Claude 一侧但修正它被批评处：计划应**就在界面里可见可改**，且每步标注要调哪个 DevKit 工具。 |
| **④ 发现性：常驻还是按需** | Zellij/k9s/lazygit 常驻提示条 ／ Claude/OpenCode 按需 ／ btop 画在盒子边框上 | 采 btop 空间化 + lazygit 上下文化：**底栏只放全局与当前 Workspace 的键，面板级提示画在面板边框上**。 |
| **⑤ 🆕 分辨率：纯 Cell 还是 Hybrid** | OpenCode/Lazygit 纯 Cell ／ btop Sub-cell（Braille） ／ Yazi Hybrid（Cell + Pixel） | Hybrid 是趋势但不是万能药——pixel graphics 解决了 content rendering 精度，但**没解决 layout model**（Yazi 的 sidebar 宽度仍是整数 column，不能是 317.5px）。AI 工作台的核心价值在 layout model 而非渲染精度，但 **chart / diff / 架构图预览场景值得做 capability adaptation**：在 Kitty-capable terminal 上把这些区域升级为 raster 渲染，在普通 terminal 上 fallback 到 braille/block。 |

---

## 8. 机会点（按差异化价值 × 实现成本排序）

**01 · 把"审查确认"做成强项** ★★★★★
情绪最低谷在这里，八个竞品全弱。打法：① 文件级折叠 + 摘要优先；② 每条改动挂 **Evidence**（知识库案例号 + ARM 手册章节 + 源码行号），把"我为什么该同意"变成可点开验证的；③ 逐文件批准而非一次性全批；④ 撤销显式声明覆盖边界。
*这是 DevKit 的天然优势——迁移改动本就有知识库依据可引，通用 AI Coding 工具引不出来。*

**02 · 分屏 + 选中联动：AI Coding 派的集体空白** ★★★★★
Canvas A/B 双栏 + P22 联动，把"结论 ↔ 证据"做成常驻空间关系。再叠 MobaXterm 式跟随——Agent 改到哪个文件，工程树自动定位到哪。**联动不只发生在用户点击时，也发生在 Agent 行动时。**

**03 · 配置补齐做成一等公民流程** ★★★★☆
无竞品做过。关键三点：就地暂停不回滚、解释为什么这一步需要它、非敏感项记忆复用。

**04 · 把观测派的数据密度带进 AI 工作台** ★★★★☆
借鉴 btop 两点：渲染精度分档打包进 Workspace 预设；颜色承载额外维度。更进一步：在 Kitty/WezTerm/iTerm2 capable terminal 上，把 chart / 架构图 / 拓扑图区域升级为真实 pixel rendering（参考 Yazi 的双重分辨率模型），普通 terminal fallback 到 btop 式 braille/block。**不同面板可以有不同的渲染精度档位**——这是 M7 的核心启示。

**05 · 终端原生能力的逃生舱** ★★★★☆
抄 Claude 的 `[`；一键关掉边框装饰进纯文本模式；键盘文本选择必须有。

**06 · 布局预设循环 + 数量变化自动重排** ★★★☆☆
Canvas 数量 2↔3 变化时自动切对应预设比例。

**07 · 工具调用透明化：抄 lazygit 的 command log** ★★★☆☆
Tool Card 加一行**等价 CLI 命令**——让用户知道 Agent 在跑什么，也能拿去脚本复用。对 DevKit 这种"CLI 已有等价物"的产品几乎零成本。

**08 · 反空转：抄 OpenCode 的 doom_loop** ★★☆☆☆
作为 P10 Approval 的触发条件加入。

---

## 9. 一句话总结

AI Coding TUI 在**意图表达**上大幅领先传统工具，但在**审查确认**与**空间组织**上集体退化到了比 lazygit、btop 更弱的水平——因为它们默认"对话是线性的"。

Kunpeng DevKit AI 的机会正在这里：**把观测派的空间密度与联动、工作台派的布局能力，接到 AI 派的意图表达之上。** 同时，从 Yazi 和 Kitty Graphics Protocol 学到的双重分辨率模型，让 DevKit 可以在 chart / diff / 架构图等区域按 terminal 能力自适应升级渲染精度——Cell 布局仍是骨架，但关键信息区的表现力不必受限于 glyph。
