#!/usr/bin/env python3
"""生成 web/design-input.html —— 《DevKit AI TUI 设计输入》评审版单页。

正文真值在 docs/DESIGN-INPUT.md，这一页是它的评审转录：同一套结论，
换成能在浏览器里扫读的排版，并把字符图交给 screens.py 的宽度断言把着。

  python3 tools/gen_design_input.py
"""

from __future__ import annotations

import pathlib

from page_css import CSS, JS
from screens import Pane, check, hcat, pad, to_html, width

OUT = pathlib.Path(__file__).resolve().parent.parent / "web" / "design-input.html"


def block(src: str, cls: str = "dense") -> str:
    return f'<pre class="{cls}">{to_html(src)}</pre>'


def fig(title: str, src: str, cls: str = "dense", strict: bool = False) -> str:
    """strict=True 的块每行等宽，交给 check_frames.py 在真浏览器里复核。

    自由排版的流程图不设 strict——它们本来就不是等宽块，拿等宽去要求它们
    只会让门禁天天报假警，报到最后没人看。
    """
    mark = f' data-check="1" data-label="{title}"' if strict else ""
    return (
        f'<div class="fig"><span class="fig-t">{title}</span>\n'
        f'<pre class="{cls}"{mark}>{to_html(src)}</pre>\n</div>'
    )


# ── 字符图 ──────────────────────────────────────────────────────────────
PROVIDER_FLOW = """⟦cm|Provider⟧ ─▸ ⟦cm|Base URL⟧ ─▸ ⟦cm|API Key⟧ ─▸ ⟦cm|获取模型⟧ ─▸ ⟦cm|选择模型⟧ ─▸ ⟦cm|测试连接⟧ ─▸ ⟦ok|✓ Ready⟧
   ⟦cm|│⟧            ⟦cm|│⟧             ⟦cm|│⟧            ⟦cm|│⟧             ⟦cm|│⟧             ⟦cm|│⟧
   ⟦cm|└ 预置清单⟧    ⟦cm|└ 格式示例⟧     ⟦cm|└ 掩码回显⟧   ⟦cm|└ 拉取失败即⟧    ⟦cm|└ 能力标注⟧     ⟦cm|└ 实测延迟⟧
   ⟦cm|  可自定义⟧    ⟦cm|  缺 /v1 提示⟧  ⟦cm|  sk-**…**⟧   ⟦wn|  分类报错⟧     ⟦cm|  上下文长度⟧   ⟦cm|  218ms⟧

⟦wn|每一步都可就地验证。⟧⟦cm|不允许「只能保存、不能测」——那等于把失败推迟到第一次真正用的时候。⟧"""


def interrupt_flow() -> str:
    left = Pane(38).add(
        "⟦cm|传统 CLI⟧",
        "",
        "⟦t|Ctrl+C⟧",
        "   ⟦cm|↓⟧",
        "⟦er|进程终止⟧",
        "   ⟦cm|↓⟧",
        "⟦er|上下文全丢，重来一遍⟧",
    )
    right = Pane(56).add(
        "⟦cm|DevKit AI⟧",
        "",
        "⟦t|Esc⟧",
        "   ⟦cm|↓⟧",
        "⟦pr|暂停当前动作⟧ ⟦cm|·⟧ ⟦pr|保留上下文⟧",
        "   ⟦cm|↓⟧",
        "⟦ok|用户纠偏 → 从断点继续（不杀进程）⟧",
    )
    lines = hcat([left, right], sep="   ", sep_cls="")
    return check("\n".join(lines), 97, "interrupt")


IA_TREE = """⟦t|DevKit AI⟧
├── ⟦t|Home / Welcome⟧              ⟦cm|环境 · 模型 · 输入 · 最近⟧
├── ⟦t|Agent Workspace⟧            ⟦cm|Conversation · Agent Status · Tool/Skill · Diff · Ask User⟧
├── ⟦t|Task Manager⟧               ⟦cm|Running · Waiting · Suspended · Completed⟧
├── ⟦t|File Explorer⟧              ⟦cm|工程树，跟随 Agent 当前文件⟧
├── ⟦t|Session⟧                    ⟦cm|历史上下文 · resume · fork⟧
├── ⟦t|Skill⟧                      ⟦cm|安装 · 卸载 · 查看源码⟧
├── ⟦t|Model / Provider⟧           ⟦cm|配置 · 诊断 · 切换⟧
└── ⟦t|Settings / Update⟧          ⟦cm|客户端与 Skill 升级⟧"""


def plan_fig() -> str:
    """阶段依赖：三行按列对齐，列宽由内容算出，不手数空格。"""
    stages = [
        ("⟦ok|S0 设计输入⟧", "⟦cm|本次⟧", "⟦ok|✓ 已完成⟧"),
        ("⟦pr|S1 IA + 全局规范⟧", "⟦cm|UI-SPEC 升版⟧", "⟦cm|状态/错误/键位/降级⟧"),
        ("⟦pr|S2 页面设计合同⟧", "⟦cm|pages/ × 8⟧", "⟦cm|双帧 + 验收条件⟧"),
        ("⟦pr|S3 任务交互原型⟧", "⟦cm|7 条链路真机跑通⟧", "⟦cm|160 / 120 / 80 三档⟧"),
        ("⟦pr|S4 组件规范 + 实现对齐⟧", "⟦cm|bun run check 全绿⟧", "⟦cm|规范与实现互为约束⟧"),
    ]
    cols = [max(width(c) for c in st) + 4 for st in stages]
    rows = ["", "", ""]
    for i, st in enumerate(stages):
        last = i == len(stages) - 1
        rows[0] += pad(st[0] + ("" if last else " ⟦cm|─▸⟧"), cols[i])
        rows[1] += pad(st[1], cols[i])
        rows[2] += pad(st[2], cols[i])
    rows += [
        "",
        "⟦wn|并行验证⟧⟦cm| ── Q1 宽度分布 · Q2 键位冲突 · Q3/Q4/Q7 图元降级 · Q9 错误样本⟧",
        "⟦cm|           结论必须在 S1 结束前给出，否则 S2 无法定帧⟧",
    ]
    w = max(width(r) for r in rows)
    return "\n".join(pad(r, w) for r in rows)


