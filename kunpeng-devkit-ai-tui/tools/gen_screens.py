#!/usr/bin/env python3
"""生成 web/screens.html —— 五个典型页面的整屏字符帧。

五屏：启动页 / Agent Workspace / Agent 执行中（Tool + Diff）/ 任务结果页 /
管理配置（服务器 · 账号 · 模型）。
每屏给两帧：160×N 宽屏主帧 + 80 列窄屏降级帧，宽度由 screens.py 断言把着。

  python3 tools/gen_screens.py
"""

from __future__ import annotations

import pathlib

from screens import Frame, Pane, bar, check, hcat, pad, to_html, width, wordmark

W = 160
INNER = W - 2
OUT = pathlib.Path(__file__).resolve().parent.parent / "web" / "screens.html"

KPI_B64 = (
    "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"
)
KPI_IMG = f'<img class="kpi" alt="K" src="data:image/png;base64,{KPI_B64}">'


# ── 小工具 ──────────────────────────────────────────────────────────────
def colsep(widths: list[int], left: str = "├", right: str = "┤", mid: str = "┼") -> str:
    """按栏宽拼一条与竖线对齐的分隔行（不含外框左右柱）。"""
    return mid.join("─" * w for w in widths)


def spread(left: str, right: str, w: int) -> str:
    """左内容 + 右对齐尾巴，中间自动补齐——省得手数空格。"""
    return pad(left, w - width(right)) + right


def card(w: int, title: str, lines: list[str], title_cls: str = "t") -> list[str]:
    """能力卡：上框嵌标题，内容左缩进 1。"""
    head = f"⟦cm|┌ ⟧⟦{title_cls}|{title}⟧⟦cm| {'─' * (w - width(title) - 4)}┐⟧"
    body = [f"⟦cm|│⟧{pad(' ' + x, w - 2)}⟦cm|│⟧" for x in lines]
    return [head, *body, f"⟦cm|└{'─' * (w - 2)}┘⟧"]


def panel(w: int, title: str, lines: list[str], right: str = "") -> list[str]:
    """浮层用圆角——圆角在这套体系里等于「浮起」，见 #frame 规则③。"""
    tail = f"⟦cm| ⟧{right}⟦cm| ⟧" if right else "⟦cm|─⟧"
    fill = w - width(title) - width(tail) - 4
    head = f"⟦cm|╭ ⟧⟦t|{title}⟧⟦cm| {'─' * fill}⟧{tail}⟦cm|╮⟧"
    body = [f"⟦cm|│⟧{pad(' ' + x, w - 2)}⟦cm|│⟧" for x in lines]
    return [head, *body, f"⟦cm|╰{'─' * (w - 2)}╯⟧"]


# ══════════════════════════════════════════════════════════════════════
# 屏 1 · 启动页
# ══════════════════════════════════════════════════════════════════════
def screen_launch() -> str:
    f = Frame(W, "⟦br|▪⟧ ⟦t|DevKit AI⟧", "◈ Kunpeng 920 · aarch64 · ⟦ok|●⟧ 就绪")
    f.blank()
    for line in wordmark("DEVKIT AI"):
        f.add("        " + line if line else "")
    f.add("        ⟦cm|AI Terminal Workspace for Kunpeng⟧      ⟦cm|v0.6 · 2026-08⟧")
    f.blank()
    f.add(
        "  您好，欢迎使用 DevKit AI，我是鲲鹏智能助手，"
        "可以辅助鲲鹏领域的⟦t|迁移⟧、⟦t|开发⟧、⟦t|诊断⟧与⟦t|调优⟧。"
    )
    f.blank()

    cw = 37
    caps = [
        ("迁移", ["系统迁移 · 应用源码迁移", "容器迁移 · 依赖兼容性扫描", "数据库 SQL 迁移"]),
        ("开发", ["代码开发 · 代码分析", "代码优化 · 亲和加速库替换", "构建与编译验证"]),
        ("诊断", ["鲲鹏服务器硬件诊断", "系统与内核问题诊断", "崩溃 · 内存 · IO 定位"]),
        ("调优", ["系统调优 · 参数调优", "热点函数 · 火焰图", "NUMA 亲和 · 缓存行为"]),
    ]
    cards = [card(cw, t, body) for t, body in caps]
    for parts in zip(*cards):
        f.add("  " + "  ".join(parts))
    f.add("  ⟦cm|更多能力 ⟧⟦ac|/info⟧⟦cm|，安装与卸载 ⟧⟦ac|/skill⟧")
    f.blank()

    col = 68
    f.add(
        pad("  ⟦cm|环境⟧    ⟦ok|●⟧ 本机 ⟦t|Kunpeng 920⟧ · aarch64 · openEuler 22.03 LTS", col)
        + "⟦cm|Runtime 本地已就绪，不联网也能用⟧"
    )
    f.add(
        pad("          ⟦wn|⚠⟧ 未检测到 aarch64 交叉编译工具链", col)
        + "⟦pr|[F]⟧ 修复    ⟦pr|[C]⟧ 连接远程鲲鹏服务器"
    )
    f.add(
        pad("  ⟦cm|模型⟧    ⟦ok|●⟧ devkit-gateway · qwen2.5-72b-instruct", col)
        + "⟦ok|✓⟧ 连接正常 218ms    ⟦ac|/model⟧ 切换"
    )
    f.blank()
    f.add("  ⟦pr|❯⟧ ⟦t|想做什么？直接说⟧ ⟦cm|·  或按 ⟧⟦ac|Ctrl+P⟧⟦cm| 打开命令面板⟧▌")
    f.blank()
    f.add(
        pad(
            "  ⟦cm|最近⟧    ⟦ac|migrate nginx⟧        3 天前 · 兼容性 82% · "
            "⟦wn|2 项待人工确认⟧",
            col,
        )
        + "⟦pr|[↵]⟧ 继续"
    )
    f.add(
        pad("          ⟦ac|hotspot falsesharing⟧   昨天 · ⟦ok|已完成⟧ · 伪共享已修复", col)
        + "⟦cm|/sessions 看全部⟧"
    )
    f.add(
        "  ⟦cm|建议⟧    扫描当前工程   ·   安装 SQL 迁移能力包   ·   跑一次性能基线"
    )
    f.blank()
    f.add(
        "  ⟦cm|命令⟧    ⟦ac|/help⟧  ⟦ac|/skill⟧  ⟦ac|/view-skills⟧  ⟦ac|/sessions⟧  "
        "⟦ac|/model⟧  ⟦ac|/provider⟧  ⟦ac|/connect-server⟧"
    )
    f.foot(
        "⟦bs4| home ⟧ ⟦cm|mode:⟧⟦ok|auto⟧⟦cm| │ model:qwen2.5-72b │ ctx:0%⟧",
        "⟦cm|[Ctrl+P] 命令面板 · [Tab] 切换区域 · 0 任务运行⟧",
    )
    return check(f.render(), W, "launch")


def screen_launch_narrow() -> str:
    f = Frame(80, "⟦br|▪⟧ ⟦t|DevKit AI⟧", "⟦ok|●⟧ 就绪")
    f.blank()
    f.add("  ⟦br|▪⟧ ⟦t|DevKit AI⟧ ⟦cm|· AI Terminal Workspace⟧      ⟦cm|v0.6⟧")
    f.add("  ⟦cm|窄屏不画块字符 Logo——行数留给状态⟧")
    f.blank()
    f.add("  鲲鹏智能助手 · 迁移 / 开发 / 诊断 / 调优      ⟦ac|/info⟧")
    f.blank()
    f.add("  ⟦cm|环境⟧  ⟦ok|●⟧ Kunpeng 920 · aarch64      ⟦wn|⚠⟧ 缺工具链 ⟦pr|[F]⟧")
    f.add("  ⟦cm|模型⟧  ⟦ok|●⟧ qwen2.5-72b · ⟦ok|✓⟧ 218ms      ⟦ac|/model⟧")
    f.blank()
    f.add("  ⟦pr|❯⟧ 想做什么？直接说▌")
    f.blank()
    f.add("  ⟦cm|最近⟧  ⟦ac|migrate nginx⟧ · 82% · ⟦wn|2 项待确认⟧  ⟦pr|[↵]⟧")
    f.foot("⟦cm|[Ctrl+P]⟧ 命令面板", "⟦cm|<80 列 · 能力卡收为一行⟧")
    return check(f.render(), 80, "launch-narrow")


