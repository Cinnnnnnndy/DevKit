# 项目 Context

## 项目定位

将 Kunpeng DevKit AI 的 Web 交互设计稿逐步开发成一个原生 Python TUI 应用。

当前阶段包含 Launch 开场页面与 `/chart` 性能诊断工作区。Chart 工作区使用统一的 Mock Profiling Session 演示迁移后性能回退的定位流程，后续再接入真实采集器与 DevKit 工具。

项目目录：

```
/Users/yin/DevKit/kunpeng-devkit-ai-tui/demo/python-textual
```

原始 Web 设计稿：

```
/Users/yin/DevKit/kunpeng-devkit-ai-tui/web/demo.html
```

视觉参考：

```
/Users/yin/DevKit/kunpeng-devkit-ai-tui/docs/VISUAL.md
```

## 技术栈

- Python 3.12
- Textual 8.2.8
- Rich
- uv：依赖与运行管理
- TCSS：Textual 样式系统
- Hatchling：项目构建后端

## 主要文件

```
kunpeng-devkit-ai-tui/
├── devkitai.py          # 应用入口、Launch 页面、背景动画及交互
├── devkitai.tcss        # TUI 页面布局与视觉样式
├── pyproject.toml       # Python 项目配置和依赖
├── uv.lock              # 锁定依赖版本
├── README.md            # 启动和使用说明
├── web/demo.html        # 原始 Web 设计稿
├── assets/
│   └── demo-splash.png  # Launch 视觉参考
└── docs/
    └── VISUAL.md        # 视觉规范和设计决策
```

## 启动方式

```bash
cd /Users/yin/DevKit/kunpeng-devkit-ai-tui/demo/python-textual
uv sync
uv run devkitai
```

如果终端环境设置了 NO_COLOR，可以这样启动：

```bash
env -u NO_COLOR uv run devkitai
```

快捷键：

- Ctrl+P：打开 Textual 命令面板
- Esc：清空输入框
- Ctrl+Q：退出
- Enter：提交任务
- 点击建议按钮：将建议内容写入输入框

## 当前已实现

### Launch 页面

- 页面在终端中水平、垂直居中
- Kunpeng 双色字符 Logo
- KUNPENG DEVKIT AI 五行点阵字标
- 产品能力徽章
- 五行启动状态日志
- 任务输入框
- 三个任务建议按钮
- 提交后的反馈和通知
- 输入框自动聚焦
- Textual 命令面板

### Logo

Logo 已根据 web/demo.html 中的原始字符定义逐行还原：

- 13 行字符结构
- 品牌红：#ED1C24
- 浅灰部分：#C9C9C9
- 红灰斜向穿插
- 36 列 Logo 容器，避免裁切

### 字标

字标使用五行点阵字体算法生成，两行左对齐：

```
KUNPENG
DEVKIT AI
```

- 字形按列等比例横向拉伸 2 倍（`block_word(stretch=2)`）
- 字母间距保持 1 格，DEVKIT 与 AI 之间 3 格，两行之间 1 空行
- 行宽：KUNPENG 76 格，DEVKIT AI 89 格
- 统一使用白色（`#f4f4f4`）
- Logo 与字标同框垂直居中，字标 `margin-top: 2` 使 Logo 相对字标高 2 行

### 任务输入框

- `round` 圆角边框（Textual 内置），无背景填充
- 默认态：白色（`#f4f4f4`）边框；聚焦态：`#009aff` 边框
- 高 5 格、上下各 1 格 padding，内容区 1 格
- 外间距 `margin: 2 0`：与上方日志间距 3 格、下方建议区间距 2 格

### 背景

背景不是图片，而是 Textual 实时渲染的字符半调场：

- 使用 `· - +` 等字符
- 确定性哈希生成基础密度，不会整屏随机抖动
- 两级值噪声产生不规则团块
- 中心区域保持干净
- 外围字符逐渐加密
- 少量外围光点快速明灭
- 光点随机取色自 `#01a7ba / #5f3cff / #ab43ab`，每个光点在其生命周期内固定一色
- 动画刷新率约 24 FPS
- 单帧通常只改变几十个字符格

这套实现对应 Web Demo 的：静态团块底图 + 外圈短生命周期光点。

## 页面结构

```
DevKitAI
├── HalftoneField
│   ├── 确定性字符密度图
│   └── 外围 Spark 动画
└── LaunchScreen
    ├── Identity
    │   ├── Kunpeng Logo
    │   └── KUNPENG DEVKIT AI
    ├── Badges
    ├── ContentRow  Boot Log
    ├── ContentRow  Task Input
    ├── Suggestions
    └── ContentRow  Launch Feedback

ContentRow 是 width:100% 的横向居中行：Textual 中 Vertical 的
align:center 只会把窄子控件钉到最宽子控件的左缘，因此 Boot Log、
Task Input、Launch Feedback 各包一层 ContentRow 实现独立水平居中；
Suggestions 本身是横向容器，去掉 max-width 后内部居中即可。
```

## 关键实现约束