def loop_fig() -> str:
    head = "⟦t|快速接入⟧ ⟦cm|─▸⟧ ⟦t|明确任务⟧ ⟦cm|─▸⟧ ⟦t|Agent 执行⟧ ⟦cm|─⟧"
    col = width(head)
    l1 = head + "⟦cm|┬─▸⟧ ⟦pr|可观察 Observe⟧ ⟦cm|─┐⟧"
    l2 = (
        " " * col
        + "⟦cm|└─▸⟧ ⟦pr|可控制 Control⟧ ⟦cm|─┴─▸⟧ ⟦ok|结果交付⟧ ⟦cm|─▸⟧ ⟦ok|Session 延续⟧"
    )
    w = max(width(l1), width(l2))
    return check("\n".join(pad(x, w) for x in (l1, l2)), w, "loop")


TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DevKit AI TUI 设计输入</title>
<meta name="description" content="背景 · 用户 · 场景 · 设计目标 · 核心能力 · 关键交互 · 状态体系 · 页面与组件 · 设计原则 · 待验证问题 · 后续阶段规划">
<style>{css}</style>
</head>
<body>

<div class="topbar">
  <span class="kpmark">◢</span>
  <span class="brand">Kunpeng DevKit AI</span>
  <span class="vchip">设计输入 v1.0</span>
  <span class="tagline">给 UX · 交互 · 视觉 · TUI 开发共用的一份输入</span>
  <span class="tb-right">
    <a href="./screens.html">五个典型页面 ↗</a>
    <a href="./index.html#primlib">设计系统 ↗</a>
    <button class="tbtn" onclick="tt()">◐ <span id="tl">Light</span></button>
  </span>
</div>

<div class="wrap">
<nav id="nav">
  <div class="ngrp">Context · 上下文</div>
  <a href="#bg">1 项目背景</a>
  <a href="#user">2 用户</a>
  <a href="#scene">3 场景</a>
  <div class="ngrp">Requirement · 要求</div>
  <a href="#goal">4 设计目标</a>
  <a href="#cap">5 核心能力</a>
  <a href="#inter">6 关键交互</a>
  <a href="#state">7 状态体系</a>
  <div class="ngrp">Output · 产出</div>
  <a href="#ia">8 页面与组件</a>
  <a href="#principle">9 设计原则</a>
  <a href="#open">10 待验证问题</a>
  <a href="#plan">11 后续阶段规划 ★</a>
  <div class="nfoot">正文真值<br>docs/DESIGN-INPUT.md</div>
</nav>

<main>

<section id="bg">
<div class="eyebrow">Design Input · v1.0</div>
<h1>DevKit AI TUI 设计输入</h1>
<p class="desc">这份输入取代原先按「用户目标 / 动作 / 情绪 / 痛点」组织的<a href="./index.html#jmap">旅程地图</a>。旅程地图回答<strong>「用户经历了什么」</strong>，适合发现问题；设计输入要回答<strong>「因此界面必须提供什么」</strong>，才能直接被交互、视觉和实现接住。旅程地图保留为推导材料，不再作为设计依据。</p>
<div class="grid g4">
  <div class="stat"><b style="color:var(--primary-hover)">6</b><span>设计目标</span></div>
  <div class="stat"><b style="color:var(--success)">4</b><span>状态机</span></div>
  <div class="stat"><b style="color:var(--warning)">20</b><span>组件</span></div>
  <div class="stat"><b style="color:var(--accent)">10</b><span>待验证问题</span></div>
</div>

<h2>1 · 项目背景</h2>
<p class="desc">DevKit AI 是面向鲲鹏开发者的 AI Agent 工具，覆盖<strong>迁移、开发、诊断、调优</strong>四类核心场景。产品以 TUI 为主要交互形态：用户在终端启动，用自然语言与 Agent 交互，Agent 通过 Skill、Tool、文件系统完成复杂任务。</p>
<p class="desc">与传统 CLI 不同，它不只是「在终端输出文字」，而要承担类似 IDE 的<strong>任务组织、状态展示、过程观察和任务控制</strong>能力。</p>
<table>
<tr><th>形态</th><th>运行方式</th><th>能力边界</th></tr>
<tr><td>CLI 工具</td><td>一次性进程，执行完退出</td><td>无状态、无布局、无实时</td></tr>
<tr><td>IDE 插件 / 内嵌终端</td><td>寄生在 IDE 进程内</td><td>受宿主 UI 约束；必须先有 IDE</td></tr>
<tr><td><strong>原生 TUI 应用</strong></td><td><strong>独立常驻进程，全屏接管终端，自有事件循环</strong></td><td><strong>自主布局 / 状态 / 快捷键 / 渲染；直接跑在目标机器上</strong></td></tr>
</table>
<div class="note"><b>本次设计的核心不是做一个终端聊天窗口，而是建立一套：可接入、可理解、可观察、可控制、可交付的 Agent 工作界面。</b>选 TUI 是工程现实决定的——DevKit 部署在鲲鹏服务器上，源码、编译器、性能计数器、驱动都在那台机器上；IDE 插件方案要本地装 IDE + 挂远程开发 + 文件同步，多一层延迟，性能采集尤其失真。</div>
<div class="sublabel">技术约束 · 设计不得越界</div>
<p class="rule">TypeScript 5.9 · React 19 · <code>@opentui/core</code> 0.5.1 · <code>@opentui/react</code> 0.5.1 · Bun。设计每一处都要同时过四关：①产品体验是否成立 ②React + OpenTUI 是否实现得了 ③是否该沉淀为可复用组件 ④宽屏 / 窄屏 / SSH / 低能力终端是否可用。<strong>实现不了的视觉效果不许留给后续阶段自行解释</strong>——冲突时记录证据与待裁决问题，裁决前保持 <code>draft</code>。</p>
</section>

