"""组件预览页 —— VISUAL.md §6 要求的 preview gate。

规范里那条"禁止在业务模块里直接造新样式"要成立，前提是有个地方能一眼看完
所有已有组件。这一页就是那个地方：每个原语连同它的评审声明（渲染层 /
降级路径 / 键盘等价 / token）一起展示，且能**现场切换渲染层**看降级效果——
降级路径写在文档里没人会去验，能按一下就看到的才会。

    python -m devkitai              # 正常跑
    DEVKITAI_NO_BRAILLE=1 python -m devkitai   # 强制 T2 降级到 T1
    NO_COLOR=1 python -m devkitai              # 强制 T3 降级到 T1 灰阶
"""

from __future__ import annotations

import math

from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Footer, Label, Static

from .spec import declared_components
from .theme import pto_theme, pto_variables
from .tiers import Capabilities, Tier, detect
from .tokens import STATUS_GLYPH
from .widgets import Annotation, BrailleChart, Column, CoreHeatmap, KernelTable

KERNELS = [
    {"name": "attention_fwd", "calls": 1024, "avg_ms": 18.2, "total_s": 18.6, "bound": "mem"},
    {"name": "matmul_4096", "calls": 512, "avg_ms": 12.4, "total_s": 6.3, "bound": "comp"},
    {"name": "layernorm", "calls": 2048, "avg_ms": 1.8, "total_s": 3.7, "bound": "mem"},
    {"name": "softmax", "calls": 1024, "avg_ms": 2.1, "total_s": 2.1, "bound": "mem"},
    {"name": "gelu", "calls": 4096, "avg_ms": 0.4, "total_s": 1.6, "bound": "comp"},
    {"name": "allreduce", "calls": 128, "avg_ms": 9.7, "total_s": 1.2, "bound": "net"},
]

COLUMNS = (
    Column("name", "Kernel", width=18),
    Column("calls", "Calls", width=8, numeric=True),
    Column("avg_ms", "Avg", width=9, numeric=True, fmt=lambda v: f"{v:.1f}ms"),
    Column("total_s", "Total", width=20, bar_domain="npu", fmt=lambda v: f"{v:.1f}s"),
    Column("bound", "Bound", width=7),
)


def _demo_series(n: int, phase: float, noise: float = 0.0) -> list[float]:
    """确定性的假数据——**不用 random**，否则每次重绘图都在抖，
    看不出是组件在动还是数据在动。"""
    return [
        50 + 42 * math.sin(i / 9 + phase) + noise * math.sin(i / 2.3 + phase)
        for i in range(n)
    ]


