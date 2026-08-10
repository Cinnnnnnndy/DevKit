# Kunpeng DevKit AI — UX SPEC

> Version 0.2 · 布局 / 交互模型 / 命令体系 / 快捷键 / 视觉语言

---

## 1. 总体布局（OpenCode 魔改三栏结构）

```
┌────────────────────────────────────────────────┐
│ Header   DevKit AI v26.0        ⬡ NPU:8  ● OK  │
├────────────┬───────────────────────────────────┤
│ Explorer   │                                   │
│            │                                   │
│ ▸ Migrate  │          Main Canvas              │
│ ▸ Develop  │   （报告 / Trace / Diff / 图表）    │
│ ▸ Diagnose │                                   │
│ ▸ Optimize │                                   │
│ ▸ Observe  │                                   │
├────────────┴───────────────────────────────────┤
│ Agent Console  ▶ analyzing trace… [tool:profiler]│
├────────────────────────────────────────────────┤
│ ❯ input                             tokens 12k │
└────────────────────────────────────────────────┘
```

**区域职责**：

| 区域 | 职责 | 常驻性 |
|---|---|---|
| Header | 版本、设备状态、连接状态 | 常驻 |
| Explorer | Workspace 切换、工程树、会话列表 | 可折叠（`Ctrl+B`） |
| Main Canvas | 当前任务的可视化主体 | 常驻，支持分屏 |
| Agent Console | Agent 步骤流 / 工具调用 / 日志 | 可抽高（`Ctrl+J`） |
| Input Bar | 自然语言 + `/命令` 双模输入 | 常驻 |

**响应式规则**（终端宽度）：
- ≥ 120 col：三栏全开
- 80–119 col：Explorer 折叠为图标列
- < 80 col：单栏 + Tab 切换

---

## 2. 核心交互循环

不采用 `Command → Output → Exit`，采用 Agent 生命周期：

```
Intent → Context Understanding → Plan → Tool Execution
      → Visualization → Decision → Action → Verification
```

对应界面状态机：

```
┌────────┐   ┌─────────┐   ┌─────────┐   ┌────────┐
│ Intent │ → │ Analyze │ → │ Execute │ → │ Verify │
└────────┘   └─────────┘   └─────────┘   └────────┘
  输入栏      Plan Card     Agent        Report +
             （可修改）     Timeline      Before/After
```

**关键原则**：
1. 复杂任务先出 Plan，不直接执行（Plan Pattern）
2. 执行过程步骤全透明（Agent Timeline Pattern）
3. 结论必须带证据（Evidence Pattern）
4. 高风险动作必须确认（Approval Pattern）
5. 动作之后必须验证（Verification 收尾）

---

## 3. 命令体系

命令不是入口，而是 **Agent 能力触发器**。自然语言与命令等价：

```
/migrate <path>      迁移工程            = "帮我迁移这个项目"
/diagnose <target>   诊断日志/程序/core   = "看看为什么崩了"
/optimize <target>   性能调优            = "这个模型太慢了"
/profile <target>    仅采集剖析数据
/observe             打开观测台
/explain <symbol>    解释代码/指令/报错
/kb <question>       知识库检索
/plan                查看/修改当前计划
/undo                回滚上一次 AI 修改
```

**Command Palette**（`Ctrl+P`）：模糊搜索全部命令 + 最近会话 + 文件。

---

## 4. 快捷键体系

| 快捷键 | 动作 |
|---|---|
| `Ctrl+P` | Command Palette |
| `Ctrl+A` | Agent Action 菜单（Accept/Review/Reject 当前提议）|
| `Ctrl+R` | Run / 重新执行 |
| `Ctrl+D` | 切到 Diff 视图 |
| `Ctrl+O` | 切到 Observe |
| `Ctrl+B` | 折叠/展开 Explorer |
| `Ctrl+J` | 抽高/收起 Agent Console |
| `Tab` | 区域焦点轮转 |
| `j / k` | 列表上下（vim 风格）|
| `Enter` | 下钻 / 展开 |
| `y / r / n` | Approve / Review / Reject |
| `Esc` | 中断 Agent / 返回上级 |
| `?` | 快捷键速查浮层 |

---

## 5. 状态符号体系（ASCII 语义）

| 符号 | 语义 | 使用处 |
|---|---|---|
| `✓` | 完成 / 通过 | Timeline、检查项 |
| `▶` | 执行中 | Timeline 当前步 |
| `○` | 等待 | Timeline 未来步 |
| `✕` | 失败 | Timeline、检查项 |
| `⚠` | 风险 / 警告 | Issue、检查项 |
| `●` | 在线 / 活跃 | Header 状态 |
| `❯` | 输入提示符 | Input Bar |
| `█ ░ ▂▃▅▇` | 图表填充 | Bar / Sparkline |

---

## 6. 视觉语言（OpenDesign TUI 映射）

**关键词**：极客 · 工程 · 专业 · 高密度信息
**避免**：普通聊天 UI、大面积空卡片、低信息密度

### 色彩 Token（256-color / truecolor 双档）

| Token | 用途 | 建议色 |
|---|---|---|
| `fg.primary` | 正文 | #E6E6E6 |
| `fg.dim` | 次级信息 | #8A8F98 |
| `accent` | 品牌主色 / 焦点 | #38D3AE（鲲鹏青绿） |
| `accent.alt` | Agent 活动 | #7AA2F7 |
| `ok` | 成功 | #9ECE6A |
| `warn` | 警告 | #E0AF68 |
| `error` | 错误 / Critical | #F7768E |
| `bg.panel` | 面板底 | #16161E |
| `border` | 边框 | #2A2F3A |

### 排版规则
- 全等宽字体；层级用 **缩进 + 符号 + 颜色** 表达，不靠字号
- 数字右对齐；百分比恒带 bar；单位不省略
- 边框：主面板圆角 `╭╮╰╯`，内嵌块直角 `┌┐└┘`，分隔 `─`

### 动效（终端可行域内）
- Spinner：`⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏`（Agent 思考/工具执行）
- 进度条填充按帧推进；Timeline 当前步 `▶` 呼吸闪烁
- 流式输出逐行 reveal；禁止全屏重绘闪烁