<section id="user">
<div class="eyebrow">Who</div>
<h2>2 · 用户</h2>
<p class="desc">鲲鹏开发者 · 软件迁移开发者 · 应用开发者 · 系统运维与诊断人员 · 性能调优人员 · AI / Agent 技术用户 · 熟悉 Linux 与 Terminal 的极客用户。</p>
<table>
<tr><th>可以假设用户会</th><th>不可以假设用户会</th></tr>
<tr><td>用 ssh、看日志、读 diff、跑编译</td><td>理解 Agent 内部机制（planner / tool loop / context window）</td></tr>
<tr><td>判断一处代码改动对不对</td><td>知道哪个 Skill 该在什么时候装</td></tr>
<tr><td>看懂火焰图、热点函数、NUMA 概念</td><td>记住 Provider / Base URL / API Key 的正确组合形态</td></tr>
<tr><td>接受键盘优先的操作方式</td><td>忍受「点了但屏幕没反应」</td></tr>
</table>
<p class="rule"><strong>技术门槛可以高，产品门槛必须低。</strong>凡是要求用户理解 Agent 实现机制才能操作的界面，都是设计缺陷。使用环境上，160 列是理想态，<strong>120 列是主力，80 列必须可用</strong>——宽度是设计变量而不是常量。</p>
</section>

<section id="scene">
<div class="eyebrow">Where</div>
<h2>3 · 场景</h2>
<table>
<tr><th>场景</th><th>用户要什么</th><th>结果形态</th></tr>
<tr><td>迁移</td><td>系统迁移 · 应用源码迁移 · 容器迁移 · 数据库 SQL 迁移</td><td>兼容性报告 + 逐条改动 diff</td></tr>
<tr><td>开发</td><td>代码开发 · 代码分析 · 代码优化 · 亲和加速库替换</td><td>代码改动 + 构建验证</td></tr>
<tr><td>诊断</td><td>硬件诊断 · 系统问题诊断 · 崩溃与内存定位</td><td>根因链路 + 修复方案</td></tr>
<tr><td>调优</td><td>系统调优 · 参数调优 · 性能分析（热点 / 火焰图 / NUMA）</td><td>方案对比图表 + 前后性能</td></tr>
</table>
<div class="sublabel">贯穿全流程的三个连接场景</div>
<div class="grid g3">
  <div class="card"><h4>配置补齐 · P27</h4><p>执行到一半才发现缺工具链 / 缺凭据 / 缺参数。<strong>要用到才问，且必须说明为什么要</strong>，填完接着原来那一步继续。</p></div>
  <div class="card"><h4>下一步引导 · P28</h4><p>一个阶段结束后给 1–3 条<strong>状态相关</strong>的建议，带耗时预估。禁止在阶段结束后甩回空白输入框。</p></div>
  <div class="card"><h4>多任务管理 · P29</h4><p>长任务后台跑，用户同时开着几个。<code>⏸ 等待配置</code>必须在底栏常驻——它卡着不动且需要人。</p></div>
</div>
<div class="sublabel">环境接入场景</div>
<table>
<tr><th>环境</th><th>判定</th><th>界面职责</th></tr>
<tr><td>本机即鲲鹏服务器</td><td>探测 aarch64 + 鲲鹏标识</td><td>直接可用，不打扰</td></tr>
<tr><td>目标在远端</td><td>架构不匹配</td><td>给「连接远程鲲鹏服务器」入口，<strong>但不阻断本地可完成的任务</strong>（源码扫描、静态分析）</td></tr>
<tr><td>远程 ssh 会话</td><td><code>SSH_TTY</code> 存在</td><td>降低重绘频率、关闭高频动效，宽度按实际 PTY 取</td></tr>
<tr><td>低能力终端</td><td>无 truecolor / 无 Braille / <code>NO_COLOR</code></td><td>走渲染降级链，<strong>形状承载信息，不依赖色相</strong></td></tr>
</table>
</section>

<section id="goal">
<div class="eyebrow">Why</div>
<h2>4 · 设计目标</h2>
<p class="desc">六条目标，每条都给出可判定的达成判据——判据是用来在评审里否决方案的，不是口号。</p>
<div class="grid g2">
  <div class="card"><h4>4.1 降低启动门槛</h4>
  <p>直接启动 · 启动带 Prompt · 恢复 Session · 非交互式执行 · 环境自动识别 · 本地与远程适配。</p>
  <p><strong>判据：用户不应该因为环境、连接方式或启动参数而无法开始工作。</strong></p></div>
  <div class="card"><h4>4.2 降低模型配置成本</h4>
  <p>配置是进入工作状态的前置条件，不是用户目的。要主动诊断、分类报错、自动反馈。</p>
  <p><strong>判据：用户感觉是在连接一个可用的 AI，而不是在配置一堆技术参数。</strong></p></div>
  <div class="card"><h4>4.3 过程可观察</h4>
  <p>在做什么 · 用什么 Skill · 调什么 Tool · 读写哪些文件 · 第几步 · 要不要决策 · 有无异常 · 能否中断。</p>
  <p><strong>判据：用户永远知道 Agent 在做什么，而不是面对一片等待中的黑屏。</strong></p></div>
  <div class="card"><h4>4.4 执行可控制</h4>
  <p>中断 · 改方向 · 回答提问 · 确认高危 · 暂停 · 后台 · 切换 · 恢复。</p>
  <p><strong>判据：Agent 可以自主执行，但用户始终拥有控制权。</strong></p></div>
  <div class="card"><h4>4.5 复杂任务可管理</h4>
  <p>Session · Agent Title · 多任务 · 后台任务 · 任务状态 · Resume · 切换。</p>
  <p><strong>判据：从「聊天记录管理」升级为「Agent 任务管理」。</strong></p></div>
  <div class="card"><h4>4.6 结果可快速获取</h4>
  <p>做了什么 · 改了什么 · 解决了什么 · 产生哪些文件 · 是否还有风险 · 下一步做什么。</p>
  <p><strong>判据：不要让用户从大量 Agent 输出里自己找最终价值。</strong></p></div>