# ══════════════════════════════════════════════════════════════════════
# 屏 2 · Agent Workspace 核心工作台
# ══════════════════════════════════════════════════════════════════════
def screen_workspace() -> str:
    """wide-three：dock 27 · canvas 90 · inspector 39 —— 宽度直接取自
    platform/terminal/layout.ts 的 layoutForWidth(160)，不是我们另拍的数。"""
    dock, canvas, insp = 27, 90, 39
    assert dock + canvas + insp + 2 == INNER

    f = Frame(W, "⟦br|▪⟧ ⟦t|DevKit AI⟧", "◈ x86_64 → ⟦t|Kunpeng ARM64⟧ · ⟦ok|●⟧ 就绪")
    f.add(
        spread(
            "  ⟦bsel| ▶ 1 migrate nginx ⟧  ⟦cm|⠹ 2 hotspot⟧  ⟦cm|○ 3 diagnose crash⟧  "
            "⟦wn|⟧⟦hw|⏸⟧⟦wn| 4 order-svc⟧  ⟦cm|+⟧",
            "⟦cm|Session #1024 · 12m04s · v0.6⟧  ",
            INNER,
        )
    )
    f.sep(colsep([dock, canvas, insp], mid="┬"))

    dock_p = Pane(dock).add(
        "⟦bs2| ⟧⟦bs2|⟦br|▪⟧⟦bs2| ⟧⟦t|⟦bs2|DevKit AI⟧⟧⟦bs2|" + " " * 14 + "⟧",
        "",
        " ⟦cm|T A S K S⟧            ⟦cm|4⟧",
        "⟦bsel| ⟦pr|▎⟧⟦bsel|⟦ok|●⟧⟦bsel| 1 migrate nginx    ⟧⟧",
        " ⟦cm|  ⟧⟦pr|▶⟧⟦cm| 2 hotspot 伪共享  ⟧⟦pr|⠹⟧",
        " ⟦cm|  ○ 3 diagnose crash⟧",
        " ⟦cm|  ⟧⟦wn|⚠⟧⟦cm| 4 order-svc      ⟧⟦hw|⏸⟧",
        "",
        " ⟦cm|P R O J E C T⟧   ⟦pr|⇄ 跟随⟧",
        " ⟦cm|nginx-main/⟧",
        "  ⟦cm|└ src/⟧",
        "⟦bsel|    ⟦pr|▎⟧⟦bsel|crypto.c⟧⟦bsel|      ⟧⟦o3|███⟧⟦bsel| ⟧⟧",
        "     ⟦cm|memory.c⟧      ⟦o5|██⟧",
        "     ⟦cm|event.c⟧       ⟦o8|▏⟧",
        "  ⟦cm|└ conf/⟧",
        "",
        " ⟦cm|T O O L S⟧            ⟦cm|4⟧",
        " ⟦ok|✓⟧ ⟦cm|code_cpp_migrator⟧",
        " ⟦ok|✓⟧ ⟦cm|knowledge_base⟧",
        " ⟦pr|⠹⟧ ⟦cm|profiler⟧",
    )

    plan = [
        ("1", "Analyze dependency", "静态扫描依赖树", "", "~20s", "done"),
        ("2", "Find incompatible API", "", "kunpeng_knowledge_base_search", "~40s", "done"),
        ("3", "Generate patches", "", "code_cpp_migrator", "~60s", "run"),
        ("4", "Build verify", "交叉编译验证", "", "~50s", "todo"),
        ("5", "Benchmark", "迁移前后性能对比", "", "~30s", "todo"),
    ]
    body = []
    for no, title, sub, tool, cost, state in plan:
        glyph = {"done": "⟦ok|✓⟧", "run": "⟦pr|▶⟧", "todo": "⟦cm|○⟧"}[state]
        head = f" {glyph} ⟦cm|{no}⟧ " + (f"⟦t|{title}⟧" if state != "todo" else f"⟦cm|{title}⟧")
        line = spread(head, f"⟦cm|{cost}⟧ ", canvas - 6)
        if state == "run":
            line = "⟦bfoc|" + line + "⟧"
        body.append(line)
        if sub:
            body.append(f"      ⟦cm|{sub}⟧")
        if tool:
            body.append(f"      ⟦bs3| {tool} ⟧")
    body += [
        "",
        spread(
            " ⟦pr|[E] Execute⟧   ⟦cm|[M] Modify Plan⟧   ⟦cm|[C] Cancel⟧",
            "⟦cm|改计划不重跑已完成的步骤⟧",
            canvas - 6,
        ),
    ]

    canvas_p = Pane(canvas).add(
        " ⟦pr|❯⟧ ⟦t|把 ./nginx 迁到鲲鹏，编译验证通过为止⟧",
        "",
        *[
            " " + x
            for x in panel(
                canvas - 3,
                "AI PLAN",
                body,
                right="⟦cm|5 tools · ~3 min⟧",
            )
        ],
    )

    insp_p = Pane(insp).add(
        " ⟦cm|I N S P E C T O R⟧      ⟦cm|Ctrl+I⟧",
        "",
        " ⟦cm|当前对象⟧",
        "⟦bsel| ⟦pr|▎⟧⟦bsel|src/crypto.c⟧⟦bsel|  ⟧⟦cm|⟦bsel|hunk 3/12⟧⟧⟦bsel|      ⟧⟧",
        "",
        " ⟦cm|证据⟧",
        " ⟦ac|[1]⟧ 案例库 #4471",
        "     ⟦cm|x86 SSE 自旋 → ARM yield⟧",
        " ⟦ac|[2]⟧ ARM ARM §B2.5",
        "     ⟦cm|YIELD 指令语义⟧",
        "",
        " ⟦cm|本次改动⟧",
        " ⟦ok|+34⟧ ⟦er|-27⟧ ⟦cm|· 9 文件 · 12 hunk⟧",
        "",
        " ⟦cm|上下文⟧  " + bar(0.72, 18, "o4") + " ⟦wn|72%⟧",
        " ⟦cm|已读 18 文件 · 1.2k 行⟧",
        " ⟦cm|超 90% 会主动建议 /compact⟧",
    )
    for line in hcat([dock_p, canvas_p, insp_p]):
        f.add(line)

    f.sep(colsep([dock, canvas, insp], mid="┴"))
    f.add(
        spread(
            " ⟦cm|A G E N T   C O N S O L E⟧",
            "⟦cm|8 行 · [Ctrl+J] 抽高  [l] 折叠⟧ ",
            INNER,
        ),
        " ⟦ok|●⟧ ⟦cm|Understand request⟧   ⟦cm|意图已解析：迁移任务⟧",
        " ⟦ok|●⟧ ⟦cm|Scan project⟧         ⟦cm|1,204 files · 18 libs⟧",
        " ⟦pr|▶⟧ ⟦t|Generate patch⟧       ⟦bs3| code_cpp_migrator ⟧ ⟦pr|⠹⟧ ⟦cm|crypto.c hunk 3/12⟧",
        " ⟦cm|○ Build verify⟧" + pad("", 40) + "⟦cm|9 行未展开⟧",
    )
    f.sep()
    f.add(
        spread(
            " ⟦pr|❯⟧ 让 crypto.c 也用 NEON 优化▌",
            "⟦cm|/ 命令 · @ 文件 · ↑ 历史 · Ctrl+P 命令面板⟧ ",
            INNER,
        )
    )
    f.foot(
        "⟦bs4| migrate nginx ⟧ ⟦cm|mode:⟧⟦ok|auto⟧⟦cm| │ model:qwen2.5-72b │ ctx:⟧⟦wn|72% ⚠⟧",
        "⟦wn|⟧⟦hw|⏸⟧⟦wn| 1 waiting⟧⟦cm| · patch 3/12 · 12:09⟧",
    )
    return check(f.render(), W, "workspace")


def screen_workspace_narrow() -> str:
    """80 列 = layoutForWidth 的 single-canvas：Dock 收成 3 列图标条
    （字形取实现里的 ▮ ▯ ◇ ?），单画布，无 Inspector，console 6 行。"""
    f = Frame(80, "⟦br|▪⟧ ⟦t|DevKit AI⟧", "⟦ok|●⟧ 就绪")
    f.add(" ⟦bsel| ▶ 1 migrate ⟧ ⟦cm|⠹ 2 hotspot⟧ ⟦cm|○ 3 diag⟧        ⟦cm|single-canvas⟧")
    f.sep()
    f.add(" ⟦pr|▮⟧ ⟦pr|❯⟧ 把 ./nginx 迁到鲲鹏")
    f.add(" ⟦cm|▯⟧")
    f.add(" ⟦cm|◇⟧ ⟦t|Agent⟧ ⟦ok|●⟧ Running ⟦cm|· 步骤 3/5⟧       ⟦cm|[Esc] 中断⟧")
    f.add(" ⟦cm|?⟧ ⟦cm|Skill⟧ ⟦bs3| migration/cpp-to-kunpeng ⟧")
    f.add("   ⟦cm|Tool⟧  ⟦pr|●⟧ edit_file ⟦cm|crypto.c 3/12⟧ ⟦pr|⠹⟧")
    f.add("   ⟦cm|进度⟧  " + bar(0.72, 27, "g6") + " ⟦t|72%⟧")
    f.sep()
    f.add(" ⟦cm|证据折叠为一行⟧ ⟦ac|[1] #4471⟧ ⟦ac|[2] §B2.5⟧  ⟦pr|[i] 展开⟧")
    f.sep()
    f.add(" ⟦pr|❯⟧ ▌")
    f.foot(
        "⟦bs4| migrate ⟧ ⟦cm|mode:⟧⟦ok|auto⟧",
        "⟦cm|ctx:⟧⟦wn|72% ⚠⟧⟦cm| · Dock 3 列图标条 · console 6 行⟧",
    )
    return check(f.render(), 80, "workspace-narrow")


# ══════════════════════════════════════════════════════════════════════
# 屏 3 · Agent 执行中 · Tool + Diff
# ══════════════════════════════════════════════════════════════════════
def screen_exec() -> str:
    """执行中：工程树 27 · 代码区 68 · 执行与审查 61。
    diff 用整行底色带（dangerBackground / successBackground）+ 左侧竖条，
    删除行与新增行共用同一个行号——改的是同一处，不是新增了一行。"""
    tree, code, side = 27, 68, 61
    assert tree + code + side + 2 == INNER

    f = Frame(
        W,
        "⟦br|▪⟧ ⟦t|DevKit AI⟧ ⟦cm|· migrate nginx⟧",
        "⟦pr|●⟧ ⟦t|Running⟧ ⟦cm|· 步骤 3/5 · 2m14s⟧",
    )
    f.sep(colsep([tree, code, side], mid="┬"))

    tree_p = Pane(tree).add(
        "⟦bs2| ⟧⟦bs2|⟦cm|资源管理器⟧⟦bs2|        ⟧⟦cm|⟦bs2|Ctrl+E⟧⟧⟦bs2| ⟧",
        "",
        " ⟦cm|N G I N X - M A I N⟧",
        "  ⟦cm|└ src/⟧",
        "⟦bsel|    ⟦pr|▎⟧⟦bsel|crypto.c⟧⟦bsel|          ⟧⟦wn|M⟧⟦bsel| ⟧⟧",
        "     ⟦cm|memory.c⟧          ⟦wn|M⟧",
        "     ⟦cm|http.c⟧",
        "     ⟦cm|ngx_core.h⟧",
        "  ⟦cm|└ conf/⟧",
        "     ⟦cm|nginx.conf⟧        ⟦wn|M⟧",
        "  ⟦cm|kunpeng.patchset⟧     ⟦ok|A⟧",
        "  ⟦cm|configure⟧",
        "",
        " ⟦cm|迁移状态⟧",
        " ⟦cm|待审改动⟧            ⟦wn|3⟧",
        " ⟦cm|已接受⟧              ⟦ok|9⟧",
        " ⟦cm|需人工确认⟧          ⟦wn|2⟧",
        "",
        " ⟦cm|⇄ 跟随 Agent 当前文件⟧",
    )

    code_p = Pane(code).add(
        spread(" ⟦t|crypto.c⟧", "⟦cm|nginx-main · C · UTF-8 · LF⟧ ", code),
        " ⟦cm|nginx › src › ⟧⟦ac|crypto.c⟧⟦cm| › ngx_crypto_spin_wait()⟧",
        "",
        " ⟦cm|80⟧  ⟦cm|/* 自旋等待：x86 用 PAUSE 降低流水线开销 */⟧",
        " ⟦cm|81⟧",
        " ⟦cm|82⟧  ⟦ac|static⟧⟦cm| ngx_int_t⟧",
        " ⟦cm|83⟧  ⟦cm|ngx_crypto_spin_wait(ngx_atomic_t *lock, ngx_uint_t spin)⟧",
        " ⟦cm|84⟧  ⟦cm|{⟧",
        " ⟦cm|85⟧      ⟦ac|for⟧⟦cm| ( ;; ) {⟧",
        " ⟦cm|86⟧          ⟦ac|while⟧⟦cm| (spin--) {⟧",
        "⟦bdel| ⟧⟦er|⟦bdel|87⟧⟧⟦bdel| ⟧⟦er|▌⟧⟦bdel|" + pad("             _mm_pause();", code - 5) + "⟧",
        "⟦badd| ⟧⟦ok|⟦badd|87⟧⟧⟦badd| ⟧⟦ok|▌⟧⟦badd|"
        + pad('             __asm__ __volatile__("yield" ::: "memory");', code - 5)
        + "⟧",
        " ⟦cm|88⟧          ⟦cm|}⟧",
        " ⟦cm|89⟧",
        " ⟦cm|90⟧      ⟦ac|if⟧⟦cm| (ngx_atomic_cmp_set(lock, ⟧⟦o4|0⟧⟦cm|, ⟧⟦o4|1⟧⟦cm|)) {⟧",
        " ⟦cm|91⟧          ⟦ac|return⟧⟦cm| NGX_OK;⟧",
        " ⟦cm|92⟧      ⟦cm|}⟧",
        " ⟦cm|93⟧  ⟦cm|}⟧",
        "",
        " ⟦cm|只高亮变化的 token —— 一眼看出「到底改动了什么」⟧",
        " ⟦cm|为什么⟧  x86 ⟦t|PAUSE⟧ 在 ARM 无对应指令，⟦t|YIELD⟧ 语义等价",
        " ⟦cm|证据⟧    ⟦ac|[1]⟧ ⟦cm|案例库 #4471⟧   ⟦ac|[2]⟧ ⟦cm|ARM ARM §B2.5⟧",
        " ⟦cm|影响⟧    ⟦bs3| Compatibility Fixed ⟧ ⟦cm|· Perf +3% · 同类调用点 3 处⟧",
    )

    side_p = Pane(side).add(
        " ⟦cm|执行过程⟧" + pad("", 34) + "⟦cm|[l] 折叠⟧",
        " ⟦ok|✓⟧ ⟦cm|Thinking⟧        ⟦cm|意图 = 源码迁移⟧",
        " ⟦ok|✓⟧ ⟦cm|Loading Skill⟧   ⟦bs3| migration/cpp-to-kunpeng ⟧",
        " ⟦ok|✓⟧ ⟦cm|read_file⟧       ⟦cm|CMakeLists.txt⟧",
        " ⟦ok|✓⟧ ⟦cm|search⟧          ⟦cm|boost · 3 hits⟧",
        " ⟦pr|▶⟧ ⟦t|edit_file⟧       ⟦cm|crypto.c⟧ ⟦pr|⠹⟧ ⟦cm|1.8s⟧",
        " ⟦cm|○ run_command⟧     ⟦cm|make -j16⟧",
        " ⟦cm|进度⟧ " + bar(0.72, 30, "g6") + " ⟦t|72%⟧ ⟦cm|9/12⟧",
        "",
        " ⟦cm|待审 hunk⟧" + pad("", 33) + "⟦cm|[/] 过滤⟧",
        " ⟦ok|✓⟧ ⟦cm|1  crypto.c:12   immintrin.h → arm_neon.h⟧",
        " ⟦ok|✓⟧ ⟦cm|2  crypto.c:31   _mm_prefetch → __builtin⟧",
        "⟦bsel| ⟦pr|▎⟧⟦bsel|⟦t|⟦bsel|3  crypto.c:87   _mm_pause → yield⟧⟧⟦bsel|" + " " * 21 + "⟧⟧",
        " ⟦cm|○ 4  memory.c:88   对齐 64 → 128⟧ ⟦wn|⚠ 需人工⟧",
        " ⟦cm|○ 5  event.c:203   ia32_pause → yield⟧",
        " ⟦cm|… 7 more⟧",
        "",
        spread(
            " ⟦pr|[Y] 接受本 hunk⟧   ⟦cm|[N] 拒绝⟧   ⟦cm|[E] 编辑⟧",
            "⟦cm|[A] 全接受⟧ ",
            side,
        ),
        " ⟦cm|[J/K] 上下 hunk · 键位在任何宽度下都不挪位⟧",
        "",
        *panel(
            side - 1,
            "⟦wn|⚠ 高危操作确认⟧",
            [
                "⟦er|rm -rf ./build-arm64⟧",
                "⟦cm|清空旧产物后重新交叉编译，不可撤销⟧",
                "⟦cm|[N] 取消⟧   ⟦bpri| [Y] 确认执行 ⟧   ⟦cm|[S] 本会话不再问⟧",
            ],
        ),
    )

    for line in hcat([tree_p, code_p, side_p]):
        f.add(line)
    f.sep()
    f.add(
        spread(
            " ⟦pr|❯⟧ memory.c 那处对齐先别改，等我确认过缓存行大小▌",
            "⟦cm|Esc 中断后可直接说，不必等它跑完⟧ ",
            INNER,
        )
    )
    f.foot(
        "⟦bs4| migrate nginx ⟧ ⟦cm|mode:⟧⟦ok|auto⟧⟦cm| │ model:qwen2.5-72b │ ctx:⟧⟦wn|72% ⚠⟧",
        "⟦cm|已接受 ⟧⟦ok|9⟧⟦cm| · 待审 ⟧⟦wn|3⟧⟦cm| · patch 3/12 · 12:09⟧",
    )
    return check(f.render(), W, "exec")


