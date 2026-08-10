# Kunpeng DevKit AI — PRD（核心场景需求）

> Version 0.2 · 四大主线场景 + 两个横向能力

---

## Scenario 01 · AI Migration Agent ⭐ 第一核心场景

### 用户目标
快速完成 x86 → 鲲鹏 ARM64 迁移（C/C++ 源码、构建脚本、SQL）。

### User Story
> 作为开发者，我希望导入已有工程，AI 自动分析不兼容点，生成迁移补丁，并完成编译验证与性能确认。

### 能力锚点（DevKit AI 现有）
- `code_cpp_migrator`：C/C++ 兼容性扫描 + 代码改写（含 Makefile/Blade/Bazel）
- `database_sql_migrator`：Oracle → GoldenDB 不兼容语法识别与适配
- `kunpeng_knowledge_base_search`：指令替换案例库辅助决策

### Workflow

```
Project Import → Architecture Scan → Compatibility Analysis
      → AI Patch → Build Verify → Performance Check
```

### 页面清单

| 页面 | 关键内容 | 关键组件 |
|---|---|---|
| P1 Migration Workspace | 项目路径、源/目标架构、启动分析 | Form Card |
| P2 迁移分析总览 | 兼容性评分、Issue 分级、文件风险热力 | Score Ring、Issue Tree、File Heatmap |
| P3 Agent 执行流 | 扫描→识别→补丁→验证 步骤流 | Agent Timeline、Tool Card |
| P4 Patch Review | 逐文件 Diff、影响评估、批量接受 | Diff View、Approval Bar |
| P5 验证报告 | 编译结果、Benchmark 前后对比 | Metric Bar、Before/After |

### 验收指标（Demo 级）
- 从导入到出报告 ≤ 3 步操作
- 每个不兼容点均有 Evidence（文件行号 + 知识库依据）
- Patch 必须经用户确认（Approval Pattern）后落盘

---

## Scenario 02 · AI Develop（开发助手）

### 用户目标
面向鲲鹏生态的编码 / 理解 / 修改 / 构建 / 调试。不止写代码，而是**架构感知的开发助手**。

### User Story
> "Add ARM optimized memcpy" —— AI 检索知识库、找到已有实现、生成 NEON 版本代码、跑 Benchmark 给出前后对比。

### 关键差异
- 架构知识图谱：识别 x86 SIMD → 给出 ARM NEON 等价物
- 编码闭环：生成 → 编译 → 测试 → Benchmark 一体

### 页面清单

| 页面 | 关键内容 | 关键组件 |
|---|---|---|
| AI Coding Session | 对话 + Agent 步骤 + 文件变更 | Chat Panel、Agent Timeline、Diff |
| Code Intelligence | 工程结构、调用关系、算子分布 | Tree、Dependency Graph、Call Graph |
| Arch Insight | 指令集知识提示（x86↔ARM 映射） | Knowledge Card |

---

## Scenario 03 · AI Diagnose（智能诊断）

### 用户目标
"哪里有问题" → AI 自动定位根因。覆盖编译失败、Runtime Crash、环境问题。

### 输入形态

```
$ devkitai diagnose build.log
$ devkitai diagnose ./app
$ devkitai diagnose core.dump
```

### AI 流程

```
Collect → Analyze → Root Cause → Evidence → Suggestion → Fix → Verify
```

### 子场景

**3.1 编译失败诊断**：错误卡片 + 根因树（置信度）+ 关联文件 + [Apply Fix]

**3.2 Runtime Crash 诊断**：Signal、Stack Tree、根因（如 memory alignment）、置信度条、修复建议

**3.3 环境一键体检**：OS / Compiler / Driver / SDK 检查，⚠ 项给 AI Fix

### 硬性要求（Evidence Pattern）
每个诊断结论必须附：证据列表（日志行、代码行、架构文档引用）+ 置信度。**工程领域 AI 不能只给答案。**

### 页面清单

| 页面 | 关键组件 |
|---|---|
| Diagnosis Input | Command / 拖入日志 |
| Root Cause View | Diagnosis Graph（问题链路图）、Confidence Bar |
| Fix Proposal | Diff View、Approval Bar |

---

## Scenario 04 · AI Optimize（性能调优）

### 用户目标
发现瓶颈 → 定位算子/热点 → 生成优化方案 → Benchmark 验证。

### 分析对象层次

```
Application → Model → Operator → Kernel
```

### 子场景

**4.1 应用/训练性能剖析**：Timeline（CPU/GPU/NPU 泳道）、Latency Breakdown 排行

**4.2 算子优化**：单算子卡片（compute-bound / memory-bound）、AI 建议（tiling / fusion / mixed precision）、预期收益

**4.3 模型推理优化**：内存构成（Weights / KV Cache）、量化建议（INT8）、Layer Timeline

### 核心页面

```
Latency Breakdown          AI Proposal
kernel_A █████████ 42%     ✓ Enable fusion
kernel_B █████    25%      ✓ INT8 quantization
memcpy   ███      15%      Expected: 120ms → 70ms (-42%)
```

### 验收指标
- 每条优化建议必须带预期收益（量化数字）
- 优化前后 Benchmark 对比自动生成

---

## Scenario 05 · Observe（横向能力：观测）

### 用户目标
实时理解系统状态；诊断/调优场景的"眼睛"——问题呈现必须能下钻到对应观测对象的值。

### 观测对象

```
Infrastructure: CPU / Memory / NPU / Network / Disk
Runtime:        Kernel / Operator / Task / Process
```

### 页面清单

| 页面 | 类比 | 关键组件 |
|---|---|---|
| System Dashboard | CLI 版 Grafana | Metric Bar、Sparkline、Status Card |
| AI Trace Viewer | Chrome Trace | Timeline（多泳道、zoom/filter/select） |
| Metric Explorer | Datadog | 自然语言查询 → Ranking Chart |

---

## Scenario 06 · Knowledge Agent（横向能力：知识库）

### 定位
DevKit AI 特有能力，**不是普通 RAG**，独立成 Workspace，同时作为其它 Agent 的内部工具被调用。

### 案例库
- x86 → 鲲鹏架构指令替换案例库
- SQL 不兼容语法迁移案例库（Oracle → GoldenDB）

### 交互

```
Question: "x86 pause instruction on ARM replacement?"
Retrieved: [1] ARM migration guide  [2] Instruction mapping case
Answer:   Use `yield` instruction instead of `pause`
          ↳ [Insert to code] [Open source doc]
```

引用必须可溯源、可跳转（Retrieval → Citation → Action）。

---

## Demo 优先级（Phase 1）

| 优先级 | Demo | 理由 |
|---|---|---|
| P0 | AI Migration Agent | DevKit AI 当前最明确的差异点，能力已落地 |
| P1 | AI Performance Optimize | 最适合 CLI 图表表达，视觉冲击强 |
| P1 | AI Diagnose | Root Cause Graph + Evidence 最能体现"专家感" |
| P2 | Observe Dashboard | 支撑前三者的下钻，可后置 |

Phase 2：Agent Runtime（MCP 工具调用展示、多 Agent 协作、Context/Memory 管理）
Phase 3：插件生态