</div>
{launch}
</section>

<section id="cap">
<div class="eyebrow">What</div>
<h2>5 · 核心能力</h2>
<div class="sublabel">5.1 启动与环境接入</div>
<p class="desc">首屏必须同时给出：产品标识与版本 · 欢迎语 · 四类能力介绍 · 输入框 · 基础命令 · <strong>当前环境检测结果</strong>。</p>
<p class="rule"><strong>不做纯 Logo 开屏。</strong>首屏要同时回答：环境状态 / 阻塞项 / 输入口 / 可继续的上下文。「最近」和「建议」两行让用户零输入就能往下走——这是常驻进程相对 CLI 的直接兑现，<strong>CLI 没有「上次」</strong>。</p>
<div class="sublabel">5.2 命令体系</div>
<table>
<tr><th>命令</th><th>作用</th><th>命令</th><th>作用</th></tr>
<tr><td class="mono">/help</td><td>命令帮助</td><td class="mono">/sessions</td><td>历史任务</td></tr>
<tr><td class="mono">/skill</td><td>Skill 安装与卸载</td><td class="mono">/model</td><td>选择模型</td></tr>
<tr><td class="mono">/view-skills</td><td>浏览 Skill 文件与源码</td><td class="mono">/provider</td><td>配置模型服务商</td></tr>
<tr><td class="mono">/info</td><td>完整能力说明</td><td class="mono">/connect-server</td><td>连接远程服务器</td></tr>
</table>
<p class="rule">自然语言是第一入口，<strong>命令是等价快捷方式而不是主路径</strong>。发现性靠 <kbd>Ctrl+P</kbd> 命令面板的模糊搜索，不靠视觉罗列——那是鼠标时代用密度换发现性的做法。</p>
<div class="sublabel">5.3 模型与 Provider</div>
<p class="desc">已出整屏字符帧：<a href="./screens.html#s5">管理配置页</a>——分类（服务器 / 账号 / 模型）→ 列表 → 详情，三类共用「必须能就地验证」这一条主线。</p>
{provider}
<table>
<tr><th>输入项</th><th>要求</th></tr>
<tr><td>Base URL</td><td>格式示例 + Placeholder；缺 <code>/v1</code>、协议头错误是最高频的两类错，要在报错里直接点名</td></tr>
<tr><td>API Key</td><td>密码掩码 · 支持粘贴 · 加密存储 · 回显只留首尾 <code>sk-****...****</code></td></tr>
<tr><td>主动验证</td><td>拉模型列表 / 测试连接 / 鉴权检查 / 网络检查 / Provider 可用性，<strong>五项都要能就地跑</strong></td></tr>
</table>
<div class="sublabel">5.4 任务、Session 与上下文</div>
<table>
<tr><th>概念</th><th>定义</th><th>界面呈现</th></tr>
<tr><td>Task</td><td>当前正在处理的具体任务，如「把 C++ 项目迁到鲲鹏」</td><td>顶部 Tab + Dock 任务列</td></tr>
<tr><td>Session</td><td>任务的完整历史上下文，可 <code>--resume</code> 恢复</td><td><code>/sessions</code> 列表 · Session 树</td></tr>
<tr><td>Context</td><td>本次对话已占的上下文水位</td><td>Inspector 常驻水位条：72% 转 warning，90% 主动建议 <code>/compact</code></td></tr>
</table>
<p class="rule">每个任务需具备：Agent Title · 状态 · 当前步骤 · 最近活动 · 运行时间 · Session ID。<strong>上下文水位是结果质量的先行指标</strong>，不能等它爆掉再解释。</p>
<div class="sublabel">5.5 – 5.7 Skill/Tool 可视化 · 结果交付 · 升级</div>
<div class="grid g3">
  <div class="card"><h4>Skill / Tool 可视化</h4><p>不输出大量原始日志，而给结构化状态：当前 Skill、Tool 列表与各自状态、进度。<strong>原始输出折叠可展开，默认不占画布。</strong></p></div>
  <div class="card"><h4>结果与交付</h4><p>固定四段 <strong>结论 → 证据 → 下一步 → 产出</strong>。产出区必须给路径与体积，并说明哪些不随报告导出。</p></div>
  <div class="card"><h4>升级</h4><p><code>devkitai update</code> 与 <code>devkitai skill update</code>：当前版本 · 目标版本 · 下载进度 · 安装状态 · 更新内容；失败给原因、重试、网络与权限提示。</p></div>
</div>
</section>

<section id="inter">
<div class="eyebrow">How</div>
<h2>6 · 关键交互</h2>
<div class="sublabel">6.1 冷启动追问</div>
<p class="desc">用户只说「帮我看看这个项目」时，Agent <strong>不应直接进入无目的执行</strong>，而要做意图识别与追问，并给鲲鹏场景相关的方向。</p>
{cold}
<div class="sublabel">6.2 执行过程</div>
<p class="desc">Thinking → Loading Skill → Calling Tool → Reading Files → Editing Files → Running Command → Verifying → Completed。界面把这条链路压成固定四行：<strong>状态 + Skill + Tools + 进度</strong>。任何时刻这四行都能回答「在做什么、用什么、到哪一步」，不需要展开日志。</p>
<div class="sublabel">6.3 Diff 与改动审查</div>
<p class="rule">重点不是展示所有代码，而是让用户快速完成一件事：<strong>确认 Agent 是否按预期改动</strong>。每个 hunk 固定带三行——<strong>为什么 / 证据 / 影响面</strong>。影响面最容易被漏掉，却直接决定用户敢不敢按「全部接受」。</p>
<div class="note"><b>这是本产品最大的机会点。</b>竞品分析跑完 7 个产品 × 22 个触点后，情绪最低点落在人审查 AI 改动这一步——<strong>没有一个产品做到 hunk 级的接受 / 拒绝</strong>。文件级接受等于逼用户二选一：要么全信，要么全部自己改。</div>
<div class="sublabel">6.4 – 6.5 Ask User 与高危确认</div>
<div class="grid g2">
  <div class="card"><h4>Ask User</h4><p>发现两个可能方案时列出来让用户选，而不是替用户拍板。<strong>不确定时询问，而不是擅自决策。</strong></p></div>
  <div class="card"><h4>高危确认</h4><p>删除文件 · 批量修改 · 改核心配置 · 高风险 Shell · 改系统环境 · 装卸软件，一律强制确认。确认框必须显示<strong>将要执行的原始命令本身</strong>与不可撤销说明，默认焦点在取消。只说「要执行危险操作吗」的确认框等于没确认。</p></div>