def screen_exec_narrow() -> str:
    f = Frame(80, "⟦t|migrate nginx⟧", "⟦pr|●⟧ ⟦cm|Running 步骤 3/5⟧")
    f.add(" ⟦cm|执行⟧ ⟦sel| Diff ⟧ ⟦cm|证据⟧                          ⟦cm|[Tab] 切页⟧")
    f.sep()
    f.add(" ⟦t|src/crypto.c⟧  ⟦cm|hunk 3/12⟧")
    f.add(" ⟦cm|86⟧      ⟦cm|while (spin--) {⟧")
    f.add("⟦bdel| ⟧⟦er|⟦bdel|87⟧⟧⟦bdel| ⟧⟦er|▌⟧⟦bdel|" + pad("     _mm_pause();", 70) + "⟧")
    f.add(
        "⟦badd| ⟧⟦ok|⟦badd|87⟧⟧⟦badd| ⟧⟦ok|▌⟧⟦badd|"
        + pad('     __asm__ __volatile__("yield" ::: "memory");', 70)
        + "⟧"
    )
    f.add(" ⟦cm|88⟧      ⟦cm|}⟧")
    f.add("")
    f.add(" ⟦cm|为什么⟧ PAUSE 无 ARM 对应指令，YIELD 语义等价")
    f.add(" ⟦cm|证据⟧   ⟦ac|[1] #4471⟧  ⟦ac|[2] ARM ARM §B2.5⟧")
    f.sep()
    f.add(" ⟦pr|[y] 接受⟧ ⟦cm|[n] 拒绝⟧ ⟦cm|[e] 编辑⟧ ⟦cm|[a] 全接受⟧ ⟦cm|[J/K] 换 hunk⟧")
    f.foot("⟦cm|[Esc]⟧ 中断", "⟦ok|9⟧⟦cm| 接受 · ⟧⟦wn|3⟧⟦cm| 待审 · single-canvas 单栏轮播⟧")
    return check(f.render(), 80, "exec-narrow")


# ══════════════════════════════════════════════════════════════════════
# 屏 4 · Result / 任务结果页（可视化报告 · 火焰图 · 热点函数）
# ══════════════════════════════════════════════════════════════════════
HOT = [
    # (符号, 函数, 占比, 周期数, 进程, 库/文件, 色阶)
    ("▸", "inc_b", 50.00, "78,376,139,465", "falsesharing", "falsesharinglong.c", "o3"),
    ("▸", "sum_a", 50.00, "78,375,676,449", "falsesharing", "falsesharinglong.c", "o3"),
    (" ", "__libc_start_main", 0.42, "658,214,003", "falsesharing", "…/libc.so.6", "o6"),
    (" ", "finish_task_switch.isra…", 0.18, "281,004,551", "swapper", "[kernel]", "o8"),
    (" ", "default_idle_call", 0.11, "170,338,092", "swapper", "[kernel]", "o8"),
    (" ", "ktime_get", 0.07, "109,772,410", "swapper", "[kernel]", "o8"),
]


def screen_result() -> str:
    left, right = 97, 60
    assert left + right + 1 == INNER

    f = Frame(
        W,
        "⟦ok|✓⟧ ⟦t|Task Completed⟧ ⟦cm|· hotspot · falsesharing_long @ Kunpeng 920⟧",
        "⟦cm|采集 30s · 19:59:51 → 20:00:21⟧",
    )
    f.add(
        " ⟦t|结论⟧  两个线程函数各占 ⟦t|50%⟧ 周期，热点收敛到同一条 cacheline —— "
        "⟦wn|判定为伪共享（false sharing）⟧⟦cm|，置信度 93%⟧"
    )
    f.sep(colsep([left, right]))

    # 列宽：符号 2 · 函数 26 · 占比 bar 12 + 数值 8 · 周期数 15 · 进程 15 · 库 19
    lp = Pane(left)
    lp.add(
        " ⟦t|Top 30 热点函数⟧   ⟦cm|分组⟧ ⟦sel| 函数/调用栈 ⟧"
        + pad("", 12)
        + "⟦cm|[g] 换分组   [/] 搜索   [↵] 展开调用栈⟧",
        "  "
        + pad("⟦cm|函数 / 调用栈⟧", 26)
        + pad("⟦cm|周期数占比 ▾⟧", 20)
        + pad("⟦cm|周期数⟧", 15, "right")
        + pad("⟦cm|  进程名⟧", 15)
        + "⟦cm|共享库 / 文件⟧",
    )
    for sym, fn, pct, cycles, proc, lib, cls in HOT:
        name = f"⟦t|{fn}⟧" if pct > 10 else f"⟦cm|{fn}⟧"
        lp.add(
            f" ⟦pr|{sym}⟧"
            + pad(" " + name, 26)
            + bar(pct / 100, 11, cls)
            + pad(f"{pct:7.2f}% ", 9)
            + pad(cycles, 15, "right")
            + f"  ⟦cm|{pad(proc, 13)}⟧⟦cm|{lib}⟧"
        )
    lp.add(
        "    ⟦cm|… 24 more⟧" + pad("", 40) + "⟦cm|[n] 下一页 · 1/3⟧",
        "",
        " ⟦t|火焰图⟧ ⟦cm|自底向上 · 宽度 = 周期数占比⟧    "
        "⟦g4|██⟧⟦cm| 用户态 ⟧⟦a4|██⟧⟦cm| 内核态 ⟧⟦v4|██⟧⟦cm| 其他 ⟧⟦sel|  ⟧⟦cm| 搜索标记⟧",
    )
    # 三类着色由图例定死（用户态 g / 内核态 a / 其他 v），**深度只改档位不改色相**——
    # 换个色相就等于宣布这一帧属于另一类，图例立刻对不上。
    flame = [
        ([("g6", 58)], "all"),
        ([("g4", 57)], "falsesharing(367078)"),
        ([("g6", 56)], "__libc_start_main  ·  libc.so.6"),
        ([("g4", 56)], "main  ·  falsesharinglong.c"),
        ([("g6", 27), ("g6", 27)], "start_thread ×2  ·  pthread"),
        ([("g3", 27), ("g3", 26)], "⟦t|inc_b⟧ / ⟦t|sum_a⟧  ·  各 50%"),
    ]
    for segs, note in flame:
        drawn = " ".join(f"⟦{c}|{'█' * n}⟧" for c, n in segs)
        lp.add(" " + pad(drawn, 58) + f"  ⟦cm|{note}⟧")
    lp.add(
        " " + pad("⟦a4|███⟧", 58) + "  ⟦cm|内核态合计 0.36%⟧   ⟦wn|3 帧过窄未显示⟧",
        "",
        " ⟦t|采集参数⟧" + pad("", 44) + "⟦cm|[t] 任务信息  [r] 重新采集⟧",
        " ⟦cm|事件⟧ cycles · ⟦cm|频率⟧ 1000Hz · ⟦cm|时长⟧ 30s · ⟦cm|有效采样⟧ 12,404",
        " ⟦cm|目标⟧ falsesharing_long ⟦cm|(pid 367078)⟧ · ⟦cm|线程⟧ 2 · ⟦cm|绑核⟧ CPU2 / CPU3",
        " ⟦cm|环境⟧ Kunpeng 920 · 64 核 · ⟦t|L1D cacheline 128B⟧ · openEuler 22.03 LTS",
    )

    rp = Pane(right)
    rp.add(
        " ⟦t|源码热点⟧ ⟦cm|falsesharinglong.c⟧        ⟦cm|[o] 打开⟧",
        " ⟦cm|115 ⟧ ⟦cm|  if(CPU_ISSET(3, &get)){⟧",
        " ⟦cm|116 ⟧ ⟦cm|    printf(\"inc_b is running\");⟧",
        " ⟦cm|117 ⟧ ⟦cm|  }⟧",
        " ⟦cm|118 ⟧⟦cm| 1.35%⟧ ⟦cm|  for (int i = 0; i < TIME_S; ++i){⟧",
        " ⟦cm|119 ⟧",
        " ⟦sel|120 ⟧⟦er|98.65%⟧⟦sel|    ++f.y;                          ⟧",
        " ⟦cm|121 ⟧",
        " ⟦cm|122 ⟧ ⟦cm|  }⟧",
        "",
        " ⟦wn|⚠ AI 判定⟧  ⟦t|伪共享 false sharing⟧  ⟦cm|93%⟧",
        " ⟦cm|f.x 与 f.y 相邻 8 字节，落在同一条⟧",
        " ⟦cm|128B cacheline（鲲鹏 920 L1D 行长）；⟧",
        " ⟦cm|两线程分别绑核 2 / 3，写各自变量却⟧",
        " ⟦cm|反复让对方缓存行失效。⟧",
        " ⟦cm|修复⟧  struct 成员按 ⟦t|128B⟧ 对齐分离",
        "",
        " ⟦t|下一步⟧",
        " ⟦pr|▸ [1]⟧ 应用 aligned(128) 补丁并重测  ⟦cm|~2min⟧",
        " ⟦cm|  [2]⟧ ⟦cm|看 NUMA 亲和热力，确认绑核合理⟧",
        " ⟦cm|  [3]⟧ ⟦cm|导出热点分析报告⟧",
        " ⟦pr|❯⟧ ⟦cm|或直接说你想干什么▌⟧",
        "",
        " ⟦t|产出⟧                        ⟦cm|[E] 导出⟧",
        " ├ ⟦ac|hotspot-report.md⟧  ⟦cm|18KB⟧",
        " ├ ⟦ac|flamegraph.svg⟧     ⟦cm|241KB⟧",
        " └ ⟦ac|perf.data⟧          ⟦cm|218MB · 不随报告导出⟧",
    )
    for line in hcat([lp, rp]):
        f.add(line)
    f.foot(
        "⟦bs4| hotspot ⟧ ⟦cm|mode:⟧⟦ok|auto⟧⟦cm| │ model:qwen2.5-72b │ ctx:38%⟧",
        "⟦cm|[↵] 下钻 · [E] 导出 · Session #1031 · 丢样 ⟧⟦ok|0.2%⟧",
    )
    return check(f.render(), W, "result")


