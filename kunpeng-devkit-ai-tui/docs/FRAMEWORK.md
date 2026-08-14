# Kunpeng DevKit AI — 应用框架

> Version 0.6 · MobaXterm 结构组织 × PTO 分割方法

---

## 1. 为什么需要这一层

三栏骨架（Explorer / Canvas / Console）够画单个场景，但撑不起"多工程 · 多任务 · 多面板"的真实工作台。本文档参照 **MobaXterm 的结构组织**（左侧竖向 Dock、中央多标签 + 分屏、跟随上下文的文件浏览器、底部状态栏），用 **PTO 的分割方法**（表面层级承担嵌套、边框强度承担层级、无阴影）把完整框架定下来。

## 2. 从 MobaXterm 借什么、不借什么

| MobaXterm 的做法 | 借鉴到 Kunpeng DevKit AI | 判断 |
|---|---|---|
| 左侧竖向标签条 Dock（Sessions / Tools / Macros / Sftp），可折叠 | **左 Dock：任务 / 工程 / 工具 / 知识库 / 历史**，竖向标签条 + 内容区，`Ctrl+B` 折叠为图标列 | 借 |
| 中央多标签会话区，支持横/竖/四宫格分屏 | **中央多任务标签 + 分屏**，直接兑现 P29 多任务与 P23 布局预设 | 借 |
| SFTP 面板「Follow terminal folder」——文件树跟随终端当前目录 | **工程树跟随 Agent 上下文**：Agent 在改哪个文件，左树就定位到哪 | 借 ★ |
| MultiExec：一次输入，广播到所有打开的会话 | **批量任务**：一条指令对多个工程同时执行（批量迁移扫描） | 借 |
| 底部状态栏常驻 | **底栏**：模式 / 模型 / 上下文水位 / 待处理任务（P15 · P20 · P29） | 借 |
| 顶部 Ribbon 大工具栏（十几个分组、上百个图标按钮） | **不借。** Ribbon 是鼠标时代的密度换发现性；本产品键盘优先，用 `Ctrl+P` 命令面板替代——发现性靠模糊搜索而非视觉罗列 | 不借 |
| 会话前必须先建 Session（填地址/协议/凭据） | **不借。** 本产品零配置启动，直接说需求即可；配置按 P27 用到才问 | 不借 |

## 3. 完整框架

```
┌ ▪ DevKit AI ───────────────────────────────── ⬡ →ARM64 · ● 就绪 ┐   ← Header
├─┬──────────────────┬────────────────────────────────────────────┤
│▮│TASKS             │ 1 migrate  2 optimize ⠹  3 diag  +         │  ← Tab Bar
│ │                  ├──────────────────────┬─────────────────────┤
│▯│● 1 migrate nginx │ Migration Report     │ src/crypto.c        │
│▯│▶ 2 optimize ⠹    │ Compat ████████░░ 82%│ - _mm_pause();      │
│▯│○ 3 diagnose      │ Critical 2  Warn 8   │ + asm("yield");     │
│▯│⚠ 4 order-svc ⏸   │                      │                     │
│ │──────────────────│ ├ SSE     ⚠ crypto.c │ Evidence            │
│ │PROJECT   ⇄ 跟随  │ ├ atomic  ⚠ memory.c │  [1] 案例库 #4471   │
│ │nginx/            │ └ Makefile ✓         │  [2] ARM ARM §B2.5  │
│ │ ├ src/           │                      │                     │
│ │ │  crypto.c ███  │                      │                     │
│ │ │  memory.c ██   │                      │                     │
│ │ └ conf/          │                      │                     │
│ ├──────────────────┼────────────────────────────────────────────┤
│ │TOOLS             │ Agent Console          [Ctrl+J]            │  ← Console
│ │✓ cpp_migrator    │ ● Scan project    1,204 files              │
│ │✓ knowledge_base  │ ● Search KB       3 hits                   │
│ │○ sql_migrator    │ ▶ Generate patch ⠹  cpp_migrator           │
├─┴──────────────────┴────────────────────────────────────────────┤
│ ❯ 让 crypto.c 也用 NEON 优化▌                                   │  ← Input
├─────────────────────────────────────────────────────────────────┤
│ [F1]Migrate  mode:auto  model:qwen  ctx:72%⚠  ⏸ 1 任务待配置    │  ← Status
└─────────────────────────────────────────────────────────────────┘
  ▲ Dock 标签条（竖排）：▮当前 ▯其它 —— Ctrl+B 折叠时只留这一列
```

## 4. 区域规格

| 区域 | 职责 | PTO 表面 | 边框 | 尺寸 | 折叠 |
|---|---|---|---|---|---|
| Header | 产品标识 · 目标架构 · 连接状态 | surface-2 | border-subtle 下边 | 1 行 | 常驻 |
| Dock 标签条 | 面板切换（竖排单字符） | surface-2 | border-subtle 右边 | 1 列 | 常驻 |
| Dock 内容 | TASKS / PROJECT / TOOLS / KB / HISTORY | background | border-subtle 分区 | 18–28 列 | `Ctrl+B` |
| Tab Bar | 任务标签 + 状态徽标 + 新建 | surface-2 | 当前页 border-strong | 1 行 | 单任务时隐藏 |
| Canvas A | 主内容（报告 / Trace / 图表） | background | 分隔 border-subtle | 剩余 | 常驻 |
| Canvas B / Inspector | 证据 · 源码 · 详情——始终承载"结论的依据" | background | border-subtle 左分隔 | 18–24 列 | `Ctrl+I` 收折 |
| Agent Console | 步骤流 / 工具调用 / 日志 | surface-1 | border-default 上边 | 3–12 行 | `Ctrl+J` 抽高 |
| Input | 自然语言 + `/命令` | surface-2 | focus 时 border-strong | 1–3 行 | 常驻 |
| Status | Workspace · 模式 · 模型 · 上下文 · 待处理 | surface-2 | border-subtle 上边 | 1 行 | 常驻 |

