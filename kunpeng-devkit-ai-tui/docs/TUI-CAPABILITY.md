# Kunpeng DevKit AI — TUI 能力基线 / 渲染分层 / 框架选型

> Version 0.4 · 参照 btop、ratatui demo、FTXUI

---

## 1. TUI ≠ CLI

前面章节的 ASCII 稿仍停留在"能被 print 出来的东西"。TUI 拿到的是**全屏可寻址缓冲 + 事件循环**，能力集远大于 CLI。设计时必须主动消费这些能力，否则做出来的只是带框线的 CLI。

| 能力 | CLI | TUI | DevKit 场景应用 |
|---|---|---|---|
| 全屏可寻址缓冲 | 只能向下追加，刷屏 | alternate screen，任意坐标重绘 | 多面板常驻：左树 + 中报告 + 右指标同屏不滚动 |
| 亚字符分辨率 | 1 字符 = 1 像素 | Braille 2×4 = **8× 密度**；象限块 2×2 = 4× | 真折线/面积图：CPU 历史、算子 latency 曲线 |
| 高频局部重绘 | 无（重跑命令） | 局部 diff 刷新，可跑 500ms 级 | 实时 Trace、采集中的 Profiler、Agent 流式步骤 |
| 鼠标事件 | 无 | click / hover / drag / wheel | 点选算子块下钻、拖拽调分栏、滚轮缩放 Timeline |
| 焦点与滚动容器 | 无（靠 less 管道） | 独立滚动区、焦点环、Scrollbar | 万行日志、64 核进程表、长 Diff 各自独立滚动 |
| 浮层 / 模态 | 无 | overlay 覆盖，不破坏底层布局 | Command Palette、Approval 弹窗、模型切换器 |
| 24-bit 真彩 | 通常 8/16 色 | 真彩 + 背景色 | **颜色作为第三维**：核心热力网格、文件风险热力 |
| 可调分栏 | 无 | resizable split、布局预设 | 用户自定义工作区（诊断偏日志 / 调优偏图表） |
| 持久会话状态 | 进程退出即丢 | 常驻进程，跨命令状态 | 上下文水位、索引状态、多会话 Tab |

**设计准则**：每画一个页面，先问三个问题——① 这里能不能用 braille 提到 8× 密度？② 这里能不能用颜色承载一个额外维度？③ 这个元素能不能点、能不能滚、能不能拖？三个都答"否"的页面，说明还停在 CLI 思维。

---

## 2. 渲染分层 T0–T4

统一分五层，**高层必须能向低层降级**（SSH 老终端、CI 日志、不支持真彩的环境）。

| 层 | 技法 | 密度 | 适用图表 | 降级到 |
|---|---|---|---|---|
| T0 文本 | 纯字符 + 状态符号 | 1×1 | Timeline、Tree、列表、日志 | —（兼容底线） |
| T1 块字符 | ▁▂▃▅▇█ / 半块 / 象限 | 1×2 · 2×2 | Gauge、Sparkline、BarChart、LineGauge | T0 数字 + 百分比 |
| T2 Braille | ⠁⡀⣿ 点阵画布 | **2×4 = 8×** | 折线、面积、散点、双向流量图 | T1 Sparkline |
| T3 真彩热力 | bgcolor 承载数值 | 颜色 = 第三维 | 核心网格、风险热力、算子热力、Trace 密度 | T1 灰阶块字符 |
| T4 交互 | mouse + focus + scroll | — | zoom/select/drag/sort/hover | 纯键盘等价（必须全覆盖） |

**硬性要求**：T4 的每个鼠标操作都必须有键盘等价路径（无鼠标的 SSH 场景是 DevKit 主战场）。T3 在 `NO_COLOR` / 16 色终端下自动降级为 T1，语义不能丢。

---

## 3. 图表原语 v2（btop 级密度）

### ① Braille 历史曲线 · T2
CPU/NPU 利用率历史、算子 latency 趋势、内存增长。采样率随面板高度自适应（btop 的 2000ms 可调档位）。

```
┌cpu──kunpeng──────────────────────────21:02──2000ms─┐
│ ⠀⠀⠀⠀⠀⢀⣀⠀⠀⠀⠀⠀⠀⢀⣠⡀⠀⠀⠀⠀⠀⢀⣀⡀⠀⠀  Kunpeng 920 │
│ ⣠⣴⣾⣿⣷⣿⣿⣷⣦⣄⣠⣴⣾⣿⣿⣿⣷⣤⣀⣠⣴⣾⣿⣿⣷⣄  64C 2.6GHz │
└────────────────────────────────────────────────────┘
```