</div>
<div class="sublabel">6.6 中断：Interrupt → Correct → Resume</div>
{interrupt}
<p class="rule"><kbd>Esc</kbd> 不只是快捷键，而是<strong>人机协同机制</strong>。中断后输入框必须立即可用并给出提示，否则用户不知道自己已经拿回控制权。</p>
<div class="sublabel">6.7 – 6.8 多任务与长尾对话</div>
<p class="rule">长任务必须能后台跑；后台完成用<strong>非打断式通知</strong>（底栏变化 + 列表徽标），不抢当前焦点。任务完成不是 Session 的终点——结果页与输入框保持连续，<strong>不要把任务完成设计成封闭流程</strong>。</p>
<div class="sublabel">6.9 快捷键（待终端兼容性验证）</div>
<table>
<tr><th>快捷键</th><th>功能</th><th>快捷键</th><th>功能</th></tr>
<tr><td><kbd>Enter</kbd></td><td>发送 / 确认</td><td><kbd>Tab</kbd></td><td>区域切换</td></tr>
<tr><td><kbd>Esc</kbd></td><td>安全中断 / 返回</td><td><kbd>Ctrl+P</kbd></td><td>命令面板</td></tr>
<tr><td><kbd>Ctrl+C</kbd></td><td>复制 / 系统级中断</td><td><kbd>Ctrl+T</kbd></td><td>新建任务</td></tr>
<tr><td><kbd>Ctrl+V</kbd></td><td>粘贴</td><td><kbd>Ctrl+W</kbd></td><td>关闭当前任务</td></tr>
<tr><td><kbd>↑ / ↓</kbd></td><td>历史 / 选项</td><td><kbd>Ctrl+1~9</kbd></td><td>快速切换任务</td></tr>
</table>
<div class="note warn"><b><kbd>Ctrl+C</kbd> 是本表最大的冲突点。</b>它同时承担「复制」与「系统级中断」两种语义，终端里这两件事无法都要。必须在实现前裁决（见 Q2），不能留到编码时由实现自行决定——那会导致两个页面的行为不一致。</div>
</section>

<section id="state">
<div class="eyebrow">System</div>
<h2>7 · 状态体系</h2>
<p class="desc">四类状态机 + 一套统一符号。<strong>符号先行、颜色其次</strong>——16 色终端与 <code>NO_COLOR</code> 下形状仍要成立。</p>
<div class="grid g4">
  <div class="card"><h4>Agent</h4><p class="mono">Idle · Running · Waiting<br>Suspended · Completed · Failed</p></div>
  <div class="card"><h4>Tool</h4><p class="mono">Pending · Running<br>Success · Failed · Cancelled</p></div>
  <div class="card"><h4>Task</h4><p class="mono">Created · Running · Waiting<br>Suspended · Completed · Failed</p></div>
  <div class="card"><h4>Connection</h4><p class="mono">Disconnected · Connecting<br>Connected · Failed</p></div>
</div>
<table>
<tr><th>状态</th><th>符号</th><th>色</th><th>用在哪</th></tr>
<tr><td>Running / 进行中</td><td class="mono">● ⠹</td><td>primary</td><td>Agent · Tool · Task</td></tr>
<tr><td>Waiting / 需要用户</td><td class="mono">?</td><td>warning</td><td>Ask User · 配置补齐</td></tr>
<tr><td>Suspended / 已暂停</td><td class="mono">⏸</td><td>warning</td><td>后台任务 · 待配置</td></tr>
<tr><td>Completed / 成功</td><td class="mono">✓</td><td>success</td><td>全部</td></tr>
<tr><td>Failed / 失败</td><td class="mono">✕</td><td>danger</td><td>全部</td></tr>
<tr><td>Pending / 未开始</td><td class="mono">○</td><td>muted</td><td>Tool · Plan 步骤</td></tr>
<tr><td>风险提示</td><td class="mono">⚠</td><td>warning</td><td>结论层，不上色块</td></tr>
</table>
<div class="note"><b>颜色三分工不可越界。</b>Kunpeng 红 <code>#ED1C24</code> 只做身份，品牌蓝 <code>#0077FF</code> 只做交互，错误红 <code>#FF4B7B</code> 只做语义。判据是——看到红色时，该想到「华为鲲鹏」还是「出事了」？两种含义同屏出现即违规。<br><br><b>数据走色阶，结论走语义色。</b>bar、火焰图、热力用域色阶；只有被判定为问题的数值与文字才上 warning / danger。<strong>50% 的占比、90% 的 CPU 利用率本身都不是错误</strong>——在调优场景里利用率高往往是好事。</div>
<div class="sublabel">7.3 Loading</div>
<p class="rule">任何可能超过短暂等待的操作都要有明确反馈（<code>⠋ Connecting to Provider...</code>）。<strong>给不出进度就不画进度条</strong>——不确定进度用不确定态动画，不画假百分比。要避免的是：用户按了键 → 屏幕无变化 → 以为程序卡死。</p>
<div class="sublabel">7.4 错误分类</div>
<p class="desc">错误不能直接甩底层错误码，必须经分类与用户化解释，且三件套齐全：<strong>发生了什么 → 为什么 → 怎么解决</strong>。</p>
<table>
<tr><th>类别</th><th>文案</th><th>附带原因 / 动作</th></tr>
<tr><td>地址 / 格式</td><td>无法连接到该地址，请检查 Base URL 是否正确</td><td>缺 <code>/v1</code> · 协议头错误 · 拼写错误</td></tr>
<tr><td>网络 / 代理</td><td>连接超时，请检查当前网络环境或 VPN / 代理设置</td><td>代理未生效 · 目标不可达</td></tr>
<tr><td>鉴权</td><td>API Key 鉴权失败，请确认 Key 是否过期或权限不足</td><td>过期 · 权限不足 · 账号欠费</td></tr>
<tr><td>能力缺失</td><td>未检测到 aarch64 交叉编译工具链</td><td>附 <code>[F] 修复</code> 动作，不给死信息</td></tr>
</table>
</section>

