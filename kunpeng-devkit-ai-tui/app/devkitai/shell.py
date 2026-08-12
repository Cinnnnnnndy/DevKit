"""工作台外壳 —— 把 Chrome 层与 Canvas 层装到一起。

结构按 VISUAL.md「Shell 结构：左栏要从顶通到底」：

    ┌─────┬──────────────────────────────┐
    │Dock │ TabBar                       │  ← Dock 头与 TabBar 等高
    │  头 ├──────────────┬───────────────┤
    │     │ Canvas A     │ Canvas B      │  ← 结论 ↔ 证据，60/40
    │TASKS│              │               │
    │PROJ ├──────────────┴───────────────┤
    │TOOLS│ Agent Console                │
    │     ├──────────────────────────────┤
    │     │ ❯ 输入（属于会话，不属于窗口）│
    ├─────┴──────────────────────────────┤
    │ keybar   （全宽：随上下文变的键）  │
    │ status   （全宽：全局唯一的状态）  │
    └────────────────────────────────────┘

**一条垂直分割贯穿全屏，一条水平分割横贯全屏，两条线各只出现一次。**
全宽的只有 keybar 与状态栏——判据是"切换页签会变的东西归页签，不变的归窗口"。

    python -m devkitai            # 这一页
    python -m devkitai preview    # 组件预览页
"""

from __future__ import annotations

import math

from textual import events
from textual.app import App, ComposeResult
from textual.geometry import Size
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Static

from .layout import DockMode, InspectorMode, Layout, resolve_layout
from .theme import pto_theme, pto_variables
from .tiers import detect
from .widgets import (
    Annotation,
    BrailleChart,
    Column,
    CoreHeatmap,
    Dock,
    DockItem,
    DockPanel,
    KernelTable,
    KeyBar,
    PromptInput,
    StatusBar,
    TabBar,
    Task,
)

# ── Demo 数据：JOURNEY.md 的十幕故事线，主角把 x86 nginx 迁到鲲鹏 ──────────
TASKS = [
    Task("migrate nginx", "done"),
    Task("optimize qwen-72b", "running"),
    Task("diagnose crash.log", "pending"),
    Task("migrate order-svc", "paused"),
]

KERNEL_COLUMNS = (
    Column("name", "Kernel", width=18),
    Column("calls", "Calls", width=8, numeric=True),
    Column("avg_ms", "Avg", width=9, numeric=True, fmt=lambda v: f"{v:.1f}ms"),
    Column("total_s", "Total", width=18, bar_domain="npu", fmt=lambda v: f"{v:.1f}s"),
)

KERNELS = [
    {"name": "attention_fwd", "calls": 1024, "avg_ms": 18.2, "total_s": 18.6},
    {"name": "matmul_4096", "calls": 512, "avg_ms": 12.4, "total_s": 6.3},
    {"name": "layernorm", "calls": 2048, "avg_ms": 1.8, "total_s": 3.7},
    {"name": "softmax", "calls": 1024, "avg_ms": 2.1, "total_s": 2.1},
]


def demo_panels() -> list[DockPanel]:
    return [
        DockPanel("tasks", "TASKS", "T", hint="[Alt+1..9]", items=[
            DockItem("migrate nginx", "done", "Build PASS  12:04"),
            DockItem("optimize qwen-72b", "running", "02:14 / ~05:00"),
            DockItem("diagnose crash.log", "pending", "排队中"),
            DockItem("migrate order-svc", "paused", "[↵] 去处理"),
        ]),
        DockPanel("project", "PROJECT", "P", hint="⇄ 跟随", items=[
            DockItem("nginx/", "pending"),
            DockItem("src/", "pending", depth=1),
            DockItem("crypto.c", "warning", depth=2, risk=92),
            DockItem("memory.c", "warning", depth=2, risk=58),
            DockItem("ngx_core.c", "done", depth=2, risk=12),
            DockItem("conf/", "pending", depth=1),
        ]),
        DockPanel("tools", "TOOLS", "L", items=[
            DockItem("cpp_migrator", "done"),
            DockItem("knowledge_base", "done"),
            DockItem("sql_migrator", "pending", "未安装"),
            DockItem("profiler", "warning", "需 NPU 驱动", new=True),
        ]),
    ]