- Textual 8.2.8 的 TCSS 不支持 CSS @media。
- 所有视觉内容都落在终端字符格中。
- Textual 的透明控件仍然占据单元格，因此背景通过密度函数提前留出中心区域，避免出现矩形切边。
- 字标和 Logo 使用 Rich/Textual 文本渲染，没有使用位图。
- 当前提交任务只显示反馈，尚未接入真实 AI 或 DevKit 工作流。

## 已完成验证

标准测试终端尺寸：

```
156 × 48
```

已经验证：

- 应用正常挂载
- 页面居中
- Logo 未裁切
- 字标未错位
- 输入框自动聚焦
- 建议按钮可以填充输入框
- Enter 可以提交任务
- 背景只有局部字符变化
- Python 编译检查通过
- git diff --check 通过

## 后续开发建议

推荐按以下顺序继续：

1. 将 Launch 提交接入任务会话。
2. 增加 Plan 页面，展示 AI 执行计划。
3. 增加左侧任务和工具 Dock。
4. 增加工作区 Tabs。
5. 接入真实 MCP/DevKit 工具状态。
6. 实现迁移、编译、诊断和优化页面。
7. 将页面切换改成 Textual Screen 或 ContentSwitcher 架构。

当前启动页代码集中在 `DevKit/kunpeng-devkit-ai-tui/demo/python-textual/devkitai.py`，样式集中在 `DevKit/kunpeng-devkit-ai-tui/demo/python-textual/devkitai.tcss`。

## 方案 A：Chart Workspace 详细规格

### 产品目标

`/chart` 不是图表原语陈列页，而是一段可以操作的开发者性能诊断 Demo。全部视图必须解释同一次性能事件，并通过选择、时间游标和对象高亮建立上下文连续性。

本阶段的 Demo 问题定义：

```text
Target      Kunpeng ARM64 · 64 cores · 4 NUMA nodes
Service     llama-inference
Build       migration/candidate-42
Window      14:32:00 – 14:37:00
Incident    P99 latency regression +37%
Root cause  worker 跨 NUMA 调度导致 remote-memory 上升
```

开发者进入工作区后应能依次回答：

1. 哪个服务指标发生了回退？
2. 回退发生在哪个时间窗口？
3. CPU、NUMA 和内存访问之间有什么相关性？
4. 哪个函数、算子和请求 Span 对回退贡献最大？
5. 下一步应该采取什么优化动作？

### 信息架构

Tabs 固定为：

```text
Overview → CPU → NUMA → Flame → Trace → Operators
```

- Overview：诊断摘要，包含 KPI、趋势、核心热力图、瓶颈排名和事件列表。
- CPU：总利用率历史、user/system/iowait 分解、核心快照和线程迁移信息。
- NUMA：节点带宽、Local/Remote 比例、访问矩阵和线程绑定异常。
- Flame：从调用树数据计算宽度的火焰图，支持栈选择与逐层检查。
- Trace：一次慢请求的多泳道时间线，展示 Host 线程、CPU/NUMA 实例、NPU stream、HBM/DDR/MTE；不是四条资源聚合带。
- Operators：可选择、可排序的算子排行，包含耗时、内存、bound 类型和微型趋势。

### 统一数据模型

所有页面必须读取同一个 `MockProfilerSession`，不允许为单个 Tab 单独编造互不关联的静态文案。

```text
MockProfilerSession
├── timestamps[]
├── latency_p99[] / throughput[]
├── cpu_total[] / cpu_user[] / cpu_system[] / cpu_iowait[]
├── remote_numa[] / node_utilization[][]
├── core_utilization[][]
├── events[]
├── flame_nodes[]
├── trace_spans[]
└── operators[]
```

关键关联：14:34:20 后发生 worker migration，remote NUMA 从约 5% 升至 21%，随后 CPU iowait 与 P99 同步升高；`attention_fwd → load_qkv` 是主要 memory-bound 路径，Trace 中同一请求出现 HBM wait。

### 共享交互状态

工作区维护共享状态：

```text
cursor_index       当前采样点
cursor_locked      鼠标点击后是否锁定
selected_core      当前核心
selected_numa      当前 NUMA node
selected_span      当前 Trace span
selected_operator  当前算子
paused             是否暂停 Mock 播放
```

时间型图表的竖向游标必须联动：

- 鼠标移动：游标跟随并显示该采样点的指标。
- 单击：锁定/解除锁定游标。
- `← / →`：逐采样点移动并锁定。
- `Space`：暂停/恢复 Mock 播放。
- `R`：回到最新采样点。
- `Enter`：检查当前选中对象。
- `Esc`：退出局部选择；没有局部选择时返回 Launch。

终端字符限制下，游标使用贯穿绘图区的 `│` 或高亮列表示；不依赖像素级浮层。

### Overview 布局

Overview 在 156×48 基准终端下使用以下结构：