def cut_note(name: str, note: str) -> str:
    return f"  {name}" + (f"  ·  {note}" if note else "")


def screen_result_narrow() -> str:
    f = Frame(80, "⟦ok|✓⟧ ⟦t|hotspot⟧ ⟦cm|falsesharing_long⟧", "⟦cm|30s⟧")
    f.add(" ⟦t|结论⟧ 两函数各占 50% 周期 · ⟦wn|伪共享⟧ ⟦cm|93%⟧")
    f.sep()
    f.add(" ⟦t|Top 热点⟧                              ⟦cm|[↵] 下钻⟧")
    f.add(" ⟦pr|▸⟧ inc_b            " + bar(0.5, 10, "o3") + " ⟦t|50.00%⟧")
    f.add(" ⟦pr|▸⟧ sum_a            " + bar(0.5, 10, "o3") + " ⟦t|50.00%⟧")
    f.add(" ⟦cm|  __libc_start_main⟧  " + bar(0.004, 10, "o6") + " ⟦cm| 0.42%⟧")
    f.add(" ⟦cm|  … 27 more · 周期数/进程/库列已隐藏，[↵] 看详情⟧")
    f.sep()
    f.add(" ⟦t|火焰图⟧ ⟦cm|降到 3 层⟧      ⟦g4|██⟧⟦cm| 用户态 ⟧⟦a4|██⟧⟦cm| 内核态⟧")
    f.add(" ⟦g6|" + "█" * 60 + "⟧⟦cm|  all⟧")
    f.add(" ⟦g3|" + "█" * 29 + "⟧ ⟦g3|" + "█" * 29 + "⟧⟦cm|  inc_b/sum_a⟧")
    f.add(" ⟦wn|9 帧过窄未显示⟧")
    f.sep()
    f.add(" ⟦sel|120⟧⟦er| 98.65%⟧ ⟦cm|++f.y;⟧   ⟦cm|→ 同一 128B cacheline⟧")
    f.foot("⟦pr|[1]⟧ 应用补丁重测", "⟦cm|[E] 导出 · <100 列降级⟧")
    return check(f.render(), 80, "result-narrow")


# ══════════════════════════════════════════════════════════════════════
# 屏 5 · 管理配置（服务器 · 账号 · 模型）
# ══════════════════════════════════════════════════════════════════════
CAT, LIST, DET = 22, 44, 90  # 22 + 44 + 90 + 2 分隔 = 158


def settings_categories(active: str) -> Pane:
    """左侧分类栏。选中项走反显，不靠颜色——16 色降级下仍成立。"""
    rows = [
        ("服务器", "3"),
        ("账号", "2"),
        ("模型", "4"),
        ("Skill", "12"),
        ("通用", ""),
        ("更新", ""),
    ]
    p = Pane(CAT).add(" ⟦t|SETTINGS⟧       ⟦cm|Ctrl+,⟧", "")
    for name, count in rows:
        mark = "▶" if name == active else "○"
        line = f" {mark} {name}"
        tail = f"⟦wn|有新版⟧" if name == "更新" else f"⟦cm|{count}⟧"
        body = pad(line, CAT - width(tail) - 1) + tail + " "
        p.add(f"⟦sel|{body}⟧" if name == active else f"⟦cm|{body}⟧")
    p.add(
        "",
        " ⟦cm|所有凭据⟧",
        " ⟦cm|AES-256-GCM 加密⟧",
        " ⟦cm|~/.devkitai/⟧",
        " ⟦cm|credentials · 600⟧",
        "",
        " ⟦ok|✕⟧ ⟦cm|不写日志⟧",
        " ⟦ok|✕⟧ ⟦cm|不随报告导出⟧",
        " ⟦ok|✕⟧ ⟦cm|不进 Session 快照⟧",
    )
    return p


MODELS = [
    # (名称, 上下文, 工具调用, 结构化输出, 实测延迟, 是否当前)
    ("qwen2.5-72b-instruct", "128k", "✓", "✓", "218ms", True),
    ("qwen2.5-32b-instruct", "64k", "✓", "✓", "140ms", False),
    ("deepseek-v3", "128k", "✓", "✓", "— 未测", False),
    ("embed-v2", "8k", "✕", "✕", "— 仅向量", False),
]


def model_table() -> list[str]:
    """模型对比表：列宽写死一处，表头与行共用，避免两边各数一遍空格。"""
    cols = (24, 9, 8, 13, 12)
    head = "  " + "".join(
        pad(f"⟦cm|{t}⟧", w, "left" if i == 0 else "right")
        for i, (t, w) in enumerate(zip(("模型", "上下文", "工具", "结构化输出", "实测延迟"), cols))
    )
    out = [head]
    for name, ctx, tool, so, lat, current in MODELS:
        cells = pad(name, cols[0] - 2) + "".join(
            pad(v, w, "right") for v, w in zip((ctx, tool, so, lat), cols[1:])
        )
        out.append(
            f"⟦sel| ▶ {cells} ⟧" if current else f"⟦cm|   {cells}⟧ "
        )
    return out


def screen_settings_model() -> str:
    f = Frame(
        W,
        "⟦br|▪⟧ ⟦t|DevKit AI⟧ ⟦cm|· 管理配置⟧",
        "⟦cm|模型⟧ ⟦ok|●⟧ ⟦cm|已连接 · ⟧⟦t|qwen2.5-72b⟧",
    )
    f.sep(colsep([CAT, LIST, DET], mid="┬"))

    lst = Pane(LIST).add(
        " ⟦t|Provider⟧              ⟦cm|[n] 新增  [Del] 删除⟧",
        " ⟦sel|▶ devkit-gateway   ⟧ ⟦ok|●⟧ ⟦cm|已连接 · 4 模型⟧",
        " ⟦cm|  openai-compat     ○ 未验证⟧",
        " ⟦cm|  vllm@10.10.3.21   ⟧⟦ok|●⟧ ⟦cm|已连接 · 1 模型⟧",
        " ⟦cm|  ollama (本地)     ⟧⟦er|✕⟧ ⟦er|连接失败⟧",
        "",
        " ⟦t|当前使用⟧",
        " ⟦ok|●⟧ qwen2.5-72b-instruct",
        "   ⟦cm|devkit-gateway · ctx 128k⟧",
        " ⟦cm|兜底⟧ qwen2.5-32b ⟦cm|（主模型不可用时）⟧",
        "",
        " ⟦t|用量⟧               ⟦cm|本月⟧",
        " ⟦cm|请求⟧  12,480",
        " ⟦cm|配额⟧  " + bar(0.18, 14, "g4") + " ⟦cm|18%⟧",
        "",
        " ⟦wn|⚠⟧ ⟦cm|ollama 连接失败⟧",
        " ⟦cm|  已自动跳过，不影响当前任务⟧",
        " ⟦cm|  [↵] 看诊断⟧",
    )

    det = Pane(DET).add(
        spread(" ⟦t|devkit-gateway⟧", "⟦cm|[e] 编辑   [t] 重测   [s] 设为默认⟧ ", DET),
        "",
        " ⟦cm|Base URL⟧  https://devkit-ai.example.com⟦t|/v1⟧",
        "            ⟦ok|✓⟧ ⟦cm|格式正确 · 含 /v1 · https⟧",
        spread(" ⟦cm|API Key ⟧  sk-a1f2⟦cm|****************⟧9c4d", "⟦cm|[r] 轮换   [x] 删除⟧ ", DET),
        "            ⟦cm|只回显首尾，粘贴后不再明文出现；90 天后过期⟧",
        " ⟦cm|代理    ⟧  ⟦cm|继承系统 HTTPS_PROXY⟧",
        "",
        spread(" ⟦t|就地验证⟧", "⟦cm|刚刚 · [t] 重测全部⟧ ", DET),
        " ⟦ok|✓⟧ 地址可达          ⟦cm|42ms⟧",
        " ⟦ok|✓⟧ 鉴权通过          ⟦cm|账号 dev-team · 配额剩余 82%⟧",
        " ⟦ok|✓⟧ 拉取模型列表      ⟦cm|4 个⟧",
        " ⟦ok|✓⟧ 测试对话          ⟦cm|218ms · 首 token 96ms⟧",
        " ⟦ok|✓⟧ 工具调用          ⟦cm|function calling 可用⟧",
        "",
        *model_table(),
        " ⟦pr|[↵] 设为当前⟧   ⟦cm|[b] 设为兜底   [i] 看能力详情⟧",
    )

    for line in hcat([settings_categories("模型"), lst, det]):
        f.add(line)
    f.sep()
    f.add(
        spread(
            " ⟦cm|改动即时生效，不需要重启；正在运行的任务用旧模型跑完当前步骤⟧",
            "⟦cm|[Esc] 返回工作台⟧ ",
            INNER,
        )
    )
    f.foot(
        "⟦cm|[Tab]⟧ 切换区域  ⟦cm|[↑↓]⟧ 选择  ⟦cm|[↵]⟧ 应用",
        "⟦cm|凭据加密存储 · ⟧⟦ok|●⟧ ⟦cm|已连接⟧",
    )
    return check(f.render(), W, "settings-model")


