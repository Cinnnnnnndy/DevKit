# Kunpeng DevKit AI — 原生 TUI 工作台设计规范

> 面向鲲鹏迁移 / 开发 / 诊断 / 调优的 **AI Native Terminal Engineering Workspace** 的完整设计文档集。
> 版本 0.9 · 概念设计阶段 · 2026-08

![启动页](assets/demo-splash.png)

---

## 这是什么

一套把 **Kunpeng DevKit AI 做成原生 TUI 应用**的设计方案，包含产品定位、用户旅程、交互 Pattern 库、视觉系统、竞品分析和一个可点击的十幕演示。

它不是一份 PPT，而是一套面向实现的 UI 设计源材料：颜色给到预合成后的实色十六进制、组件给到 React + OpenTUI 的行为与状态契约、渲染能力给到分层降级策略、Pattern 给到编号和适用条件。用于后续实现的内容仍须汇总进正式交付，并通过人工审核。

本仓库只负责 UI 设计与正式交付，真实产品的实现仓库独立存在。正式交付入口是 [`UI-SPEC.md`](UI-SPEC.md) 和 [`pages/`](pages/)；`docs/`、`web/` 与 `assets/` 主要服务设计研究、推导和评审。

**产品形态先钉死一条**——这是**原生 TUI 应用**，不是 CLI 命令集合，不是 IDE 里的终端面板，不是聊天窗口套壳：

| 形态 | 运行方式 | 能力边界 |
|---|---|---|
| CLI 工具 | 一次性进程，执行完退出 | 无状态、无布局、无实时 |
| IDE 插件 / 内嵌终端 | 寄生在 IDE 进程内 | 受宿主 UI 约束；必须先有 IDE |
| **原生 TUI 应用** | **独立常驻进程，全屏接管终端，自有事件循环** | **自主布局 / 状态 / 快捷键 / 渲染；直接跑在目标机器上** |

理由很实在：DevKit 部署在鲲鹏 Linux 服务器上，待迁移源码、编译器、性能计数器、驱动全在那台机器上。IDE 插件方案要本地装 IDE + 挂远程开发 + 文件同步，多一层延迟，性能采集尤其失真；原生 TUI 是 ssh 上去直接 run。

---


### Web 设计稿

下列 HTML 是自包含的单文件，**下载后双击即可打开**，无需构建、无需联网：

| 文件 | 内容 |
|---|---|
| [`web/screens.html`](web/screens.html) ★ | **五个典型页面** — 启动页 / Agent Workspace / 执行中 Tool+Diff / 任务结果页 / 管理配置（服务器·账号·模型），各一张 160 列宽屏帧 + 一张 80 列窄屏降级帧 |
| [`web/design-input.html`](web/design-input.html) ★ | **设计输入** — 背景 → 用户 → 场景 → 目标 → 能力 → 交互 → 状态 → 页面组件 → 原则 → 待验证 → 阶段规划 |
| [`web/demo.html`](web/demo.html) | **十幕交互演示** — 可自动播放或键盘切换，右侧标注每幕的设计 Pattern 与"哇点" |
| [`web/index.html`](web/index.html) | **产品规范单页** — 设计系统 + 渲染分层 + Pattern 库 + 场景 PRD 的整合版（评审用） |
| [`web/competitive-analysis.html`](web/competitive-analysis.html) | **TUI 竞品分析** — 7 竞品 × 22 触点 × 6 阶段旅程 |
| [`web/competitive-analysis-2.html`](web/competitive-analysis-2.html) | **TUI 竞品分析 · 第二部分** — AI Agent TUI 交互全景：10 竞品 × 12 交互域 × 48 触点（输入 / 配置 / 上下文 / 压缩 / 代码联动 / 图标 / 左树 / 对白 / 会话），证据窗口 2026-06→08 |
| [`web/visual-analysis.html`](web/visual-analysis.html) | **TUI 视觉风格分析** — 五个审美流派 + 皮肤生态 + 手法清单 |

想在浏览器里直接看，可以开启 GitHub Pages（Settings → Pages → Deploy from branch → `main` / `root`），之后访问 `https://<user>.github.io/<repo>/web/demo.html`。

<table>
<tr>
<td width="50%"><img src="assets/demo-report.png" alt="迁移报告"><br><sub><b>④ 出报告</b> — 文件风险热力用单一色阶顺序取档，一眼定位到 crypto.c</sub></td>
<td width="50%"><img src="assets/demo-review.png" alt="审改动"><br><sub><b>⑤ 审改动</b> — 每条改动都附知识库案例编号与 ARM 手册章节，可跳转验证</sub></td>
</tr>
<tr>
<td><img src="assets/demo-diagnose.png" alt="编译翻车"><br><sub><b>⑥ 编译翻车</b> — 失败不只报错，直接转入诊断并给修复方案</sub></td>
<td><img src="assets/spec-index.png" alt="规范单页"><br><sub><b>产品规范单页</b> — 设计系统与 Pattern 库的整合版</sub></td>
</tr>
</table>

---

## 目录结构