<section id="ia">
<div class="eyebrow">Output</div>
<h2>8 · 页面与组件</h2>
{ia}
<div class="sublabel">组件清单 · 20 个</div>
<table>
<tr><th>组件</th><th>核心作用</th><th>归属</th><th>组件</th><th>核心作用</th><th>归属</th></tr>
<tr><td>Welcome</td><td>首次启动 · 能力介绍</td><td>页面局部</td><td>Confirm</td><td>高危操作确认</td><td>通用</td></tr>
<tr><td>Prompt</td><td>自然语言输入</td><td>全局 Shell</td><td>Task Panel</td><td>多任务管理</td><td>通用</td></tr>
<tr><td>Command Palette</td><td>命令发现</td><td>全局 Shell</td><td>Session</td><td>历史任务</td><td>通用</td></tr>
<tr><td>Agent Status</td><td>Agent 状态四行</td><td>通用</td><td>File Tree</td><td>工作区文件（跟随）</td><td>通用</td></tr>
<tr><td>Streaming Output</td><td>流式输出</td><td>通用</td><td>Model Selector</td><td>模型选择</td><td>页面局部</td></tr>
<tr><td>Tool Call</td><td>Tool 执行展示</td><td>通用</td><td>Provider Config</td><td>Provider 配置</td><td>页面局部</td></tr>
<tr><td>Skill Card</td><td>Skill 展示</td><td>通用</td><td>Loading</td><td>长耗时反馈</td><td>通用</td></tr>
<tr><td><strong>Diff</strong></td><td><strong>hunk 级修改确认 ★</strong></td><td>通用</td><td>Error</td><td>错误诊断</td><td>通用</td></tr>
<tr><td>Ask User</td><td>Agent 主动询问</td><td>通用</td><td>Summary</td><td>任务结果</td><td>通用</td></tr>
<tr><td>File Export</td><td>文件导出</td><td>通用</td><td>Update</td><td>软件 / Skill 更新</td><td>页面局部</td></tr>
</table>
<p class="rule">判定规则：<strong>出现在两个以上页面的进通用组件库，只出现一次的先留在页面里。</strong>这条规则要在每次新增页面时重跑一遍，否则组件库会同时长出「该复用却没复用」和「只用一次却被抽象」两类债。</p>
<div class="sublabel">五个典型页面（已出整屏字符帧）</div>
<table>
<tr><th>屏</th><th>回答哪个问题</th><th>关键组件</th></tr>
<tr><td><a href="./screens.html#s1">启动页</a></td><td>我能不能马上开始</td><td>Welcome · Env/Model 状态行 · Prompt · Next Step</td></tr>
<tr><td><a href="./screens.html#s2">Agent Workspace</a></td><td>Agent 在干什么</td><td>Task Tabs · File Tree · Plan Card · Agent Status · Evidence</td></tr>
<tr><td><a href="./screens.html#s3">执行中 · Tool + Diff</a></td><td>它有没有跑偏</td><td>Tool Call · Diff（hunk 级）· Confirm · Interrupt</td></tr>
<tr><td><a href="./screens.html#s4">任务结果页</a></td><td>我得到了什么</td><td>Summary · Hotspot Table · Flame Chart · Source Hotspot · Artifact List</td></tr>
<tr><td><a href="./screens.html#s5">管理配置</a></td><td>Agent 到底能不能工作</td><td>Settings Nav · Provider Config · Model Selector · Credential Field · Connection Test · Error</td></tr>
</table>
<div class="note"><b>结果页对齐 DevKit Web 端「热点函数分析」。</b>Top 30 热点调用栈表（函数/调用栈 · 周期数占比 · 周期数 · 进程名 · 共享库/文件）、火焰图（用户态 / 内核态 / 其他）、源码级逐行百分比——<strong>字段名与分组方式沿用 Web 端，用户在两端之间不需要做术语翻译</strong>。只有两处按 TUI 规则改写：红色退出数据层（语义红只表示「出事了」），紫色搜索标记改为背景反显（16 色下色相不可靠）。</div>
</section>

<section id="principle">
<div class="eyebrow">Principles</div>
<h2>9 · 设计原则</h2>
<div class="grid g2">
  <div class="card"><h4>① 状态优先</h4><p>用户首先要知道「现在发生了什么」，而不是先看到大量文本。</p></div>
  <div class="card"><h4>② 过程透明</h4><p>Agent 可以自主执行，但执行过程必须可观察。</p></div>
  <div class="card"><h4>③ 用户可控</h4><p>任何时候都能 Pause / Interrupt / Correct / Confirm / Resume。</p></div>
  <div class="card"><h4>④ 渐进式信息披露</h4><p>默认给状态 + 核心结果，需要时再展开 Tool → 参数 → 原始输出 → 日志。避免 TUI 被技术日志淹没。</p></div>
  <div class="card"><h4>⑤ 错误可理解</h4><p>从 <code>HTTP 500</code> / <code>Connection Refused</code> 转成「发生了什么 → 为什么 → 怎么解决」。</p></div>
  <div class="card"><h4>⑥ Agent First 而非 Chat First</h4><p>核心对象是 Task / Agent / Skill / Tool / File / Result，不是 User / Message / Message / Message。</p></div>
  <div class="card"><h4>⑦ 画不下就显式说</h4><p><code>… 24 more</code> · <code>3 帧过窄未显示</code> · <code>9 行未展开</code>。悄悄省略会把「我看全了」变成错觉，比不画更危险。</p></div>
  <div class="card"><h4>评审三问</h4><p>①遮住所有蓝色，还能说清「我现在选中的是什么」吗？能，说明蓝铺多了。②遮住颜色，状态还读得出来吗？③每条结论旁边有没有可点开的证据？</p></div>