def screen_settings_server() -> str:
    f = Frame(
        W,
        "⟦br|▪⟧ ⟦t|DevKit AI⟧ ⟦cm|· 管理配置⟧",
        "⟦cm|服务器⟧ ⟦ok|●⟧ ⟦cm|kp920-dev-01 已连接⟧",
    )
    f.sep(colsep([CAT, LIST, DET], mid="┬"))

    lst = Pane(LIST).add(
        " ⟦t|远程服务器⟧          ⟦cm|[n] 新增  [c] 连接⟧",
        " ⟦sel|▶ kp920-dev-01    ⟧ ⟦ok|●⟧ ⟦cm|12ms⟧",
        "   ⟦cm|10.10.3.21 · aarch64 · Kunpeng 920⟧",
        " ⟦cm|  kp920-perf-02   ○ 未连接⟧",
        "   ⟦cm|10.10.3.22 · aarch64 · 专用压测机⟧",
        " ⟦cm|  x86-build-01    ⟧⟦wn|⚠ 指纹变更⟧",
        "   ⟦cm|10.10.4.7 · x86_64⟧",
        "",
        " ⟦t|本机⟧",
        " ⟦cm|macOS · arm64 · 非鲲鹏⟧",
        " ⟦cm|可本地完成：源码扫描 · 静态分析⟧",
        " ⟦wn|需要远端：交叉编译 · 性能采集⟧",
        "",
        " ⟦t|默认落点⟧",
        " ⟦cm|编译⟧  kp920-dev-01",
        " ⟦cm|采集⟧  kp920-perf-02 ⟦cm|（专机避免干扰）⟧",
        " ⟦cm|[e] 改落点规则⟧",
    )

    det = Pane(DET).add(
        spread(" ⟦t|kp920-dev-01⟧", "⟦cm|[e] 编辑   [r] 重探测   [k] 断开⟧ ", DET),
        "",
        spread(" ⟦cm|地址⟧    dev@10.10.3.21:22", "⟦cm|[c] 复制 ssh 命令⟧ ", DET),
        spread(
            " ⟦cm|认证⟧    公钥 ~/.ssh/id_ed25519 ⟦cm|（已加载）⟧",
            "⟦cm|[p] 改用密码 / 跳板机⟧ ",
            DET,
        ),
        " ⟦cm|指纹⟧    SHA256:9f3a…c71d   ⟦ok|✓⟧ ⟦cm|已确认 2026-08-02⟧",
        "         ⟦cm|指纹变化时一律拦截并要求重新确认，不提供「永久忽略」⟧",
        "",
        spread(" ⟦t|环境探测⟧", "⟦cm|3 分钟前 · [r] 重探测⟧ ", DET),
        " ⟦ok|✓⟧ 架构          ⟦cm|aarch64 · Kunpeng 920 · 64 核 · 4 NUMA⟧",
        " ⟦ok|✓⟧ 系统          ⟦cm|openEuler 22.03 LTS · kernel 5.10⟧",
        " ⟦ok|✓⟧ DevKit        ⟦cm|24.0.RC1 · MCP 工具 6 个可用⟧",
        " ⟦ok|✓⟧ 编译器        ⟦cm|gcc 10.3 · BiSheng 3.2⟧",
        spread(
            " ⟦wn|⚠⟧ perf 权限     ⟦wn|perf_event_paranoid=2⟧⟦cm| → 只能采自己的进程⟧",
            "⟦pr|[F] 修复⟧ ",
            DET,
        ),
        spread(" ⟦er|✕⟧ 交叉工具链    ⟦cm|未装 aarch64-linux-gnu-gcc⟧", "⟦pr|[I] 安装⟧ ", DET),
        "",
        spread(" ⟦t|连通性⟧    延迟 ⟦ok|12ms⟧ · 带宽 ⟦cm|92MB/s⟧ · 丢包 ⟦ok|0%⟧",
          "⟦cm|按 SSH 低带宽档渲染⟧ ", DET),
        " ⟦cm|文件同步⟧  ⟦cm|工程目录 rsync 增量 · 排除 .git 与 build 产物⟧",
        "",
        " ⟦cm|本机非鲲鹏时，迁移编译与性能采集按上面的落点规则自动跑在这台上，⟧",
        " ⟦cm|用户不需要先手工 ssh 过去。⟧",
    )

    for line in hcat([settings_categories("服务器"), lst, det]):
        f.add(line)
    f.sep()
    f.add(
        spread(
            " ⟦wn|⚠⟧ ⟦cm|x86-build-01 的主机指纹与上次不一致，已暂停对它的所有任务⟧",
            "⟦pr|[↵] 去核对⟧ ",
            INNER,
        )
    )
    f.foot(
        "⟦bs4| settings ⟧ ⟦cm|[Tab] 切换区域 │ [c] 连接 │ [n] 新增服务器⟧",
        "⟦cm|3 台 · ⟧⟦ok|1 已连接⟧⟦cm| · ⟧⟦wn|1 待核对⟧",
    )
    return check(f.render(), W, "settings-server")


def screen_settings_account() -> str:
    f = Frame(
        W,
        "⟦br|▪⟧ ⟦t|DevKit AI⟧ ⟦cm|· 管理配置⟧",
        "⟦cm|账号⟧ ⟦wn|⚠⟧ ⟦cm|1 项凭据需要处理⟧",
    )
    f.sep(colsep([CAT, LIST, DET], mid="┬"))

    lst = Pane(LIST).add(
        " ⟦t|账号与凭据⟧            ⟦cm|[n] 新增⟧",
        " ⟦sel|▶ 知识库访问令牌   ⟧ ⟦er|✕ 已过期⟧",
        " ⟦cm|  华为云 / DevKit   ⟧⟦ok|●⟧ ⟦cm|已登录⟧",
        "   ⟦cm|dev-team@example.com · SSO⟧",
        " ⟦cm|  Git 凭据         ⟧⟦ok|●⟧ ⟦cm|ssh-agent⟧",
        "",
        " ⟦t|到期提醒⟧",
        " ⟦er|✕⟧ ⟦cm|知识库令牌⟧   ⟦er|已过期 2 天⟧",
        " ⟦wn|⚠⟧ ⟦cm|API Key⟧      ⟦wn|30 天后⟧",
        " ⟦ok|✓⟧ ⟦cm|SSO 会话⟧     ⟦cm|还有 6 天⟧",
        " ⟦cm|  过期前 30 天开始提醒，⟧",
        " ⟦cm|  不到当天才报错。⟧",
        "",
        " ⟦t|遥测⟧",
        " ⟦cm|使用数据上报⟧  ⟦er|✕ 已关闭⟧",
        " ⟦cm|崩溃日志上报⟧  ⟦er|✕ 已关闭⟧",
        " ⟦cm|默认全关，开关在这里且只在这里⟧",
    )

    det = Pane(DET).add(
        spread(" ⟦t|知识库访问令牌⟧", "⟦cm|[r] 重新登录   [t] 粘贴新令牌⟧ ", DET),
        "",
        " ⟦cm|用途⟧    鲲鹏知识库 · 迁移案例库检索 ⟦cm|（Agent 引用证据的来源）⟧",
        spread(" ⟦cm|令牌⟧    kb-3f9a⟦cm|**********⟧7c21", "⟦cm|输入时掩码，可粘贴⟧ ", DET),
        " ⟦cm|权限⟧    ⟦ok|✓⟧ 知识库读   ⟦ok|✓⟧ 案例库读   ⟦er|✕⟧ ⟦cm|写（本产品不需要）⟧",
        " ⟦cm|存储⟧    ~/.devkitai/credentials · ⟦cm|0600 · AES-256-GCM⟧",
        "",
        *panel(
            DET - 2,
            "⟦er|✕ 上次验证失败⟧",
            [
                spread("⟦cm|发生了什么⟧   知识库令牌鉴权失败", "⟦cm|HTTP 401⟧", DET - 6),
                "⟦cm|为什么    ⟧   令牌已于 ⟦t|2026-08-15⟧ 过期（有效期 90 天）",
                "⟦cm|怎么解决  ⟧   ⟦pr|[r] 重新登录 SSO 自动换发⟧   ⟦cm|或⟧   ⟦cm|[t] 粘贴新令牌⟧",
                "",
                "⟦cm|影响面：Agent 仍可工作，但改动将失去案例库证据；"
                "屏 3 的「证据」区会显示为不可用。⟧",
            ],
            right="⟦cm|刚刚⟧",
        ),
        "",
        " ⟦t|凭据纪律⟧",
        *[
            pad(f" ⟦ok|✓⟧ ⟦cm|{yes}⟧", 40) + f"⟦er|✕⟧ ⟦cm|{no}⟧"
            for yes, no in (
                ("输入即掩码，回显只留首尾", "不写入任何日志与终端回滚缓冲"),
                ("静态加密，文件权限 0600", "不随报告 / Session 快照导出"),
                ("支持系统钥匙串托管", "不发送给模型，不进上下文"),
            )
        ],
    )

    for line in hcat([settings_categories("账号"), lst, det]):
        f.add(line)
    f.sep()
    f.add(
        spread(
            " ⟦er|✕⟧ ⟦cm|知识库令牌已过期，涉及案例检索的步骤会降级为「无证据」并在改动上标注⟧",
            "⟦pr|[r] 现在处理⟧ ",
            INNER,
        )
    )
    f.foot(
        "⟦cm|[Tab]⟧ 切换区域  ⟦cm|[r]⟧ 重新登录  ⟦cm|[x]⟧ 删除凭据",
        "⟦cm|4 项凭据 · ⟧⟦er|1 过期⟧⟦cm| · ⟧⟦wn|1 将到期⟧",
    )
    return check(f.render(), W, "settings-account")


def screen_settings_narrow() -> str:
    f = Frame(80, "⟦t|管理配置⟧", "⟦wn|⚠⟧ ⟦cm|1 项待处理⟧")
    f.add(" ⟦cm|服务器⟧  ⟦cm|账号⟧  ⟦sel| 模型 ⟧  ⟦cm|Skill⟧  ⟦cm|通用⟧  ⟦cm|更新⟧   ⟦cm|[Tab] 切分类⟧")
    f.sep()
    f.add(" ⟦t|Provider⟧  ⟦sel| devkit-gateway ⟧ ⟦ok|●⟧      ⟦cm|[↵] 换一个⟧")
    f.add(" ⟦cm|Base URL⟧  ⟦cm|…/devkit-ai/⟧⟦t|v1⟧            ⟦ok|✓⟧")
    f.add(" ⟦cm|API Key ⟧  sk-a1f2⟦cm|****⟧9c4d          ⟦cm|[r] 轮换⟧")
    f.sep()
    f.add(" ⟦t|就地验证⟧                          ⟦cm|[t] 重测⟧")
    f.add(" ⟦ok|✓⟧ ⟦cm|可达 42ms⟧   ⟦ok|✓⟧ ⟦cm|鉴权⟧   ⟦ok|✓⟧ ⟦cm|模型 4 个⟧")
    f.add(" ⟦ok|✓⟧ ⟦cm|对话 218ms⟧  ⟦ok|✓⟧ ⟦cm|工具调用⟧")
    f.sep()
    f.add(" ⟦t|当前模型⟧ qwen2.5-72b-instruct ⟦cm|· 128k · 工具 ✓⟧")
    f.add(" ⟦cm|窄屏隐藏模型对比表，[↵] 进列表逐个看⟧")
    f.foot("⟦cm|[Esc]⟧ 返回", "⟦cm|<100 列 · 三栏塌为分类页签⟧")
    return check(f.render(), 80, "settings-narrow")


# ══════════════════════════════════════════════════════════════════════
# 页面
# ══════════════════════════════════════════════════════════════════════
from page_css import CSS, JS


def fig(title: str, frame: str, foot: str = "", cls: str = "dense screen") -> str:
    """把整屏帧装进应用窗口外壳里——它是一个跑起来的应用，不是一段代码。

    data-check 让 check_frames.py 在真浏览器里复核这一块的逐行宽度。
    """
    cols = max(width(line) for line in frame.split("\n"))
    rows = len(frame.split("\n"))
    mode = {160: "wide-three", 80: "single-canvas"}.get(cols, f"{cols} 列")
    return (
        '<div class="win">\n'
        f'  <div class="win-bar">{KPI_IMG}'
        '<span class="nm">Kunpeng DevKit AI</span>'
        f'<span class="sub">{title}</span>'
        '<span class="meta">'
        f'<span class="tag">{cols} × {rows}</span>'
        f'<span class="tag">{mode}</span>'
        '<span class="tag on">truecolor</span></span></div>\n'
        f'  <div class="win-scroll"><pre class="{cls}" data-check="1" data-label="{title}">'
        f"{to_html(frame)}</pre></div>\n"
        + (f'  <div class="win-foot">{foot}</div>\n' if foot else "")
        + "</div>"
    )