```
.
├── README.md                        本文件
├── UI-SPEC.md                       跨仓交付的全局 UI 规范
├── pages/                           跨仓交付的页面单文件设计合同
│   └── _TEMPLATE.md                 页面详情模板
├── docs/                            UI 研究与源规范（Markdown）
│   ├── DESIGN-INPUT.md              设计输入：设计依据的唯一入口 ★
│   ├── OVERVIEW.md                  产品定位 · 愿景 · 用户角色 · 信息架构
│   ├── PRD.md                       六大核心场景需求
│   ├── UX-SPEC.md                   布局 · 交互模型 · 命令体系 · 快捷键
│   ├── PATTERN.md                   交互 Pattern 库 P01–P29
│   ├── COMPONENT.md                 图表原语与组件规范
│   ├── VISUAL.md                    视觉系统：PTO Design System → TUI token 翻译 ★
│   ├── JOURNEY.md                   六阶段用户旅程 · Demo 故事线
│   ├── FRAMEWORK.md                 应用框架：MobaXterm 结构 × PTO 分割
│   ├── TUI-CAPABILITY.md            能力基线 · 渲染分层 T0–T5 · 框架选型
│   ├── COMPETITIVE-ANALYSIS.md      竞品分析（Markdown 版）
│   └── DEMO-WIREFRAME.md            四大 Demo 的 ASCII 交互稿
├── web/                             可交互 HTML（自包含单文件）
├── tools/                           字符帧与页面生成器（screens.py 带宽度断言）
└── assets/                          README 用截图
```

`docs/VISUAL.md` 是整套里最厚的一份（570+ 行），也是最值得先读的——所有视觉决策的推导过程和被推翻的方案都记在里面。

---

## 技术栈

```
        Kunpeng DevKit AI（原生 TUI）
                 │
   PTO Design System（529 tokens · Dark-first）   ← docs/VISUAL.md
                 │
   React 19 + OpenTUI 0.5.1（组件与渲染底座）
                 │
   TypeScript 5.9 + Bun（开发与构建）
                 │
   DevKit Intelligence（MCP 工具）
   code_cpp_migrator · database_sql_migrator
   kunpeng_knowledge_base_search · profiler
```

框架选型结论：使用 **TypeScript 5.9、React 19、`@opentui/core` 0.5.1、`@opentui/react` 0.5.1 和 Bun**。

---

## 几条核心结论

这套文档里最值得单独拎出来的判断：

**Chrome 层 vs Canvas 层——结构用组件，数据用字符。** TUI 不等于"全屏都用字符拼"。框架、侧栏、标签页、输入框这些**结构性元素是真 UI 组件**，有状态层、有焦点环、有选中态；只有承载数据的画布区才回到字符渲染。这条是整套设计的分界线，早期版本没分清，导致侧栏只是一堆没有状态的文本行。

**渲染分层 T0–T5。** 从纯文本、块字符、Braille（2×4 = 8 倍密度）、真彩热力、交互，一直到终端图形协议（Kitty / Sixel / iTerm2）。每一档都要有明确的降级路径——同一个标识在 T5 走光栅、在 T1 走半块像素。

**颜色三分工。** Kunpeng 红 `#ED1C24` 只做身份（标识、NEW 标），品牌蓝 `#0077FF` 只做交互（选中、焦点、当前推荐动作），错误红 `#FF4B7B` 只做语义。判据：**看到红色时，该想到"华为鲲鹏"还是"出事了"？** 两种含义同屏出现即违规。

**强调色配额：蓝 = 当前对象，或当前唯一推荐的动作。** 其余一律中性。第一版把蓝铺到十几处，结果蓝不再指向任何东西。评审判据：遮住所有蓝色，还能说清"我现在选中的是什么"吗？能，说明蓝铺多了。

**先问"终端画得出来吗"。** 高斯模糊、自由定位、亚像素粒子——这些做出来好看但实现不了的效果一律不要，否则设计稿和实现之间会留一道永远填不平的沟。启动页因此重做过一轮：辉光换成 bloom（大半径低透明度，不能有小半径层，否则会把点阵字体的直角糊掉），背景换成字符半调场，动效换成逐帧改写字符的明灭光点。

**行业最弱环节是"审查与决策"。** 竞品分析里跑完 7 个产品 × 22 个触点后，情绪最低点落在人审查 AI 改动的那一步——**没有一个产品做到 hunk 级的接受/拒绝**。这是本产品最大的机会点。

---

## 设计系统来源

视觉继承 **PTO Design System 4.1**（529 tokens · Dark-first · Inter + JetBrains Mono），定位是技术、克制、精确——对标 Cursor / Warp / Resend，而非消费级仪表盘。

`docs/VISUAL.md` 记录了完整的 web → terminal token 翻译：六级表面、四级前景透明度预合成为实色、状态叠加层预合成、五档 highlight ramp 的顺序 vs 分类纪律、以及为什么品牌蓝会和原色板里的 copy-blue 撞色（色相差 7°，最后退役了 copy-blue 并重建了域色映射）。

---

## 状态与后续

当前是 **概念设计（Concept Design）** 阶段，尚未进入实现。文档中已明确标注的待验证项：

- OpenTUI 0.5.1 在宽屏、窄屏及 SSH 低带宽场景下的局部重绘性能
- 160×50 宽屏与 58×32 窄屏布局的可用性及降级策略
- 终端图形协议（T5）在目标环境的实际可用比例
- Braille 密度渲染在中文等宽字体下的对齐表现

欢迎以 Issue 形式讨论。文档中所有被推翻的方案都保留了推翻理由，改动前建议先读一眼相关章节，避免重复踩坑。

---

## 授权

内部设计资料，授权方式待定。Kunpeng 标识及华为品牌色版权归华为技术有限公司所有，本仓库仅在设计示意中引用。
