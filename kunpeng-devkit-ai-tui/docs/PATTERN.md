# Kunpeng DevKit AI — Pattern Library

> Version 0.2 · 12 个可复用交互 Pattern
> 参考：CodeArts CLI 研究库沉淀的 AI CLI 六阶段生命周期（启动 → 表达意图 → 等待执行 → 审查确认 → 多智能体协调 → 收尾总结）

Pattern 与生命周期映射：

```
启动        表达意图      等待执行        审查确认        收尾
 |            |             |               |             |
Env Check   P02 Plan     P01 Timeline    P05 Diff      P12 Summary
P09 Palette P08 KB       P11 Tool Exec   P10 Approval
                         P06/P07 Chart   P03 Evidence
                                         P04 Graph
```

---

## P01 · Agent Timeline Pattern

**场景**：所有 AI Agent 执行过程。解决"AI 现在做到哪一步"。

```
Agent Workflow
● Understand Request
│
● Scan Project              1.2s
│
● Search Knowledge Base     3 hits
│
▶ Generate Migration Patch  ⠹
│
○ Compile Verify
│
○ Performance Test
```

**规则**：每步可展开查看工具输入/输出；失败步 `✕` 红色并给出跳转；`Esc` 可中断当前步。

---

## P02 · AI Plan Pattern

**场景**：复杂任务开始前，AI 先出计划，不直接执行。

```
AI Plan
Goal: Migrate nginx x86 project → Kunpeng ARM64

1. Analyze dependency
2. Find incompatible API      (kunpeng_knowledge_base_search)
3. Generate patches           (code_cpp_migrator)
4. Build verify
5. Benchmark

Estimated: 5 tools · ~3 min

[E]xecute   [M]odify Plan   [C]ancel
```

**规则**：计划可编辑（增删步骤）；执行中计划变更需重新确认。

---

## P03 · Evidence Pattern

**核心理念**：工程领域 AI 不能只给答案，必须展示"为什么这么判断"。

```
Root Cause: Memory Alignment Issue

Evidence:
 [1] kernel.c:223            ← 代码行，Enter 跳转
 [2] runtime.log: "unaligned access at 0x7f3a…"
 [3] ARM Architecture Reference Manual §B2.5

Confidence  █████████░ 91%
```

**规则**：每条证据可跳转源头；置信度 < 70% 时禁用一键 Apply，只允许 Review。

---

## P04 · Diagnosis Graph Pattern

**场景**：Crash / 编译失败 / 性能瓶颈的因果链路。

```
app
 │
runtime.so
 │
memory allocator
 │
unaligned access   ◀ Root Cause
═══════════════
Fix: replace malloc → aligned_alloc
```

**节点类型**：Problem / Evidence / Solution；根因节点高亮 + 双线标记；节点 Enter 下钻到对应观测值或代码。

---

## P05 · Diff Review Pattern

**场景**：AI 修改代码 / 配置 / 参数。

```
Migration Patch · src/memory.c        (2/12 files)

- _mm_pause();
+ asm volatile("yield");

Impact:  Performance +35% · Compatibility Fixed

[A]ccept  [E]dit  [R]eject  [Space] next file
```

**规则**：支持逐文件与批量；Accept 后进入 Build Verify 步；`/undo` 可整体回滚。

---

## P06 · Metric Visualization Pattern

CLI 图表标准（详见 COMPONENT.md）：

```
Bar        CPU  ████████░░ 80%
Ranking    kernel_A ██████████ 40%
           kernel_B ██████    25%
Sparkline  Latency ▂▃▅▇▆▃▂
Heatmap    main.c ███████  memory.c ██████████  util.c ██
```

**规则**：百分比必带 bar；排行榜默认 Top10 + "N more"；所有图表元素可选中下钻。

---

## P07 · Trace Pattern

**场景**：模型 / 算子 / Runtime 执行时序。

```
Execution Timeline           0ms ──────────── 100ms
CPU   ████████
GPU      ███████
NPU         █████████
         └─ matmul  attention  softmax
```

**交互**：`+/-` zoom、`f` filter、方向键 select、Enter 打开区间详情（对应 kernel 指标）。

---

## P08 · Knowledge Retrieval Pattern

**场景**：DevKit 知识库问答（也被其它 Agent 内部调用）。

```
Knowledge Agent
Q: How to replace SSE _mm_pause on ARM?

Retrieved:
 [1] ARM migration guide · 指令替换案例库
 [2] Optimization case #4471

A: Use `yield` instruction instead of `pause`.

[I]nsert to code   [O]pen source doc
```

**规则**：回答必须带 citation；citation 可跳转；可一键将答案落到当前代码上下文。

---

## P09 · Command Palette Pattern

`Ctrl+P` 全局唤起：

```
❯ mig▌
  /migrate         迁移工程
  /migrate-sql     SQL 迁移
  ↺ migrate nginx  (recent session)
```

**规则**：命令、最近会话、文件三类混合模糊搜索；上下键 + Enter。

---

## P10 · Approval Pattern

**场景**：AI 执行危险动作（改文件、装依赖、改配置）。

```
AI wants to: Modify 12 files
Risk: ▮▮▮ Medium        Changes: +320 −80

[Y] Apply   [R] Review each   [N] Cancel
```

**风险分级**：Low（只读/生成新文件）自动放行可配置；Medium（改现有文件）默认确认；High（删除/系统级）强制逐项 Review。

---

## P11 · Tool Execution Pattern

**场景**：Agent 调用 DevKit 工具（MCP）时的透明化展示。

```
Tool: code_cpp_migrator
In:   src/crypto.c (SSE scan)
⠼ running… 2.1s
Out:  3 incompatible instructions found
```

**规则**：工具名 / 输入摘要 / 耗时 / 结果摘要四要素必现；失败给 stderr 折叠块 + 重试按钮。

---

## P12 · Session Summary Pattern

**场景**：任务收尾（生命周期"收尾总结"阶段）。

```
Session Summary · migrate nginx
✓ 21 issues fixed   ⚠ 2 need manual review
Build: PASS         Benchmark: 100ms → 70ms (-30%)
Files: +6 modified  Tokens: 48k

[S]ave report   [N]ew task   [Q]uit
```

**规则**：自动生成可导出报告（md）；未完成项转为下次会话的待办。