FOOT = {'s1': '<b>可实现性</b> <code>LandingScreen</code> src/components/ui/landing.tsx · <code>KunpengBrand</code> brand.tsx · <code>PromptBar</code> prompt-bar.tsx · <code>Keybar/StatusBar</code> keybar.tsx <b>待新增</b> 环境探测行 · 最近 Session 列表', 's1n': '<b>降级</b> <code>layoutForWidth(80)</code> → single-canvas；<code>brandVariantFor()</code> 在 &lt;10 列不画字标', 's2': '<b>可实现性</b> <code>Shell</code> shell.tsx · <code>Dock</code> dock.tsx（宽度 27 取自 <code>layoutForWidth(160)</code>）· <code>TaskTabs</code> task-tabs.tsx · <code>PlanCard/EvidenceList/ContextGauge</code> component-library.tsx · <code>AgentConsole</code> agent-console.tsx（consoleHeight 8）· <code>Inspector</code> canvas.tsx', 's2n': '<b>降级</b> single-canvas：dockWidth 3，图标字形 <code>▮ ▯ ◇ ?</code> 与 dock.tsx 折叠态一致，consoleHeight 6', 's3': '<b>可实现性</b> <code>DiffView</code> component-library.tsx（现为纯前景色，本稿的整行底色带需要给 <code>&lt;text&gt;</code> 加 <code>bg</code>，StatusBar 已在用同一手法）· <code>AgentTimeline/ToolCard/ApprovalBar</code> component-library.tsx · <code>Overlay</code> 承载高危确认 <b>待补 token</b> <code>successBackground</code>（tokens.ts 现只有 info/warning/danger 三档）', 's3n': '<b>降级</b> 三栏轮播；接受/拒绝键位不随宽度挪位', 's4': '<b>可实现性</b> <code>SortableTable</code> component-library.tsx（热点表）· <code>FlameChart</code> charts/FlameChart.tsx · <code>SummaryCard</code> · <code>MetricBar</code> charts/ <b>待新增</b> 源码级逐行百分比视图 · 产出清单', 's4n': '<b>降级</b> 列按优先级砍，占比列永远保留；火焰图降到 3 层并显式标注未显示帧数', 's5': '<b>可实现性</b> <code>SplitContainer</code> + <code>SelectorPopup</code> component-library.tsx 可拼出三栏主从结构 <b>待新增</b> Settings 外壳 · 服务器条目与环境探测 · 凭据掩码输入 · 就地验证结果行', 's5b': '<b>可实现性</b> <code>SortableTable</code> 可承载模型对比表 <b>待新增</b> Provider 表单与就地验证', 's5c': '<b>可实现性</b> 错误三件套复用 <code>infoBackground/warningBackground/dangerBackground</code> 三档底色 <b>待新增</b> 凭据字段组件', 's5n': '<b>降级</b> 三栏塌为分类页签 + 单栏详情；就地验证五行压两行但一项不删'}


def build() -> str:
    launch, workspace, execu, result = (
        screen_launch(),
        screen_workspace(),
        screen_exec(),
        screen_result(),
    )
    rows = {
        "s1": (launch, screen_launch_narrow()),
        "s2": (workspace, screen_workspace_narrow()),
        "s3": (execu, screen_exec_narrow()),
        "s4": (result, screen_result_narrow()),
        "s5": (screen_settings_server(), screen_settings_narrow()),
    }
    body = TEMPLATE.format(
        css=CSS,
        js=JS,
        kpi_b64=KPI_B64,
        s1=fig("屏 1 · 启动页", rows["s1"][0]),
        s1n=fig("窄屏降级", rows["s1"][1]),
        s2=fig("屏 2 · Agent Workspace", rows["s2"][0]),
        s2n=fig("窄屏降级", rows["s2"][1]),
        s3=fig("屏 3 · Agent 执行中 · Tool + Diff", rows["s3"][0]),
        s3n=fig("窄屏降级", rows["s3"][1]),
        s4=fig("屏 4 · 任务结果页", rows["s4"][0]),
        s4n=fig("窄屏降级", rows["s4"][1]),
        s5=fig("屏 5 · 管理配置 · 服务器管理", rows["s5"][0]),
        s5b=fig("同屏 · 分类切到「模型 / Provider」", screen_settings_model()),
        s5c=fig("同屏 · 分类切到「账号与凭据」", screen_settings_account()),
        s5n=fig("窄屏降级", rows["s5"][1]),
    )
    return body


TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Kunpeng DevKit AI — 五个典型页面</title>
<meta name="description" content="启动页 · Agent Workspace · Agent 执行中（Tool + Diff）· 任务结果页（火焰图与热点函数）· 管理配置（服务器 / 账号 / 模型）五屏整屏字符帧。">
<style>{css}</style>
</head>
<body>

<div class="topbar">
  <img class="kpmark" alt="Kunpeng" src="data:image/png;base64,{kpi_b64}">
  <span class="brand">Kunpeng DevKit AI</span>
  <span class="vchip">五个典型页面</span>
  <span class="tagline">启动 · 工作台 · 执行 · 结果 · 配置 —— 整屏字符帧，非示意图</span>
  <span class="tb-right">
    <a href="./index.html#primlib">设计系统 ↗</a>
    <a href="./design-input.html">设计输入 ↗</a>
    <button class="tbtn" onclick="tt()">◐ <span id="tl">Light</span></button>
  </span>
</div>

<div class="wrap">
<nav id="nav">
  <div class="ngrp">Overview</div>
  <a href="#intro">这五屏是什么</a>
  <a href="#rules">五屏共用的规则</a>
  <div class="ngrp">Screens · 五屏</div>
  <a href="#s1">屏 1 · 启动页</a>
  <a href="#s2">屏 2 · Agent Workspace</a>
  <a href="#s3">屏 3 · 执行中 · Tool + Diff</a>
  <a href="#s4">屏 4 · 任务结果页 ★</a>
  <a href="#s5">屏 5 · 管理配置</a>
  <div class="ngrp">System</div>
  <a href="#comp">组件与状态覆盖</a>
  <a href="#open">待验证问题</a>
  <div class="nfoot">160×N · 80 列降级<br>宽度由生成器断言<br>tools/gen_screens.py</div>
</nav>

<main>

<section id="intro">
<div class="eyebrow">Key Screens</div>
<h1>五个典型页面</h1>
<p class="desc">从《<a href="./design-input.html">DevKit AI TUI 设计输入</a>》里挑出五屏最吃劲的：<strong>启动页</strong>（能不能马上开始）、<strong>Agent Workspace</strong>（Agent 在干什么）、<strong>执行中 Tool + Diff</strong>（有没有跑偏）、<strong>任务结果页</strong>（我得到了什么）、<strong>管理配置</strong>（Agent 到底能不能工作）。五屏刚好把设计输入 §9.1 的六个问题答完 ①②③④⑥，只剩 ⑤ 多任务由 Task Manager 承接。</p>
<div class="grid g3">
  <div class="card"><h4>对着实现画，不是对着想象画</h4>
  <p>布局尺寸取自 <code>platform/terminal/layout.ts</code> 的 <code>layoutForWidth()</code>——160 列是 <code>wide-three</code>：Dock 27 列、console 8 行；80 列是 <code>single-canvas</code>：Dock 收成 3 列图标条、console 6 行。状态栏字段顺序、任务页签字形、折叠态图标 <code>▮ ▯ ◇ ?</code>、选中标记 <code>▎</code> 全部与 <code>src/components/ui/</code> 里跑着的代码一致。<strong>每屏下方标出用了哪些现成组件、哪些还得新增。</strong></p></div>
  <div class="card"><h4>视觉与 Demo 同源</h4>
  <p>窗口外壳、AI PLAN 卡的编号 + 耗时、工具名 chip、diff 的整行底色带与左侧竖条、状态栏胶囊，都跟 <a href="./demo.html">设计 Demo</a> 是同一套语言。色值不是照着截图取的——<strong>直接取自实现的 <code>theme/tokens.ts</code></strong>：selected <code>#18293C</code>、focus <code>#162E49</code>、dangerBackground <code>#351B24</code>、surface2/3/4。</p></div>
  <div class="card"><h4>设计系统的纪律照旧生效</h4>
  <p>语义色只上字符与短文本、<strong>永不上色块</strong>（文件风险热力因此走 accum-orange 顺序色阶而不是 danger 红）；一屏只允许一个填充蓝，留给当前唯一推荐动作；圆角只给浮层。<a href="./index.html#color">Colors</a> · <a href="./index.html#frame">应用框架</a></p></div>
</div>
<p class="desc">五屏都是<strong>整屏字符帧</strong>，不是配色示意图：160 列宽屏 + 80 列窄屏各一帧，每行宽度在生成时被断言把着（<code>tools/screens.py</code>），CJK 按 2 格、Braille 按 1 格算——<strong>页面上看到的对齐关系，就是终端里的对齐关系</strong>。色值全部取自<a href="./index.html#color">设计系统</a>的既有色阶，未新造调色板。</p>
<div class="grid g4">
  <div class="stat"><b style="color:var(--primary-hover)">5</b><span>典型页面</span></div>
  <div class="stat"><b style="color:var(--success)">12</b><span>字符帧（宽 + 窄）</span></div>
  <div class="stat"><b style="color:var(--warning)">25</b><span>覆盖组件</span></div>
  <div class="stat"><b style="color:var(--accent)">0</b><span>新增色值</span></div>
</div>
<div class="note warn"><b>一处需要补的 token。</b><code>theme/tokens.ts</code> 现在只有 <code>infoBackground</code> / <code>warningBackground</code> / <code>dangerBackground</code> 三档底色，<strong>没有 <code>successBackground</code></strong>——而 diff 的新增行需要它。本稿按同族推导取 <code>#0E2F24</code>（base <code>#101010</code> + 15.5% 的 success 色，与另外三档同一算法），需要在实现里补进 tokens 并同步到 <code>UI-SPEC.md</code>。<code>&lt;text bg=…&gt;</code> 本身是支持的，<code>StatusBar</code> 已经在用同一手法。</div>
<div class="note"><b>这一版没有录屏。</b>录屏适合讲流程，不适合评审单屏——它没法定格、没法量宽度、没法比对齐。要看十幕连贯流程仍去<a href="./tui-live.html">实录回放</a>；这一页只回答“每一屏长什么样、每个像素为什么在那儿”。</div>
</section>

<section id="rules">
<div class="eyebrow">Foundation</div>
<h2>五屏共用的规则</h2>
<p class="desc">这些规则不属于任何单屏，写在这里，五屏都遵守；与<a href="./index.html#frame">应用框架</a>一节同源。</p>
<div class="grid g2">
  <div class="card"><h4>① 三条锚点永不隐藏</h4>
  <p>Header（我在哪 / 连什么机器）、Input（我怎么说话）、Status（现在什么状态）在各屏里位置一致、永不折叠。高度不够时先砍 Console，再砍 Canvas，最后砍 Tab Bar。</p></div>
  <div class="card"><h4>② 状态先于内容</h4>
  <p>每屏左上角第一个非框线字符就是状态符号（<code>●</code> Running / <code>✓</code> Completed / <code>⏸</code> 待配置 / <code>⚠</code> 风险）。用户扫一眼左上角就知道要不要继续读。</p></div>
  <div class="card"><h4>③ 结论与证据同屏</h4>
  <p>屏 2/3/4 都留了证据位：Inspector 的案例库编号、Diff 的“为什么”、结果页的源码行。<strong>没有证据位的结论不允许出现在画布上。</strong></p></div>
  <div class="card"><h4>④ 数据走色阶，结论走语义色</h4>
  <p>bar、火焰图、热力走域色阶（<code>o3–o8</code> / <code>g3–g8</code>）；只有被判定为问题的<strong>数值与文字</strong>才上 warning / danger。50% 的占比本身不是错误。</p></div>
  <div class="card"><h4>⑤ 画不下就显式说</h4>
  <p>火焰图标 <code>3 帧过窄未显示</code>、热点表标 <code>… 24 more</code>、Console 标 <code>9 行未展开</code>。悄悄省略会把“我看全了”变成错觉。</p></div>
  <div class="card"><h4>⑥ 圆角等于浮起</h4>
  <p>固定区域一律直角 <code>┌┐└┘</code>；Plan 卡、Tool call、高危确认、错误卡这些浮层才用圆角 <code>╭╮╰╯</code>。五屏里出现的每一个圆角都是浮层。</p></div>
</div>
</section>