### ② 多核热力网格 · T3 · 鲲鹏特化
鲲鹏 920 多核（32/48/64C）+ NUMA 亲和性可视化——CLI 完全做不到、而对鲲鹏调优最关键的一张图。颜色承载利用率，位置承载拓扑，AI 在其上叠加热点标注。

```
64-core heatmap              ▁ idle  ▃ low  ▅ mid  █ hot
 0-15  █▇▅▃▂▁▁▂▃▅▇█▇▅▃▁   NUMA0 ██████░░ 78%
16-31  ▂▁▁▂▃▅▇█▇▅▃▂▁▁▁▂   NUMA1 ████░░░░ 44%
32-47  ▅▇█▇▅▃▂▁▁▂▃▅▇█▇▅   NUMA2 ███████░ 82%  ▚▚▚
48-63  ▁▁▂▃▅▇█▇▅▃▂▁▁▂▃▅   NUMA3 ███░░░░░ 31%
⚠ AI: core 34-38 持续 >80%，疑似跨 NUMA 内存访问
```

### ③ 分段渐变 Gauge · T1
内存构成（Weights / KV Cache / Activation）、显存、磁盘。一条 bar 表达多个量。

```
Memory  ██████████████████████░░░░░░░░  38.2 / 64 GiB
        used 22G   cached 12G  kv 4G  free 26G
```

### ④ 双向面积图 · T2
网络收发、PCIe/HBM 读写带宽、Host↔Device 拷贝。上下对称让方向差异一眼可见。

```
↑ up   ⣀⣠⣴⣶⣤⣀⣀⣠⣴⣿⣷⣦⣄⣀⣠⣴⣶⣤⣀   1.30 KiB/s
↓ down ⠉⠛⠿⣿⣿⠿⠛⠉⠙⠻⢿⡿⠟⠋⠉⠛⠿⠟⠉   346 B/s
```

### ⑤ 散点 + 坐标轴 Chart · T2
Roofline 图（compute vs memory bound）、batch-latency 曲线、量化前后精度-性能散点。

### ⑥ 可排序进程/算子表 · T4
算子排行、进程表、Issue 表、文件风险表。列头点击排序（`▾` 标记）、行选中反色、Enter 下钻。

```
┌kernels─filter▸──────────per-core─reverse─tree─▾ time─┐
│ Name           Calls   Avg      Total    Mem   Bound │
│ attention_fwd   1024   18.2ms   18.6s    2.1G  mem   │  ← 选中反色
│ matmul_4096      512   12.4ms    6.3s    1.4G  comp  │
└─────────────────────────▲▼ select  ↵ drill  / filter─┘
```

### ⑦ Trace 密度带 · T3
多泳道 Trace。颜色深浅承载利用率强度（不只是"有/无"），一眼看出气泡与瓶颈段。

### ⑧ 其它保留原语
Tabs · Scrollbar · LineGauge · Sparkline · Tree / Graph / Diff。

---

## 4. 框架选型

**关键前提**：DevKit AI 已通过 MCP over streamableHttp（:8000）暴露能力，TUI 本质是客户端。实现语言与 Agent Runtime 解耦，选型可纯按"渲染能力 + 团队栈 + 集成成本"决策。

| 维度 | Textual（Python） | OpenTUI（TypeScript） | FTXUI（C++17） |
|---|---|---|---|
| 生态位 | Textualize 出品，基于 Rich，社区最大 | **OpenCode 所用**，Zig 核心 + TS 绑定 | 无依赖 C++ 库 |
| **样式系统** | **TCSS —— CSS 子集，含变量、选择器、伪类、层** | 组件 style props（flexbox 式） | C++ 装饰器链式调用 |
| **设计 token 落地** | **原生主题系统**，变量可直接映射 PTO token | 需自建 token 层 | 需自建 token 层 |
| 内置组件 | DataTable / Tree / Tabs / Input / TextArea / Select / Switch / ProgressBar / Sparkline / Log / Markdown / Collapsible … | box / text / input / select / scrollbox / tabs（React·Solid 绑定） | button/input/menu/slider/dropdown/tab/window/resizable_split |
| **Command Palette** | **框架内置**（直接兑现 P09） | 需自建 | 需自建 |
| Canvas / Braille | Rich 提供渲染原语，braille 画布需薄封装 | 核心含缓冲级绘制 | Canvas DrawPoint / DrawBlock 双层 |
| 鼠标 / 动画 | ✓ 完整鼠标 + `animate()` 缓动 | ✓ | ✓ |
| Web 部署 | **textual-serve**：同一份代码跑进浏览器 | — | WebAssembly |
| 与 DevKit 工具链 | Python 生态贴近 AI/编译分析工具 | 需 IPC | 同进程直连 C/C++ |
| OpenCode 复用 | 低 | **高**（同栈） | 低 |