```text
┌ KPI strip: P99 / throughput / CPU / Remote NUMA ┐
├──────────────────────────────┬────────────────────┤
│ 4-track Braille history      │ 4×16 core heatmap  │
├──────────────┬───────────────┼────────────────────┤
│ Memory Gauge │ DDR dual area │ Hot-kernel race    │
└──────────────────────────────┴────────────────────┘
```

Overview 首屏必须至少出现一张趋势图和一张热力图，禁止仅使用表格或纯文本摘要。

### 图表原语落位

`#prim` 中定义的原语必须变成真实 profiling 证据，不作为装饰性图例复刻：

- 多核热力网格：Overview 与 CPU 页显示 64 核瞬时利用率，固定为 4 个 NUMA 行、每行 16 核；同一条 accum-orange 色阶编码强度，AI 热点使用独立 danger 描边。
- 分段渐变 Gauge：Overview 与 NUMA 页显示 64 GiB 的 used / cached / KV cache / free 构成；分段颜色和数值标签同时存在。
- 双向面积图：NUMA 页用上半区表示 local DDR read、下半区表示 remote DDR traffic，并与全局时间游标联动。
- Race：Overview 与 CPU 页显示当前时间窗内 attention、matmul、KV cache、layernorm 的热点份额排名；迁移事件之后 `attention_fwd` 必须超过 `matmul_4096`，形成可读的排名变化。
- Trace 密度带：Trace 页先显示 CPU / NPU / HBM / MTE 的分类泳道，色相编码资源身份、同色阶明度/字符密度编码忙闲；下方 span 列表负责精确对象选择。
- Braille 历史曲线：保留在 Overview 与 CPU，用于时间连续指标；不得用离散点阵冒充趋势。

这些图共享 `cursor_index`。鼠标 hover、点击锁定和左右键移动后，Gauge、面积图、Race、热力网格与密度带必须读取同一采样时刻。

### 实例数据密度下限

详情页不得用少量概念样例冒充真实工作集：

- Trace 至少 28 条实例 Lane，按 Host、CPU/NUMA、NPU、Memory 分组；默认窗口显示约 12–30 条，随终端高度变化，并可用上下键滚动选择。
- Flame 至少 18 个调用节点，包含多条分支和 8 层以上的深栈；选中节点始终保持在可见窗口。
- Operators 至少 16 个算子，窗口化呈现排行，选中项始终可见。
- CPU/NUMA 共享至少 32 个 worker 实例；每行包含 CPU、NUMA、迁移率、run queue 与 local/remote 状态。
- 64 核热力图必须保留每个核心的独立值，不能降为 4 个 NUMA 聚合块。

聚合图负责定位异常，实例列表负责解释异常；两层必须通过同一个 worker、算子或时间游标建立关联。

### 图表视觉语义

沿用 `web/index.html#prim` 的语义，而不是复制其示例数据：

- CPU 与通用时间序列：copy-blue。
- NUMA/内存带宽与热度：accum-orange 顺序色阶。
- NPU：l0a-violet。
- 告警或回退：danger pink/red。
- 当前选择背景：`#18293C`。
- 应用背景：`#101010`；方案 B 的 `#181822` 不覆盖方案 A。
- Braille 用于高分辨率趋势；Block 用于热力图、泳道和选择区域。

### Launch 布局修订

Launch 使用统一的 84 列主内容轴。Logo 可以更宽，但 Logo、状态、输入框和建议按钮组的几何中心必须一致。

建议区改为两层：第一层为弱化的“建议”标签，第二层为三个等宽按钮。按钮组自身居中，标签不参与按钮组宽度计算。垂直节奏按品牌、状态、主操作、次操作四组组织，避免所有间距近似相等。

### btop 借鉴边界

借鉴 btop 的：

- 高密度 Box Dashboard 与状态嵌入标题；
- 历史采样缓冲和自动缩放；
- Braille/Block 图形策略；
- 键盘与鼠标双通道操作；
- 列表选择、过滤、排序、暂停和详情检查；
- 随终端尺寸调整的信息密度。

不直接嵌入 btop 子进程，也不复制其系统监控页面。btop 自行管理终端绘制和输入循环，无法作为 Textual Widget 使用；本项目只将其交互原则转译为 Kunpeng profiling 语义。

### 验收标准

- 输入 `/chart` 后默认进入 Overview。
- Overview 同时展示 KPI、Braille 趋势、4×16 热力网格、分段 Gauge、双向面积图和 Race；事件通过趋势游标与各详情页联动读取。
- 六个 Tab 使用同一组 Mock 会话数据。
- Overview、CPU、NUMA、Trace 存在可见竖向时间游标。
- 鼠标移动和左右键可以改变游标，点击可以锁定。
- Flame、Trace 和 Operators 至少支持一项真实对象选择反馈。
- Trace ≥28 lanes、Flame ≥18 nodes、Operators ≥16 rows、Workers ≥32 rows，并支持窗口化选择。
- 建议按钮组相对输入框水平居中。
- Esc 能从 Chart 返回 Launch，原有 Launch 任务输入行为保持有效。
- 156×48 基准终端无关键内容裁切，并通过自动化交互测试。
