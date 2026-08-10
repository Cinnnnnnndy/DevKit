# 产品定位 · 愿景 · 用户角色 · 信息架构

> Version 0.9 · Status: Concept Design · 2026-08
> PTO Design System + Textual 渲染底座 + 鲲鹏 DevKit 工具链

---

## 1. 产品定位

**产品名称**：**Kunpeng DevKit AI**（原生 TUI 形态；二进制 `devkitai`）

**一句话定义**：面向开发者、芯片工程师和性能工程师的 **AI Native Terminal Engineering Workspace** —— 一个独立运行、全屏接管终端的**原生 TUI 应用**，将 AI Agent、DevKit 工具链与工程可视化能力融合在一起，直接跑在鲲鹏服务器上。

**不是什么**：
- 不是 CLI 命令集合（command → output → exit）
- 不是 IDE 里的终端面板或插件聊天框
- 不是聊天窗口套壳（Chat UI in terminal）
- 不是 IDE 替代品

## 1.1 产品形态：原生 TUI（最需先钉死的一条）

| 形态 | 代表 | 运行方式 | 能力边界 |
|---|---|---|---|
| CLI 工具 | `devkitai_cli`、`porting_workflow_cli` | 一次性进程，执行完退出 | 无状态、无布局、无实时 |
| IDE 插件 / 内嵌终端 | Cline + DevKit MCP（当前形态） | 寄生在 IDE 进程内 | 受宿主 UI 约束；必须先有 IDE |
| **原生 TUI 应用** | **本产品** | **独立常驻进程，全屏接管终端，自有事件循环** | **自主布局 / 状态 / 快捷键 / 渲染；直接跑在目标机器上** |

**为什么必须是原生 TUI**——DevKit AI 部署在鲲鹏 Linux 服务器上，工程师 SSH 上去工作。待迁移源码、编译器、性能计数器、NPU 驱动、DevKit 服务全在那台机器上。IDE 插件方案要本地装 IDE + 挂远程开发 + 文件同步，多一层延迟，性能采集尤其失真；原生 TUI 是 ssh 上去直接 run。

只有原生 TUI 才成立的四件事：① 与被观测对象同机采集；② SSH 即完整体验，本地零安装；③ 自主渲染权（braille / 真彩热力需直接控制终端缓冲）；④ 常驻状态（上下文水位、索引、实时曲线）。

由此产生的设计约束：键盘优先鼠标可选；不假设 IDE 存在（跳源码要内置预览）；低带宽友好（局部刷新、采样率降档）；终端能力运行时探测并降级；单二进制交付。

**本地与远程是同一个二进制、同一套体验**：上面讲的是生产场景（工程师 ssh 到鲲鹏机器干活）；但同一个 `devkitai` 也直接跑在本地开发机上做交叉编译迁移，**不连任何远端、零配置启动**——Demo 演示的正是这条本地路径。两种部署共用同一份渲染、同一套快捷键、同一个会话模型，差别只是被观测对象在本机还是在远端。这种"一个二进制两处都完整"恰恰是原生 TUI 独有的：CLI 两处都能跑但没有工作台，IDE 插件两处都别扭。

**与现有形态并存而非替代**：CLI 留给 CI/脚本，IDE 插件留给本地轻量编码，原生 TUI 面向"做迁移、诊断、调优"这个 DevKit 主战场。三者共用同一套 Agent Runtime 与 MCP 工具，差异只在壳。

**是什么**：

```
AI Agent  +  DevKit Tool Runtime  +  Engineering Visualization
   大脑           手               眼
```

**对标融合**：

| 参照物 | 借鉴什么 |
|---|---|
| OpenCode / OpenTUI | Agent Loop、会话交互、流式渲染节奏 |
| Cursor | AI 原生工程体验 |
| Datadog CLI | 可观测、Metric Explorer |
| Nvidia Nsight | 性能剖析、Trace |
| 鲲鹏 DevKit | 迁移 / 开发 / 诊断 / 调优专业工具链 |

**技术栈层次**：

```
        Kunpeng DevKit AI
             |
      PTO Design System（视觉 token · 见 VISUAL.md）
             |
      Textual / TCSS（渲染底座 · 见 TUI-CAPABILITY.md）
             |
      DevKit Intelligence（MCP 工具：code_cpp_migrator /
      database_sql_migrator / kunpeng_knowledge_base_search / profiler ...）
```

---

## 2. 产品愿景

传统 CLI：

```
Command → Output → Human Analysis → Manual Action
```

Kunpeng DevKit AI：

```
Intent → AI Agent → Analysis → Visualization → Suggestion → Action → Verification
```

核心体验：**用户描述目标，AI 理解上下文，自动调用 DevKit 工具，并通过终端可视化结果辅助人做决策。**

---

## 3. 用户角色

| 角色 | 关注点 | 高频 Workspace |
|---|---|---|
| Application Developer | 编译、调试、代码迁移、API 适配 | Migrate / Develop |
| Performance Engineer | 算子性能、CPU/NPU 利用率、内存瓶颈 | Optimize / Observe |
| System Engineer | 环境、日志、故障定位 | Diagnose / Observe |
| AI Engineer | 模型推理、算子优化、Benchmark | Optimize / Observe |
| DBA / 数据工程师 | SQL 迁移（Oracle → GoldenDB） | Migrate |

---

## 4. 信息架构（V2）

以鲲鹏 DevKit AI 现有能力为锚点，**迁移是第一核心场景**，加上开发、诊断、调优三条主线与两个横向能力（观测、知识库）：

```
                     Kunpeng DevKit AI
                             |
        ┌───────────┬────────┴───────┬────────────┐
        |           |                |            |
     Migrate     Develop         Diagnose      Optimize
        |           |                |            |
  x86→ARM64    Code Assist      Build失败      性能剖析
  C/C++迁移     Build/Debug      Crash定位      算子调优
  SQL迁移      知识增强编码      根因分析       模型推理优化
  构建脚本迁移
        └────────────┬───────────────┘
                     |
        ┌────────────┴────────────┐
        |                         |
     Observe（横向）          Knowledge（横向）
     系统/Trace/Metric        鲲鹏领域知识库检索
```

对应 DevKit AI 当前已落地能力：
- `kunpeng_knowledge_base_search` — x86→鲲鹏指令替换案例库、SQL 不兼容语法案例库
- `database_sql_migrator` — Oracle → GoldenDB 迁移
- `code_cpp_migrator` — C/C++ 及构建脚本（Makefile/Blade/Bazel）迁移
- REST API / MCP / CLI（devkitai_cli、porting_workflow_cli）三种形态

---

## 5. 文档结构

仓库分三块：`docs/` 是设计规范（Markdown），`web/` 是四份自包含的可交互 HTML，`assets/` 是 README 用的截图。各份文档的用途与推荐阅读顺序见 [`docs/README.md`](README.md)，仓库总览见根目录 [`README.md`](../README.md)。


## 设计系统

继承 **PTO Design System 4.1**（529 tokens · Dark-first · Inter + JetBrains Mono），
设计定位：技术、克制、精确——对标 Cursor · Warp · Resend，而非消费级仪表盘。
完整的 web→terminal token 翻译见 `VISUAL.md`。

## 技术选型

```
  Textual TUI Shell（主选）   ← 渲染 · 交互 · 布局；TCSS = PTO token 直译
        │  MCP / HTTP :8000
  Agent Runtime               ← Agent Loop · 会话 · 上下文 · 工具编排
        │
  DevKit Tools                ← 四个 MCP 工具 + profiler + 诊断器
```