## 5. PTO 分割方法在 TUI 的四条落地规则

1. **嵌套用表面层，不用阴影**——外层 `background` → 面板 `surface-1` → 面板内表头/工具条 `surface-2` → hover `surface-3` → 选中 `surface-4`。**最多嵌两层**，第三层改用留白分隔而非再加一层底色。
2. **层级用边框强度**——同级区域分隔 `border-subtle`；跨职责区域（Console 与 Canvas 之间）`border-default`；当前焦点区域整圈升到 `border-strong`。焦点不靠颜色靠**边框强度 + 左侧 `▮` 标记**。
3. **圆角只给浮层**——框架内所有固定区域用直角 `┌┐└┘`（radius-sm/md）；只有浮层、模态、Palette 用圆角 `╭╮╰╯`（radius-lg）。**圆角在这套体系里等于"浮起"**。
4. **留白只取六档**——面板内边距 space-4（左右 2 列 / 上下 1 行）；面板之间 space-5（3 列）；大区块 space-6。**禁止裸数字 padding**。

## 6. 分屏规则

```
单屏      ┌───────────────┐   报告类、Trace 全宽、Landing
          └───────────────┘

左右分    ┌───────┬───────┐   主力形态：结论 ↔ 证据
          └───────┴───────┘   默认 60/40，可拖拽，比例随 Workspace 记忆

上下分    ┌───────────────┐   时序 ↔ 明细
          ├───────────────┤
          └───────────────┘

三分      ┌─────┬────┬────┐   仅 ≥160col；<160col 自动降级为左右分
          └─────┴────┴────┘   第三栏优先牺牲（折叠成 Inspector 条）
```

**硬规则：同屏最多 3 个 Canvas。** 终端行列有限，四宫格（MobaXterm 支持）在 TUI 里每格都会窄到读不了数据——宁可用标签页切换。分屏是为了**并置对比**（P22 联动的载体），不是为了塞更多东西。

## 7. Dock 面板

| 面板 | 内容 | 对应 Pattern | 快捷键 |
|---|---|---|---|
| TASKS | 并发任务列表 + 状态徽标 + 耗时；`⏸ 等待配置` 置顶 | P29 多任务 | `Alt+1..9` |
| PROJECT | 工程树 + 文件风险热力；**`⇄ 跟随` 开关：自动定位到 Agent 正在处理的文件** | P22 联动 | `Ctrl+E` |
| TOOLS | 已装 MCP 工具与状态；点击查看最近调用记录 | P11 · P17 | — |
| KB | 知识库检索入口与最近引用；可拖引用进 Canvas | P08 知识检索 | `Ctrl+K` |
| HISTORY | 历史会话，全文可搜；支持 fork 出新任务 | P20 上下文管理 | `Ctrl+H` |

> **`⇄ 跟随` 是这一节最值得实现的一个细节。** MobaXterm 的 SFTP 面板会跟随终端当前目录，省掉了用户反复手动定位。搬到这里就是：**Agent 改到哪个文件，左侧工程树就高亮定位到哪个文件，风险热力同步更新**。用户不需要在"AI 说它改了 crypto.c"和"我去树里找 crypto.c"之间做翻译。这条同时也是 P22 Linked Drill-down 在框架层的常驻体现——联动不只发生在用户点击时，也发生在 Agent 行动时。

## 8. 折叠降级链

```
≥160col  Dock + Canvas×3 + Inspector          全展开
140-159  Dock + Canvas×2 + Inspector 条        Inspector 收成 1 列
120-139  Dock + Canvas×2                       Inspector 隐藏，Ctrl+I 浮层调出
100-119  Dock 图标列 + Canvas×2                Dock 收成 1 列
 80-99   Dock 图标列 + Canvas×1                取消分屏
 <80     单栏 + Tab 切换                        Dock 转为浮层

高度不足时的收缩优先级：Console(3行底线) → Canvas → Tab Bar(单任务时隐藏)
Header / Input / Status 永不隐藏——它们是方向感的锚点
```

这一档只决定**给几个 Canvas、每个多宽**。每个 Canvas 里那张图怎么缩，是它的
**图元级对应**——见网页版「图元尺寸与排布」一节，规格与判决在
[`../app/devkitai/layout.py`](../app/devkitai/layout.py) 的下半部分
（`PRIMITIVES` / `chart_box()` / `fit_box()` / `shrink_order()`）。

两者必须对得上，否则会出现「整屏还在给栏、图元级已经全线拒绝画」的空栏，
所以放在同一个模块、由 `tests/test_layout.py` 同时压。对上之后浮出来一条
反直觉的结论：**全链路最窄的 Canvas 出现在最宽的终端上**——160 列三分屏的
第三栏只有 28 列（图元可用 24 列），比 40 列窄终端的单栏还要窄 12 列。
火焰图与泳道 Timeline 的最小宽度是 30 列，因此**三分屏时它们必须落在第一栏**。
