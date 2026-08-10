# Kunpeng DevKit AI — Component Library（CLI 组件规范）

> Version 0.2 · OpenDesign TUI 组件体系

---

## 1. Layout Components

### Main Shell

```
┌────────────────────────────┐
│ Header                     │
├───────────┬────────────────┤
│ Explorer  │ Workspace      │
├───────────┴────────────────┤
│ Agent Console              │
├────────────────────────────┤
│ Input Bar                  │
└────────────────────────────┘
```

### Panel / Card

```
╭ Migration ─────────╮   ┌──────────────┐
│ Score  82%         │   │ 内嵌块直角     │
╰────────────────────╯   └──────────────┘
```
主面板圆角、内嵌块直角；标题嵌入上边框。

---

## 2. 组件清单

| 组件 | 用途 | 关联 Pattern |
|---|---|---|
| Agent Timeline | 任务状态流 | P01 |
| Plan Card | 任务规划 | P02 |
| Evidence List | 证据 + 置信度 | P03 |
| Diagnosis Graph | 因果链路 | P04 |
| Diff View | 代码/配置变更 | P05 |
| Metric Bar / Ranking / Sparkline / Heatmap | 指标 | P06 |
| Trace View | 时序泳道 | P07 |
| Knowledge Card | 检索问答 | P08 |
| Command Palette | 命令入口 | P09 |
| Approval Bar | 确认操作 | P10 |
| Tool Card | 工具调用 | P11 |
| Summary Card | 会话总结 | P12 |
| Tree View | 工程/模型结构 | — |
| Graph View | 依赖/调用关系 | — |
| Log View | 原始日志（折叠） | — |
| Status Card | 设备/环境状态 | — |

---

## 3. 图表组件规格

### 3.1 Metric Bar

```
CPU  ████████░░  80%
```
- 填充 `█`，底 `░`，宽度 10/20 两档
- 阈值着色：<60% accent · 60–85% warn · >85% error（可按指标语义反转）
- 数值右对齐，恒带单位

### 3.2 Ranking Bar（排行）

```
Top Bottleneck
kernel_A  ██████████  42%   12.4ms
kernel_B  ██████      25%    7.4ms
memcpy    ███         15%    4.4ms
          … 4 more
```
- 默认 Top10，尾部 "N more" 可展开
- 行可选中（反色），Enter 下钻

### 3.3 Sparkline

```
Latency  ▂▃▅▇▆▃▂  avg 8.2ms
```
- 字符集 `▁▂▃▄▅▆▇█`，窗口 30/60 点
- 异常点用 error 色标出

### 3.4 Timeline（泳道）

```
        0ms                      100ms
CPU     ████████
GPU        ███████
NPU           █████████
```
- 每泳道一行；块可命名；支持 zoom/filter/select
- 选中块高亮并在下方吐出该区间指标

### 3.5 Tree

```
Model
 ├ Layer1
 │  └ Attention   ⚠
 └ Layer2
```
- `├ │ └` 制图符；状态符号后缀；`h/l` 折叠展开

### 3.6 Graph（依赖/因果）

```
app
 │
runtime ──── libcrypto
 │
driver
```
- 纵向为主流向；横向为关联；根因/焦点节点反色

### 3.7 Diff

```
- _mm_pause();
+ asm volatile("yield");
```
- `-` error 色 / `+` ok 色；hunk 头 dim；行号列可开关

### 3.8 Heatmap（文件风险）

```
src/
 main.c    ███████
 memory.c  ██████████   ◀ highest risk
 util.c    ██
```

### 3.9 Score Ring（终端替代形态）

```
Compatibility  ████████░░  82%   Critical 2 · Warn 8 · Fixed 21
```
圆环在 TUI 中降级为 bar + 分级计数。

### 3.10 Before / After

```
Latency   120ms  →  70ms   (−42%)
          ██████████  ██████
```

---

## 4. 组件状态规范

所有交互组件必须定义 5 态：`default / focused（反色或 accent 边框） / selected / disabled（dim） / error`。
所有异步组件必须定义 3 态：`loading（spinner） / loaded / failed（✕ + 重试）`。