</div>
<div class="sublabel">本次设计重点解决的六个问题</div>
<table>
<tr><th>#</th><th>问题</th><th>靠什么解</th><th>对应屏</th></tr>
<tr><td>①</td><td>我能不能马上开始？</td><td>启动 · 环境检测 · 远程连接</td><td><a href="./screens.html#s1">启动页</a></td></tr>
<tr><td>②</td><td>Agent 到底能不能工作？</td><td>Model / Provider / API Key / Connection</td><td><a href="./screens.html#s5">管理配置</a></td></tr>
<tr><td>③</td><td>Agent 到底在干什么？</td><td>Agent 状态 · Skill · Tool · Streaming · Progress</td><td><a href="./screens.html#s2">Workspace</a></td></tr>
<tr><td>④</td><td>Agent 有没有跑偏？</td><td>Diff · Ask User · Checkpoint · Interrupt</td><td><a href="./screens.html#s3">执行中</a></td></tr>
<tr><td>⑤</td><td>我有很多任务怎么办？</td><td>Task / Session / Background / Switch</td><td>Task Manager（P1，待出）</td></tr>
<tr><td>⑥</td><td>做完之后我得到了什么？</td><td>Summary · Files · Diff · Export · Next Step</td><td><a href="./screens.html#s4">结果页</a></td></tr>
</table>
<div class="sublabel">体验闭环</div>
{loop}
<p class="rule"><strong>让 Agent 自主执行，让用户始终看得见、管得住、拿得到结果。</strong></p>
</section>

<section id="open">
<div class="eyebrow">Open</div>
<h2>10 · 待验证问题</h2>
<p class="desc">十个问题，每个都标了裁决人——<strong>没有裁决人的待办不会被解决</strong>。Q1 Q2 是 S1 的阻塞项。</p>
<table>
<tr><th>#</th><th>问题</th><th>影响</th><th>验证方式</th><th>裁决人</th></tr>
<tr><td>Q1</td><td>目标用户终端宽度分布</td><td>决定 3 栏布局是主路径还是奢侈路径</td><td>抽样调研；若 &lt;140 列占多数，Inspector 默认折叠</td><td>产品</td></tr>
<tr><td>Q2</td><td><kbd>Ctrl+C</kbd> 语义冲突</td><td>影响全局键位表</td><td>终端兼容性实测 + 用户预期调研</td><td>交互</td></tr>
<tr><td>Q3</td><td>火焰图在 TUI 的可用深度</td><td>超过 6 层每帧不足 1 格</td><td>真实 perf 数据跑降级，评估「过窄未显示」占比</td><td>设计 + 实现</td></tr>
<tr><td>Q4</td><td>热点表 6 列在 120 列下的可读性</td><td>共享库路径列极易溢出</td><td>中段省略 vs 只留 basename 两版对比</td><td>设计</td></tr>
<tr><td>Q5</td><td>中断后「继续」的语义</td><td>重跑当前步还是跳过</td><td>需产品裁决，两种语义都要有明确文案</td><td>产品</td></tr>
<tr><td>Q6</td><td>OpenTUI 0.5.1 局部重绘性能</td><td>宽屏 + SSH 低带宽下的可用性</td><td>真机压测</td><td>实现</td></tr>
<tr><td>Q7</td><td>Braille 在中文等宽字体下的对齐</td><td>影响 T2 图元可用性</td><td>目标终端字体实测</td><td>实现</td></tr>
<tr><td>Q8</td><td>终端图形协议（T5）可用比例</td><td>决定要不要投入光栅渲染</td><td>目标环境采样统计</td><td>实现</td></tr>
<tr><td>Q9</td><td>Provider 错误的真实分布</td><td>错误分类是否覆盖得住</td><td>收集真实失败样本再定分类粒度</td><td>产品 + 实现</td></tr>
<tr><td>Q10</td><td><code>Failed</code> / <code>Idle</code> 态屏未设计</td><td>失败是分支不是死路，缺屏即缺路径</td><td>下一阶段补出失败态与空态屏</td><td>设计</td></tr>
</table>
</section>