<section id="s1">
<div class="eyebrow">Screen 01</div>
<h2>启动页 —— 回答“我能不能马上开始”</h2>
<p class="desc">用户敲完 <code>devkitai</code> 看到的第一屏。它要同时交付四件事：<strong>我是谁</strong>（Logo + 能力）、<strong>环境行不行</strong>（本机架构 / 工具链 / 模型连通性）、<strong>怎么开口</strong>（输入框 + 命令）、<strong>能不能接着上次干</strong>（最近 Session）。缺任何一件，用户都得多问一轮。</p>
{s1}
<div class="sublabel">区域与职责</div>
<table>
<tr><th>区域</th><th>回答什么</th><th>关键设计决定</th></tr>
<tr><td>Wordmark + 版本</td><td>我打开的是什么</td><td>块字符 5 行封顶。<strong>不做纯 Logo 开屏</strong>——Logo 之外必须同屏给出可执行信息</td></tr>
<tr><td>能力四卡</td><td>它能干什么</td><td>迁移 / 开发 / 诊断 / 调优四类各三行，等宽卡片；更细的能力走 <code>/info</code>，首屏不铺开</td></tr>
<tr><td>环境行</td><td>这台机器行不行</td><td>本机架构自动探测；<strong>缺件用 warning 且必须带修复动作</strong>（<kbd>F</kbd> 修复 / <kbd>C</kbd> 连远程），不给“已知问题”式的死信息</td></tr>
<tr><td>模型行</td><td>AI 通不通</td><td>Provider + 模型 + 实测延迟三件一行。连接失败时这一行整行转 warning，并直接给 <code>/provider</code> 入口</td></tr>
<tr><td>输入框</td><td>我怎么开口</td><td>常驻第一入口，自然语言优先，命令面板是等价快捷方式而非主路径</td></tr>
<tr><td>最近 / 建议</td><td>零输入能干什么</td><td>常驻进程相对 CLI 的直接兑现——CLI 没有“上次”。建议随环境状态变，不是固定菜单</td></tr>
</table>
<div class="sublabel">状态矩阵</div>
<table>
<tr><th>状态</th><th>表现</th></tr>
<tr><td>首次启动</td><td>无“最近”行，“建议”换成三条冷启动建议；能力卡下方出现 <code>[A] 一键安装迁移能力包</code></td></tr>
<tr><td>模型未配置</td><td>模型行转 <code>⚠ 未配置模型</code>，输入框置灰并提示先按 <kbd>Enter</kbd> 走 Provider 向导——<strong>唯一允许禁用输入框的场景</strong></td></tr>
<tr><td>非鲲鹏环境</td><td>环境行给出 <code>⚠ 当前非鲲鹏环境</code> + <code>[C] 连接远程鲲鹏服务器</code>；不阻断本地可完成的任务（如源码扫描）</td></tr>
<tr><td>有后台任务</td><td>底栏显示运行中任务数，<code>⏸ 待配置</code> 的任务置顶到“最近”第一行</td></tr>
</table>
{s1n}
<p class="rule"><strong>窄屏降级：</strong>&lt;100 列时能力四卡塌成一行文字，环境/模型两行保留（它们是阻塞项，不能省），最近只留一条。<strong>输入框和状态栏在任何宽度下都不消失。</strong></p>
</section>

<section id="s2">
<div class="eyebrow">Screen 02</div>
<h2>Agent Workspace —— 回答“Agent 在干什么”</h2>
<p class="desc">核心工作台。左 Dock 管任务 / 工程 / 工具，中间画布是对话与 Agent 状态，右 Inspector 常驻证据与上下文水位，底部 Console + 输入 + 状态栏。<strong>对象是 Task / Skill / Tool / File，不是一串 message</strong>——这是 Agent First 而非 Chat First 的直接结构表达。</p>
{s2}
<div class="sublabel">区域与职责</div>
<table>
<tr><th>区域</th><th>宽度</th><th>职责</th><th>折叠</th></tr>
<tr><td>Rail</td><td>3</td><td>Dock 面板切换（T/P/K/H 单字符）</td><td>常驻</td></tr>
<tr><td>Dock</td><td>26</td><td>TASKS 多任务 · PROJECT 工程树（<code>⇄ 跟随</code> Agent 当前文件）· TOOLS 工具状态</td><td><kbd>Ctrl+B</kbd> 收为图标列</td></tr>
<tr><td>Canvas</td><td>88</td><td>用户意图 → Plan 卡 → Agent 实时状态（Skill / Tools / 进度）</td><td>常驻</td></tr>
<tr><td>Inspector</td><td>39</td><td>当前对象 · 证据 · 上下文水位 · 本次改动统计</td><td><kbd>Ctrl+I</kbd></td></tr>
<tr><td>Console</td><td>1–12 行</td><td>工具调用流水，默认折成一行，<kbd>Ctrl+J</kbd> 抽高</td><td>最低 1 行</td></tr>
</table>
<div class="sublabel">这一屏在兑现设计输入的哪几条</div>
<div class="grid g2">
  <div class="card"><h4>过程可观察（§2.3）</h4>
  <p>Agent 区固定四行：状态 + Skill + Tools + 进度。<strong>任何时刻这四行都能回答“它在做什么、用什么、到哪一步”</strong>，不需要展开日志。</p></div>
  <div class="card"><h4>执行可控制（§2.4）</h4>
  <p>Agent 行右端常驻 <code>[Esc] 中断</code>；Plan 卡右上角常驻 <code>[e] 改计划</code>。<strong>控制入口和状态显示在同一行，不藏进菜单。</strong></p></div>
  <div class="card"><h4>多任务可管理（§2.5）</h4>
  <p>顶部 Tab + Dock 任务列双重呈现：Tab 管切换，列表管全局状态。<code>⏸ 待配置</code> 同时在底栏常驻提示——它卡着不动且需要人。</p></div>
  <div class="card"><h4>上下文可见（§2.6 前置）</h4>
  <p>Inspector 底部的 ctx 水位是<strong>结果质量的先行指标</strong>：到 72% 转 warning，到 90% 主动建议 <code>/compact</code>，不等它爆掉再解释。</p></div>
</div>
{s2n}
<p class="rule"><strong>窄屏降级：</strong>&lt;100 列 Dock 转浮层、Inspector 折成一行证据摘要；&lt;80 列 Canvas 单栏 + Tab 轮播。<strong>Agent 四行与输入框优先保留</strong>——它们是“看得见、管得住”的最小集合。</p>
</section>

<section id="s3">
<div class="eyebrow">Screen 03</div>
<h2>Agent 执行中 · Tool + Diff —— 回答“它有没有跑偏”</h2>
<p class="desc">竞品分析里情绪最低点落在“人审查 AI 改动”这一步，<strong>没有一个产品做到 hunk 级接受/拒绝</strong>。这一屏就是对着那个缺口设计的：左边是执行过程与工具调用，右边是逐 hunk 的代码审查，每个 hunk 都带“为什么”和可跳转的证据。</p>
{s3}
<div class="sublabel">三个关键机制</div>
<table>
<tr><th>机制</th><th>做法</th><th>为什么这样</th></tr>
<tr><td>hunk 级审查</td><td><kbd>y</kbd> 接受 / <kbd>n</kbd> 拒绝 / <kbd>e</kbd> 编辑后接受 / <kbd>a</kbd> 全接受，<kbd>J K</kbd> 换 hunk</td><td>文件级接受等于逼用户二选一：要么全信，要么全部自己改</td></tr>
<tr><td>改动带理由与证据</td><td>每个 hunk 下方固定三行：为什么 / 证据 / 影响面</td><td>“影响面”是最容易被漏掉的一行——同类调用点还有几处，直接决定用不用 <kbd>a</kbd></td></tr>
<tr><td>高危操作确认</td><td>浮层列出<strong>将要执行的原始命令</strong>与不可撤销说明，默认焦点在取消</td><td>确认框不能只说“执行危险操作吗”，必须让用户看到那条命令本身</td></tr>
</table>
<div class="note warn"><b>Esc 不是 Ctrl+C。</b>传统 CLI 里 <kbd>Ctrl+C</kbd> 杀进程、上下文全丢；这里 <kbd>Esc</kbd> 是<strong>暂停当前动作 → 保留上下文 → 用户纠偏 → 从断点继续</strong>。因此中断后输入框必须立刻可用且带提示“中断后可直接说”，否则用户不知道自己已经拿回了控制权。这条是 Interrupt → Correct → Resume 三段式，属全局交互规则，不是本屏私有。</div>
{s3n}
<p class="rule"><strong>窄屏降级：</strong>执行流 / Diff / 证据由并排改为 <kbd>Tab</kbd> 轮播三页，Diff 页是默认页。<strong>接受/拒绝键位在任何宽度下都在同一行的同一位置</strong>——审查是肌肉记忆动作，位置漂移代价最大。</p>
</section>

<section id="s4">
<div class="eyebrow">Screen 04 · 参照 DevKit Web 热点函数分析</div>
<h2>任务结果页 —— 回答“我到底得到了什么”</h2>
<p class="desc">这一屏对齐 DevKit Web 端「热点函数分析」的信息结构：<strong>Top 30 热点调用栈表</strong>（函数/调用栈 · 周期数占比 · 周期数 · 进程名 · 共享库/文件）、<strong>火焰图</strong>（用户态 / 内核态 / 其他三类着色 + 搜索标记）、<strong>源码级热点</strong>（行号左侧标该行占所属函数总周期的百分比）。字段名与分组方式沿用 Web 端，用户在两端之间不需要做术语翻译。</p>
{s4}
<div class="sublabel">与 Web 端的对照</div>
<table>
<tr><th>Web 端</th><th>TUI 端</th><th>翻译决定</th></tr>
<tr><td>Top 30 热点调用栈表格 + 排序/筛选图标</td><td>同字段表格，占比列前置 bar</td><td>bar 用八分之一格，<strong>50.00% 与 49.２% 必须画得出区别</strong>；排序状态嵌在列头 <code>▾</code></td></tr>
<tr><td>分组方式下拉（函数/调用栈）</td><td>行内 <code>分组 [函数/调用栈]</code> + <kbd>g</kbd> 切换</td><td>TUI 无下拉控件的空间预算，改为当前值常显 + 单键循环</td></tr>
<tr><td>火焰图（绿=用户态 / 橙=内核态 / 红=其他）</td><td>同三分类，改走域色阶</td><td><strong>红色退出数据层</strong>：语义红只表示“出事了”，其余走 violet；图例常显在图上方</td></tr>
<tr><td>火焰图搜索框 + 紫色搜索标记</td><td><kbd>/</kbd> 搜索 + 反显块（<code>state-selected</code>）</td><td>16 色终端下紫色不可靠，改用背景反显——形状承载，不依赖色相</td></tr>
<tr><td>源码窗口：行号左侧百分比</td><td>同布局，热点行整行反显</td><td>只显示热点行 ±4 行上下文；<strong>98.65% 那一行必须一眼可见</strong>，不能靠滚动找</td></tr>
<tr><td>缩略图 / 全屏 / 大小写敏感等工具按钮</td><td>不做</td><td>鼠标时代的密度换发现性；TUI 走单键 + 命令面板</td></tr>
</table>
<div class="sublabel">结果页的四段固定结构</div>
<p class="rule"><strong>结论 → 证据 → 下一步 → 产出。</strong>任务结束时用户要的是判断，不是更多输出。所以第一行就是判定（伪共享 · 置信度 93%），中间是支撑它的三张图（热点表 / 火焰图 / 源码行），然后才是可执行的下一步与文件清单。<strong>产出区必须给出路径与体积，并说明哪些不随报告导出</strong>——“Agent 生成了很多文件但我不知道在哪”是结果页最常见的失败。</p>
<div class="note"><b>为什么结论敢写死在第一行。</b>热点表两行各 50%、源码定位到 <code>++f.y;</code> 占 98.65%、两线程分别绑核 2/3——三条证据在同屏内互相印证，才允许把“伪共享”写成结论并给置信度。<strong>置信度低于阈值时这一行改写成疑问句并列出待排除项</strong>，不允许把猜测写成判定。鲲鹏 920 的 L1D cacheline 是 128B，这个常数也必须写出来，否则用户没法自行验证。</div>
{s4n}
<p class="rule"><strong>窄屏降级：</strong>热点表按列优先级砍——占比列永远保留，周期数、进程名、共享库依次隐藏（<kbd>Enter</kbd> 看详情）；火焰图降到 3 层并显式标注未显示帧数；源码只留热点行 + 结论一行。</p>
</section>

