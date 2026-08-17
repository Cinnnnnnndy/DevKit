# 设计规范索引

> 本目录保存设计研究、推导和源规范。供后续实现使用的正式交付入口是 [`../UI-SPEC.md`](../UI-SPEC.md) 与 [`../pages/`](../pages/)；本目录不承载正式交付中缺失的规范性要求。

从这里进入各份文档。建议阅读顺序：**DESIGN-INPUT → OVERVIEW → VISUAL → PATTERN**，其余按需查阅。

| 文档 | 内容 | 什么时候读 |
|---|---|---|
| [DESIGN-INPUT.md](DESIGN-INPUT.md) ★ | 设计输入：背景 · 用户 · 场景 · 目标 · 能力 · 交互 · 状态 · 页面组件 · 原则 · 待验证 · 阶段规划 | **开始任何设计之前**——它取代旅程地图作为设计依据 |
| [OVERVIEW.md](OVERVIEW.md) | 产品定位、愿景、用户角色、信息架构 | 第一次接触这个项目 |
| [JOURNEY.md](JOURNEY.md) | 六阶段用户旅程、Demo 十幕故事线、演示画布规范 | 想知道用户怎么用它（推导材料，非设计依据） |
| [VISUAL.md](VISUAL.md) ★ | PTO → TUI 的完整 token 翻译、颜色纪律、动效边界 | 动任何视觉之前 |
| [PATTERN.md](PATTERN.md) | 交互 Pattern 库 P01–P29 | 设计任一具体界面时 |
| [UX-SPEC.md](UX-SPEC.md) | 布局、交互模型、命令体系、快捷键 | 定键位和命令时 |
| [COMPONENT.md](COMPONENT.md) | 图表原语与组件规范 | 画数据可视化时 |
| [TUI-CAPABILITY.md](TUI-CAPABILITY.md) | 能力基线、渲染分层 T0–T5、框架选型 | 判断"这个效果做不做得出来" |
| [FRAMEWORK.md](FRAMEWORK.md) | 应用框架：MobaXterm 结构 × PTO 分割 | 定整体布局时 |
| [PRD.md](PRD.md) | 六大核心场景需求 | 排功能优先级时 |
| [COMPETITIVE-ANALYSIS.md](COMPETITIVE-ANALYSIS.md) | 7 竞品 × 22 触点的 UX 对比 | 想知道别人怎么做的 |
| [DEMO-WIREFRAME.md](DEMO-WIREFRAME.md) | 四大 Demo 的 ASCII 交互稿 | 准备演示时 |

**★ DESIGN-INPUT.md 是设计的入口。** 旅程地图回答「用户经历了什么」，设计输入回答「因此界面必须提供什么」——后者才能被交互、视觉和实现直接接住。四个典型页面的整屏字符帧见 [`../web/screens.html`](../web/screens.html)。

**★ VISUAL.md 是最厚也最关键的一份。** 它不只写"结论是什么"，也写了"曾经试过什么、为什么被推翻"——字符做的辉光为什么是脏的、全屏横扫的动效为什么参数怎么调都不对、把 KUNPENG 压灰为什么反而把名字拆散了。改动之前先读，能省下重复踩坑的时间。