<section id="plan">
<div class="eyebrow">Roadmap</div>
<h2>11 · 后续阶段规划</h2>
<p class="desc">四类设计产物按<strong>依赖顺序</strong>排，不并行开工：信息架构不定，页面会互相打架；页面不定，组件规范只能凭空写。</p>
{plan}
<div class="sublabel">阶段划分</div>
<table>
<tr><th>阶段</th><th>交付物</th><th>完成判据</th><th>依赖</th><th>主要风险</th></tr>
<tr><td><strong>S0 设计输入</strong><br><span class="badge s">已完成</span></td><td>本文 + 五个典型页面字符帧</td><td>六问答上 ①②③④⑥；五屏宽度经断言校验并在真浏览器复核</td><td>—</td><td>问题 ⑤ 的 Task Manager 屏留到 S2</td></tr>
<tr><td><strong>S1 IA 与全局规范</strong></td><td>IA 定稿；<code>UI-SPEC.md</code> 升版：状态体系、错误体系、键位表、降级链</td><td>跨页面规则全部落在 <code>UI-SPEC.md</code>，页面只引用规则 ID</td><td>S0</td><td>Q2 未裁决则键位表无法 <code>approved</code></td></tr>
<tr><td><strong>S2 页面设计合同</strong></td><td><code>pages/&lt;page-id&gt;.md</code> × 8，含 160×50 与 58×32 双帧、状态矩阵、验收条件</td><td>每页无待猜测项，实现无需回头问设计</td><td>S1</td><td>页面一多容易复制全局规则，需评审把关</td></tr>
<tr><td><strong>S3 任务交互原型</strong></td><td>7 条关键任务链路的可运行原型（TUI 真机）</td><td>每条链路能在 160 / 120 / 80 三档宽度下走通</td><td>S2</td><td>OpenTUI 性能（Q6）可能倒逼布局回改</td></tr>
<tr><td><strong>S4 组件规范与实现对齐</strong></td><td>通用组件契约 + <code>tui/</code> 实现 + 门禁</td><td><code>bun run check</code> 全绿；规范与实现无漂移</td><td>S3</td><td>规范与实现双向约束，任一方改动都要同步</td></tr>
</table>
<div class="sublabel">页面优先级</div>
<table>
<tr><th>优先级</th><th>页面</th><th>理由</th></tr>
<tr><td><span class="badge d">P0</span></td><td>Welcome · Agent Workspace · 执行中 Tool+Diff · 任务结果 · 管理配置（服务器/账号/模型）</td><td>直接对应六问 ①②③④⑥，缺一条链路就断；<strong>五屏字符帧已出</strong></td></tr>
<tr><td><span class="badge w">P1</span></td><td>Task Manager · Session · Skill 管理 · 失败态屏</td><td>支撑长任务与多任务，对应问题 ⑤</td></tr>
<tr><td><span class="badge">P2</span></td><td>File Explorer · File Export · Settings / Update</td><td>收尾能力，可在 S3 之后补</td></tr>
</table>
<div class="sublabel">S3 的七条关键任务链路</div>
<div class="grid g2">
  <div class="card"><h4>1 首次启动</h4><p>启动 → 环境检测 → 能力安装</p></div>
  <div class="card"><h4>2 模型配置</h4><p>配置 → 失败诊断 → 连接成功</p></div>
  <div class="card"><h4>3 代码迁移</h4><p>自然语言触发 → Plan 确认 → 配置补齐 → 执行</p></div>
  <div class="card"><h4>4 改动审查</h4><p>Agent 执行 → hunk 级审查 → 高危确认</p></div>
  <div class="card"><h4>5 中断纠偏</h4><p><kbd>Esc</kbd> 中断 → 纠偏 → 断点续跑</p></div>
  <div class="card"><h4>6 多任务</h4><p>切换 → 后台完成通知 → 回到原任务</p></div>
  <div class="card"><h4>7 结果交付</h4><p>结果页 → 下一步引导 → 导出与 Session 延续</p></div>
  <div class="card"><h4>并行验证</h4><p>Q1 宽度调研 · Q2 键位裁决 · Q3/Q4/Q7 图元降级实测 · Q9 错误样本收集。<strong>都要在 S1 结束前有结论</strong>，否则阻塞 S2 定帧。</p></div>
</div>
<div class="note"><b>每一阶段评审只问一句：</b>是否能让用户在纯终端环境下，建立接近 IDE 的<strong>「任务感、状态感和控制感」</strong>，而不是仅仅得到一个更漂亮的 CLI。</div>
</section>

<footer>
Kunpeng DevKit AI · 设计输入 v1.0 · 正文真值 docs/DESIGN-INPUT.md · 本页由 tools/gen_design_input.py 生成<br>
内部设计资料，授权方式待定。Kunpeng 标识及华为品牌色版权归华为技术有限公司所有。
</footer>

</main>
</div>
<script>{js}</script>
</body>
</html>
"""

LAUNCH_CMDS = """⟦cm|$⟧ devkitai                                  ⟦cm|交互式 TUI⟧
⟦cm|$⟧ devkitai ⟦ac|"帮我迁移这个 C++ 项目"⟧           ⟦cm|启动即执行⟧
⟦cm|$⟧ devkitai ⟦pr|--resume⟧ ⟦ac|<id>⟧                    ⟦cm|恢复历史任务⟧
⟦cm|$⟧ devkitai ⟦pr|session list⟧                     ⟦cm|查看历史 Session⟧
⟦cm|$⟧ devkitai ⟦pr|--non-interactive⟧ ⟦ac|"检查这个项目"⟧  ⟦cm|CI 可调用⟧"""

COLD = """⟦pr|❯⟧ ⟦t|帮我看看这个项目⟧

⟦cm|Agent⟧  ⟦wn|意图不足以直接执行⟧⟦cm| —— 先识别再问，而不是先跑起来⟧
       ⟦cm|已扫描：C/C++ 工程 · 1,204 文件 · 检出 x86 内联汇编 3 处⟧

⟦cm|我可以从以下方向帮你分析：⟧
  ⟦pr|[1] 迁移兼容性⟧   ⟦cm|[2] 代码优化⟧   ⟦cm|[3] 性能诊断⟧   ⟦cm|[4] 依赖分析⟧   ⟦cm|[5] 鲲鹏适配检查⟧
⟦pr|❯⟧ ⟦cm|或直接说你想干什么▌⟧"""


def build() -> str:
    return TEMPLATE.format(
        css=CSS,
        js=JS,
        launch=fig("启动方式 · 五条入口", LAUNCH_CMDS),
        provider=fig("模型配置链路 · 每一步都可就地验证", PROVIDER_FLOW),
        cold=fig("冷启动追问", COLD),
        interrupt=fig("Interrupt → Correct → Resume", interrupt_flow(), strict=True),
        ia=fig("信息架构", IA_TREE),
        loop=fig("体验闭环", loop_fig(), strict=True),
        plan=fig("阶段依赖 · S0 已完成", plan_fig(), strict=True),
    )


if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8")
    print(f"✓ {OUT.name}  {OUT.stat().st_size / 1024:.0f}KB")