<section id="s5">
<div class="eyebrow">Screen 05</div>
<h2>管理配置 —— 回答“Agent 到底能不能工作”</h2>
<p class="desc">服务器、账号、模型三类配置收在同一页，左侧分类 · 中间列表 · 右侧详情。它回答设计输入六问里的 <strong>②</strong>——这一问答不上，其余四屏全部无从开始。三类配置差异很大，但共用一条主线：<strong>每一项都必须能就地验证，不能只让用户点“保存”</strong>。只能保存不能测，等于把失败推迟到第一次真正干活的时候，而那时用户正在做别的事。</p>
{s5}
<div class="sublabel">三类配置的共同结构</div>
<table>
<tr><th>区域</th><th>宽度</th><th>职责</th></tr>
<tr><td>分类栏</td><td>22</td><td>服务器 / 账号 / 模型 / Skill / 通用 / 更新，各带计数与异常徽标；<strong>选中走反显不走颜色</strong></td></tr>
<tr><td>列表</td><td>44</td><td>该类下的条目 + 状态，以及跨条目的汇总（当前使用的模型、到期提醒、默认落点）</td></tr>
<tr><td>详情</td><td>90</td><td>选中项的字段、<strong>就地验证结果</strong>、可执行动作</td></tr>
<tr><td>底部通知条</td><td>整宽</td><td>本页最该被处理的那一件事，带直达动作——不让用户自己在三个分类里翻</td></tr>
</table>
<div class="sublabel">分类切到「服务器」</div>
<p class="desc">远程鲲鹏服务器是<strong>本机不是鲲鹏时的执行落点</strong>。所以这一屏不只是填地址：它要回答“连上之后这台机器到底能不能干活”，因此环境探测把架构、系统、DevKit 版本、编译器、<code>perf</code> 权限、交叉工具链逐条列出来，<strong>每个不合格项都直接带修复动作</strong>。</p>
{s5b}
<div class="grid g2">
  <div class="card"><h4>指纹变化一律拦截</h4>
  <p>主机指纹与上次不一致时暂停对该机的所有任务并要求重新确认，<strong>不提供“永久忽略”</strong>。这是唯一一处我们主动牺牲便利的地方——中间人风险不能用一个复选框换掉。</p></div>
  <div class="card"><h4>落点规则是配置项，不是猜测</h4>
  <p>编译落哪台、采集落哪台写在“默认落点”里且可改。性能采集默认单独指到压测机——<strong>和编译共机会让采集数据失真</strong>，这条不该靠用户自己想到。</p></div>
  <div class="card"><h4>本机能做的不阻断</h4>
  <p>本机非鲲鹏时，源码扫描与静态分析照常在本地跑，只有交叉编译与性能采集需要远端。<strong>不因为“环境不对”把整个产品锁死。</strong></p></div>
  <div class="card"><h4>连通性影响渲染</h4>
  <p>探测到 SSH 低带宽时整体切到低重绘档。<strong>连接质量是渲染策略的输入</strong>，不是只拿来显示的一个数字。</p></div>
</div>
<div class="sublabel">分类切到「账号」</div>
<p class="desc">账号页承载凭据，所以它同时是<strong>错误体系与凭据纪律的样板屏</strong>：上次验证失败按“发生了什么 → 为什么 → 怎么解决”三段展开，并额外给出<strong>影响面</strong>——令牌过期不会让 Agent 停摆，但会让改动失去案例库证据，屏 3 的证据区随之显示为不可用。用户需要据此决定现在处理还是先干活。</p>
{s5c}
<table>
<tr><th>凭据要做到</th><th>凭据不允许</th></tr>
<tr><td>输入即掩码，回显只留首尾 <code>sk-a1f2****9c4d</code></td><td>写入任何日志与终端回滚缓冲</td></tr>
<tr><td>静态加密（AES-256-GCM），文件权限 <code>0600</code></td><td>随报告 / Session 快照导出</td></tr>
<tr><td>支持系统钥匙串托管</td><td>发送给模型、进入上下文</td></tr>
<tr><td>过期前 30 天开始提醒</td><td>到期当天才以报错形式告知</td></tr>
</table>
<p class="rule"><strong>遥测开关默认全关，且只在这一页。</strong>散落在多处的隐私开关等于没有开关——用户找不到就默认它是开着的。</p>
{s5n}
<p class="rule"><strong>窄屏降级：</strong>三栏塌成“分类页签 + 单栏详情”，<kbd>Tab</kbd> 切分类。<strong>就地验证的五行结果压成两行但一项不删</strong>——它是这一页存在的理由；先被牺牲的是模型对比表，改为进列表逐个看。</p>
</section>

<section id="comp">
<div class="eyebrow">System</div>
<h2>组件与状态覆盖</h2>
<p class="desc">五屏一共动用 25 个组件。<strong>下表右列是判断这一屏该不该沉淀为通用组件的依据</strong>：出现在两屏以上的一律进通用组件库，只出现一次的先留在页面里。</p>
<table>
<tr><th>组件</th><th>屏 1</th><th>屏 2</th><th>屏 3</th><th>屏 4</th><th>屏 5</th><th>归属</th></tr>
<tr><td>Header / Status Bar</td><td>✓</td><td>✓</td><td>✓</td><td>✓</td><td>✓</td><td>全局 Shell</td></tr>
<tr><td>Prompt Input</td><td>✓</td><td>✓</td><td>✓</td><td>✓</td><td>—</td><td>全局 Shell</td></tr>
<tr><td>Agent Status</td><td>—</td><td>✓</td><td>✓</td><td>—</td><td>—</td><td>通用组件</td></tr>
<tr><td>Tool Call</td><td>—</td><td>✓</td><td>✓</td><td>—</td><td>—</td><td>通用组件</td></tr>
<tr><td>Progress Bar</td><td>—</td><td>✓</td><td>✓</td><td>—</td><td>—</td><td>通用组件（图元）</td></tr>
<tr><td>Metric Bar</td><td>—</td><td>✓</td><td>—</td><td>✓</td><td>✓</td><td>通用组件（图元）</td></tr>
<tr><td>Evidence List</td><td>—</td><td>✓</td><td>✓</td><td>✓</td><td>—</td><td>通用组件</td></tr>
<tr><td>Task List / Tabs</td><td>—</td><td>✓</td><td>—</td><td>—</td><td>—</td><td>通用组件</td></tr>
<tr><td>File Tree（跟随）</td><td>—</td><td>✓</td><td>—</td><td>—</td><td>—</td><td>通用组件</td></tr>
<tr><td>Plan Card</td><td>—</td><td>✓</td><td>—</td><td>—</td><td>—</td><td>通用组件</td></tr>
<tr><td>Diff Viewer（hunk 级）</td><td>—</td><td>—</td><td>✓</td><td>—</td><td>—</td><td>通用组件 ★</td></tr>
<tr><td>Confirm（高危）</td><td>—</td><td>—</td><td>✓</td><td>—</td><td>—</td><td>通用组件</td></tr>
<tr><td>Next Step 引导</td><td>✓</td><td>—</td><td>—</td><td>✓</td><td>—</td><td>通用组件</td></tr>
<tr><td>Capability Card</td><td>✓</td><td>—</td><td>—</td><td>—</td><td>—</td><td>页面局部</td></tr>
<tr><td>Env / Model 状态行</td><td>✓</td><td>—</td><td>—</td><td>—</td><td>✓</td><td>页面局部</td></tr>
<tr><td>Hotspot Table</td><td>—</td><td>—</td><td>—</td><td>✓</td><td>—</td><td>页面局部（可升）</td></tr>
<tr><td>Flame Chart</td><td>—</td><td>—</td><td>—</td><td>✓</td><td>—</td><td>通用组件（图元）</td></tr>
<tr><td>Source Hotspot</td><td>—</td><td>—</td><td>—</td><td>✓</td><td>—</td><td>页面局部</td></tr>
<tr><td>Artifact List</td><td>—</td><td>—</td><td>—</td><td>✓</td><td>—</td><td>通用组件</td></tr>
<tr><td>Wordmark</td><td>✓</td><td>—</td><td>—</td><td>—</td><td>—</td><td>页面局部</td></tr>
<tr><td>Settings Nav</td><td>—</td><td>—</td><td>—</td><td>—</td><td>✓</td><td>页面局部</td></tr>
<tr><td>Provider Config</td><td>—</td><td>—</td><td>—</td><td>—</td><td>✓</td><td>页面局部</td></tr>
<tr><td>Model Selector</td><td>—</td><td>—</td><td>—</td><td>—</td><td>✓</td><td>页面局部</td></tr>
<tr><td>Credential Field（掩码）</td><td>—</td><td>—</td><td>—</td><td>—</td><td>✓</td><td>通用组件</td></tr>
<tr><td>Connection Test（就地验证）</td><td>✓</td><td>—</td><td>—</td><td>—</td><td>✓</td><td>通用组件</td></tr>
<tr><td>Error（三件套）</td><td>—</td><td>—</td><td>—</td><td>—</td><td>✓</td><td>通用组件</td></tr>
</table>
<div class="sublabel">五屏覆盖的状态</div>
<p class="rule">Agent：<code>Running</code>（屏 2/3）· <code>Completed</code>（屏 4）· <code>Waiting</code>（屏 3 高危确认）· <code>Suspended</code>（屏 2 Dock 内 <code>⏸</code>）。Connection 四态在屏 5 齐了：<code>Connected</code> / <code>Connecting</code> / <code>Disconnected</code> / <code>Failed</code>（ollama 那条）。<strong>仍未覆盖：Agent 的 <code>Failed</code> 与 <code>Idle</code></strong>——失败态屏需要单独出一版（编译翻车转诊断那一幕），列入下一阶段。</p>
</section>

<section id="open">
<div class="eyebrow">System</div>
<h2>待验证问题</h2>
<table>
<tr><th>问题</th><th>影响</th><th>怎么验</th></tr>
<tr><td>160 列在实际 SSH 窗口的占比</td><td>决定 3 栏布局是主路径还是奢侈路径</td><td>统计目标用户终端宽度分布；若 &lt;140 列占多数，Inspector 需改为默认折叠</td></tr>
<tr><td>火焰图在 TUI 的可用深度</td><td>超过 6 层后每帧不足 1 格，宽度信息失真</td><td>用真实 perf 数据跑降级：先按占比阈值裁剪，再评估“过窄未显示”的比例是否可接受</td></tr>
<tr><td>热点表 6 列在 120 列下的可读性</td><td>共享库路径列极易溢出</td><td>路径中段省略 vs 只留 basename，两版做可读性对比</td></tr>
<tr><td>Diff 在 CJK 注释行的对齐</td><td>中文注释占 2 格，行号列会被推歪</td><td>已有 <code>fit()/pad()</code> 规则，需要针对 diff 高亮再跑一次断言</td></tr>
<tr><td>中断后上下文恢复的语义</td><td><kbd>Esc</kbd> 之后“继续”是重跑当前步还是跳过</td><td>需产品裁决；两种语义都要在 Agent 行给出明确文案</td></tr>
</table>
</section>

<footer>
Kunpeng DevKit AI · 五个典型页面 · 字符帧由 tools/gen_screens.py 生成，宽度经断言校验<br>
内部设计资料，授权方式待定。Kunpeng 标识及华为品牌色版权归华为技术有限公司所有。
</footer>

</main>
</div>
<script>{js}</script>
</body>
</html>
"""


if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8")
    print(f"✓ {OUT.relative_to(OUT.parent.parent.parent)}  {OUT.stat().st_size / 1024:.0f}KB")