class PreviewApp(App):
    """Phase 0 三个原语的预览页。"""

    CSS_PATH = "theme/pto.tcss"
    TITLE = "Kunpeng DevKit AI · 渲染底座预览"

    BINDINGS = [
        ("space", "freeze", "冻结读数"),
        ("bracketright", "interval", "采样率档位"),
        ("a", "area", "折线/面积"),
        ("l", "layer", "AI 标注层"),
        ("s", "sort", "排序列"),
        ("t", "tier", "强制降级"),
        ("q", "quit", "退出"),
    ]

    def __init__(self, caps: Capabilities | None = None) -> None:
        super().__init__()
        self._caps = caps or detect()
        self._forced: Tier | None = None

    # ── 布局 ────────────────────────────────────────────────────────────
    def compose(self) -> ComposeResult:
        yield Label(self._banner(), id="statusbar")
        with VerticalScroll(id="main"):
            with Horizontal():
                yield BrailleChart("cpu · kunpeng-920", "cpu", id="chart-cpu",
                                   caps=self._caps)
                yield BrailleChart("npu · ascend", "npu", id="chart-npu",
                                   caps=self._caps)
            yield CoreHeatmap(64, 16, id="heatmap", caps=self._caps)
            yield KernelTable(COLUMNS, title="kernels", id="kernels")
            yield Static(self._specs(), id="specs", classes="panel")
        yield Footer()

    def get_theme_variable_defaults(self) -> dict[str, str]:
        """样式表在 mount 之前就解析，所以 ``$pto-*`` 必须从这里进去，
        不能只挂在主题上——否则 CSS 解析阶段就是 UnresolvedVariableError。"""
        return pto_variables()

    def on_mount(self) -> None:
        self.register_theme(pto_theme())
        self.theme = "pto"

        self.query_one("#chart-cpu", BrailleChart).extend(_demo_series(160, 0.0))
        self.query_one("#chart-npu", BrailleChart).extend(_demo_series(160, 2.1, 6.0))

        heat = self.query_one("#heatmap", CoreHeatmap)
        heat.update_utilisation(
            [abs(50 + 45 * math.sin(i / 5.5)) % 100 for i in range(64)]
        )
        heat.annotate([
            Annotation(tuple(range(34, 39)), "warning",
                       "持续 >80%，疑似跨 NUMA 内存访问"),
        ])

        self.query_one("#kernels", KernelTable).set_rows(KERNELS)

    # ── 说明面板 ────────────────────────────────────────────────────────
    def _banner(self) -> str:
        caps = self._caps
        bits = [
            f"truecolor {STATUS_GLYPH['done'] if caps.truecolor else STATUS_GLYPH['failed']}",
            f"braille {STATUS_GLYPH['done'] if caps.braille else STATUS_GLYPH['failed']}",
            f"mouse {STATUS_GLYPH['done'] if caps.mouse else STATUS_GLYPH['failed']}",
            f"graphics {STATUS_GLYPH['done'] if caps.graphics else STATUS_GLYPH['failed']}",
        ]
        forced = f"  强制降级 → {self._forced.label}" if self._forced else ""
        return f" 终端能力  {'  '.join(bits)}   上限 {caps.max_tier.label}{forced}"

    def _specs(self) -> str:
        lines = ["组件评审声明（VISUAL.md §6：渲染层 · 降级路径 · 键盘等价 · token）", ""]
        for name, spec in declared_components().items():
            lines.append(f"▸ {name}")
            lines.append("  " + spec.describe().replace("\n", "\n  "))
            if spec.degraded_as:
                lines.append(f"  降级形态：{spec.degraded_as}")
            lines.append("")
        return "\n".join(lines)

    # ── 动作：每一条都是键盘路径，鼠标只是可选加速 ─────────────────────
    def action_freeze(self) -> None:
        for chart in self.query(BrailleChart):
            chart.frozen = not chart.frozen
            chart.refresh()

    def action_interval(self) -> None:
        for chart in self.query(BrailleChart):
            chart.cycle_interval()

    def action_area(self) -> None:
        for chart in self.query(BrailleChart):
            chart.area = not chart.area
            chart.refresh()

    def action_layer(self) -> None:
        heat = self.query_one("#heatmap", CoreHeatmap)
        heat.show_annotations = not heat.show_annotations
        heat.refresh()

    def action_sort(self) -> None:
        self.query_one("#kernels", KernelTable).cycle_sort()

    def action_tier(self) -> None:
        """在原生能力与两档降级之间循环——把降级路径变成能按一下就看到的东西。"""
        order: list[Capabilities] = [
            self._caps,
            Capabilities(truecolor=True, braille=False, mouse=True, graphics=False),
            Capabilities(truecolor=False, braille=False, mouse=False, graphics=False),
        ]
        labels = [None, Tier.BLOCK, Tier.TEXT]
        idx = (labels.index(self._forced) + 1) % len(order)
        self._forced = labels[idx]
        caps = order[idx]
        for chart in self.query(BrailleChart):
            chart._caps = caps
            chart.refresh()
        heat = self.query_one("#heatmap", CoreHeatmap)
        heat._caps = caps
        heat.refresh()
        self.query_one("#statusbar", Label).update(self._banner())


def main() -> None:
    PreviewApp().run()