class DevKitShell(App):
    """Kunpeng DevKit AI 工作台外壳。"""

    CSS_PATH = "theme/pto.tcss"
    TITLE = "Kunpeng DevKit AI"

    BINDINGS = [
        ("ctrl+b", "toggle_dock", "折叠 Dock"),
        ("ctrl+j", "toggle_console", "Console"),
        ("tab", "focus_next", "焦点轮转"),
        ("q", "quit", "退出"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._caps = detect()
        self._layout: Layout | None = None

    def get_theme_variable_defaults(self) -> dict[str, str]:
        return pto_variables()

    # ── 布局 ────────────────────────────────────────────────────────────
    def compose(self) -> ComposeResult:
        # 根容器显式排布。不用 dock:bottom——多个 dock 到同一边的兄弟会被算到
        # 同一行上互相盖住，只有最后一个看得见。
        with Vertical(id="root"):
            with Horizontal(id="shell"):
                yield Dock(demo_panels(), id="dock")
                with Vertical(id="workspace"):
                    yield TabBar(TASKS, id="tabs")
                    with Horizontal(id="canvases"):
                        with VerticalScroll(id="canvas-a", classes="canvas"):
                            yield BrailleChart("cpu · kunpeng-920", "cpu",
                                               id="chart-cpu", caps=self._caps)
                            yield CoreHeatmap(64, 16, id="heatmap", caps=self._caps)
                            yield KernelTable(KERNEL_COLUMNS, title="kernels", id="kernels")
                        with VerticalScroll(id="canvas-b", classes="canvas"):
                            yield Static(_evidence(), id="evidence")
                    yield Static(_console(), id="console", classes="panel")
                    yield PromptInput(
                        placeholder="把 ./nginx 迁到鲲鹏",
                        slot="Ctrl+P 命令面板",
                        id="prompt",
                    )
            # 全宽的只有这两条：keybar 随上下文变，状态栏全局唯一
            yield KeyBar(id="keybar")
            yield StatusBar(id="status")

    def on_mount(self) -> None:
        self.register_theme(pto_theme())
        self.theme = "pto"

        chart = self.query_one("#chart-cpu", BrailleChart)
        chart.extend([50 + 42 * math.sin(i / 9) for i in range(160)])

        heat = self.query_one("#heatmap", CoreHeatmap)
        heat.update_utilisation([abs(50 + 45 * math.sin(i / 5.5)) % 100 for i in range(64)])
        heat.annotate([
            Annotation(tuple(range(34, 39)), "warning", "持续 >80%，疑似跨 NUMA 内存访问"),
        ])

        self.query_one("#kernels", KernelTable).set_rows(KERNELS)

        status = self.query_one("#status", StatusBar)
        status.workspace, status.context_pct, status.blocked_tasks = "Migrate", 72, 1

        self.query_one("#keybar", KeyBar).keys = (
            ("Ctrl+B", "折叠 Dock"),
            ("Ctrl+J", "Console"),
            ("Ctrl+P", "命令面板"),
            ("Tab", "焦点轮转"),
            ("?", "快捷键"),
        )
        self._apply_layout()

    def on_resize(self, event: events.Resize) -> None:
        # 必须用事件带来的尺寸。这时候 self.size 还是**改之前**的值，
        # 拿它算出来的布局会永远慢一拍——拖窄一次没反应，再拖一次才跳到
        # 上一次该有的档位。
        self._apply_layout(event.size)

    def _apply_layout(self, size: Size | None = None) -> None:
        """把宽度判决应用到实际组件上。

        判决本身在 :mod:`devkitai.layout` 里，是个纯函数——布局降级属于
        "平时不会有人手动把终端拖到 97 列"的逻辑，不做成可测的就等于没写。
        """
        size = self.size if size is None else size
        if not size.width:
            return
        layout = resolve_layout(size.width, size.height, tasks=len(TASKS))
        if layout == self._layout:
            return
        self._layout = layout

        dock = self.query_one("#dock", Dock)
        dock.collapsed = layout.dock is not DockMode.FULL
        dock.display = layout.dock is not DockMode.OVERLAY

        self.query_one("#tabs", TabBar).display = layout.show_tabs
        self.query_one("#canvas-b").display = layout.canvases > 1
        self.query_one("#console").styles.height = layout.console_rows

        status = self.query_one("#status", StatusBar)
        status.tooltip = layout.summary

    # ── 动作 ────────────────────────────────────────────────────────────
    def action_toggle_dock(self) -> None:
        dock = self.query_one("#dock", Dock)
        dock.collapsed = not dock.collapsed

    def action_toggle_console(self) -> None:
        console = self.query_one("#console")
        current = console.styles.height.value if console.styles.height else 5
        console.styles.height = 12 if current < 12 else 5


def _evidence() -> str:
    """Canvas B 始终承载"结论的依据"——这是 P03 Evidence 在框架层的常驻位置。"""
    return (
        " EVIDENCE\n\n"
        " src/crypto.c:223\n"
        "  - _mm_pause();\n"
        "  + asm volatile(\"yield\");\n\n"
        " [1] 指令替换案例库 #4471\n"
        " [2] ARM ARM §B2.5\n"
        " [3] runtime.log: unaligned\n"
        "     access at 0x7f3a…\n\n"
        " 置信度 █████████░ 91%\n"
    )


def _console() -> str:
    return (
        " AGENT CONSOLE                      [Ctrl+J]\n"
        " ● Scan project        1,204 files\n"
        " ● Search KB           3 hits\n"
        " ▶ Generate patch  ⠹   cpp_migrator\n"
        " ○ Build verify\n"
    )


def main() -> None:
    DevKitShell().run()