### 推荐：Textual 为主选，OpenTUI 为备选

决定性理由是**设计系统落地成本**——VISUAL.md 把 PTO token 体系完整翻译成了 TUI token，而 Textual 的 TCSS 是 CSS 子集、且有原生主题变量系统，**这套 token 可以近乎 1:1 写成 TCSS 变量文件**，Web 端与终端端共用同一份设计语言、同一套命名。换到 OpenTUI 或 FTXUI，都要先自建一层 token 系统再手工映射，设计系统的一致性靠人肉维护。

次要理由：Textual 内置 Command Palette 直接兑现 P09；`textual-serve` 让同一份代码能跑进浏览器，评审和文档嵌入零成本；DataTable / Tree / Tabs / Collapsible 覆盖了组件清单的大半。

**选 OpenTUI 的场景**：如果目标是**最大化复用 OpenCode 的 Agent Loop 与会话层**（而不只是通过 MCP 调用），同栈的 OpenTUI 是更短的路径——OpenCode 本身就跑在它上面，会话管理、流式渲染、工具调用展示都有现成实现可借鉴。代价是 PTO token 体系需自建映射层，braille 图表原语要自己封装。

> 注：OpenTUI 的组件清单与绘图 API 细节建议在选型评审前实测确认——本表基于公开信息整理，其具体版本能力可能已演进。

### 建议架构

```
  Textual TUI Shell   ← 渲染 T0–T4 · 交互 · 布局 · 快捷键
        │              TCSS 变量文件 = PTO token 直译
        │  MCP / HTTP :8000 · streamableHttp
  Agent Runtime       ← Agent Loop · 会话 · 上下文 · 工具编排
        │
  DevKit Tools        ← code_cpp_migrator · database_sql_migrator
                        sql_syntax_repair · kunpeng_knowledge_base_search
                        profiler · 诊断器
```

---

## 5. TUI 原生 Patterns（P21–P26）

依赖上述 TUI 增量能力，**在 CLI 里无法实现**。这是"这个产品必须是 TUI 而不是 CLI"的理由。

| Pattern | 依赖能力 | 说明 |
|---|---|---|
| P21 Live Canvas | 局部重绘 + Braille | 实时曲线，采样率档位可调（250ms/500ms/2s/5s），`space` 冻结读数 |
| P22 Linked Drill-down | 鼠标 + 多面板联动 | 选中任一视图元素，其它面板同步聚焦同一对象/时间窗：诊断结论 → 证据 → 观测值 → 源码四跳联动 |
| P23 Workspace Layout Preset | resizable split | 每个 Workspace 默认布局预设，F1–F4 切换，拖拽微调并记忆 |
| P24 Sortable / Filterable Table | 焦点 + 列头点击 | 列排序（`▾` 标记）、筛选表达式、多选批量操作 |
| P25 Non-destructive Overlay | 浮层缓冲 | 真浮层覆盖，关闭后底层布局与滚动位置完全不变（对比 P16 的 CLI 妥协方案） |
| P26 AI Annotation Layer | 真彩 + 图层叠加 | **最具差异化**：AI 判断作为图层叠加在数据可视化之上——热点描边、异常标色、瓶颈角标。让"AI 说了什么"和"数据长什么样"在同一视觉空间对齐 |

---

## 6. Phase 0：渲染底座先行

最有价值的 pattern（P21 Live Canvas、P26 AI Annotation、多核热力）全部依赖渲染底座。若先做业务 Demo 再补渲染，大概率退化成"带框线的 CLI"。

建议用两周先跑通三个原语：Braille 曲线 / 多核热力网格 / 可排序表 + MCP 客户端连 :8000，再往上叠场景。
