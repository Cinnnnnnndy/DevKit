"""多核热力网格 · T3 · 鲲鹏特化（``docs/TUI-CAPABILITY.md`` §3 ②）。

鲲鹏 920 多核（32/48/64C）+ NUMA 亲和性可视化——**CLI 完全做不到、而对鲲鹏
调优最关键的一张图**。颜色承载利用率，位置承载拓扑。

这里同时兑现 P26 AI 标注层：AI 的判断是**独立一层**叠在数据之上，
可以整层开关。标注只用语义色的**字符**（角标 / 描边符号），不改单元格底色——
底色是数据，角标是结论，两套颜色系统不能混。

降级：T3 → T1 灰阶 + 字形梯度（``░▒▓█``）。颜色被抽掉之后强度由字形接住，
否则热力图会退化成一片同样的方块，那是丢信息不是降级。

标题嵌在上边框（Textual 原生 ``border_title`` / ``border_subtitle``），
和 :class:`~devkitai.widgets.braille_chart.BrailleChart` 用同一套约定——
见 ``docs/COMPONENT.md`` "Canvas 层的框"。这个组件原来完全没有边框，
标题只是内容区顶上一行文字，和有边框的 BrailleChart 并排摆在同一个
Canvas 里会看着不成一套。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from rich.text import Text
from textual.reactive import reactive
from textual.widgets import Static

from ..render import blocks
from ..render.ramp import grayscale, sequential
from ..spec import ComponentSpec
from ..tiers import Capabilities, Tier, resolve
from ..tokens import SEMANTIC, SURFACE_1, foreground


@dataclass(frozen=True)
class Annotation:
    """AI 标注层的一条结论。``severity`` 取 ``SEMANTIC`` 的键。"""

    cores: tuple[int, ...]
    severity: str
    message: str

    @property
    def glyph(self) -> str:
        return {"success": "✓", "warning": "⚠", "danger": "✕"}[self.severity]


class CoreHeatmap(Static):
    """N 核利用率热力网格 + NUMA 亲和条。"""

    SPEC = ComponentSpec(
        tier=Tier.TRUECOLOR,
        keyboard={
            "←→↑↓": "移动核心焦点",
            "enter": "下钻到该核的进程 / 算子",
            "n": "按 NUMA 节点分组折叠",
            "l": "开关 AI 标注层",
        },
        tokens=("DOMAIN_RAMPS[cpu]", "SEMANTIC", "SURFACE_1", "foreground(muted)"),
        degraded_as="T1 灰阶 + ░▒▓█ 字形梯度，NUMA 条改用块字符 gauge",
        notes="标注层只上语义色字符，永不改单元格底色——底色是数据，角标是结论",
    )

    DEFAULT_CSS = """
    CoreHeatmap {
        height: auto; background: $pto-surface-1;
        border: solid $pto-border-subtle;
    }
    CoreHeatmap:focus-within { border: solid $pto-border-strong; }
    """

    show_annotations: reactive[bool] = reactive(True)

    def __init__(
        self,
        cores: int = 64,
        per_row: int = 16,
        *,
        caps: Capabilities | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        if cores <= 0 or per_row <= 0:
            raise ValueError("核数与每行核数都必须为正")
        self.cores = cores
        self.per_row = per_row
        self._util: list[float] = [0.0] * cores
        self._numa: list[float] = []
        self._annotations: list[Annotation] = []
        self._caps = caps

    def on_mount(self) -> None:
        # 标题是身份（多少核），构造时就定了——只设一次，同 BrailleChart。
        self.border_title = Text(f"{self.cores}-core heatmap",
                                  style=foreground(SURFACE_1, "secondary"))

    # ── 数据 ────────────────────────────────────────────────────────────
    def update_utilisation(self, values: Sequence[float]) -> None:
        if len(values) != self.cores:
            raise ValueError(f"需要 {self.cores} 个利用率，收到 {len(values)}")
        self._util = [float(v) for v in values]
        # NUMA 节点利用率由成员核聚合得出，不单独喂——两者不一致会让人怀疑
        # 是哪个数字错了，而不是去看图。
        group = max(1, self.cores // 4)
        self._numa = [
            sum(self._util[i : i + group]) / group for i in range(0, self.cores, group)
        ]
        self.refresh()

    def annotate(self, annotations: Sequence[Annotation]) -> None:
        self._annotations = list(annotations)
        self.refresh()

    def _annotation_for(self, core: int) -> Annotation | None:
        for a in self._annotations:
            if core in a.cores:
                return a
        return None

    # ── 渲染 ────────────────────────────────────────────────────────────
    @property
    def tier(self) -> Tier:
        caps = self._caps
        if caps is None:
            from ..tiers import detect

            caps = detect()
            self._caps = caps
        return resolve(self.SPEC.tier, caps)

    def render(self) -> Text:
        tier = self.tier
        truecolor = tier >= Tier.TRUECOLOR
        muted = foreground(SURFACE_1, "muted")
        secondary = foreground(SURFACE_1, "secondary")

        # 图例 + 当前降级层随 tier 变，挪进下边框；标题（核数）不变，
        # on_mount 里设过一次就够了。
        legend = "▁ idle  ▃ low  ▅ mid  █ hot" if not truecolor else "低 ▏▍▋█ 高"
        self.border_subtitle = Text(f"{legend} · {tier.label}", style=secondary)

        out = Text()
        group = max(1, self.cores // 4)
        for start in range(0, self.cores, self.per_row):
            row = self._util[start : start + self.per_row]
            out.append(f"{start:>3}-{start + len(row) - 1:<3} ", style=muted)
            for value in row:
                if truecolor:
                    # 颜色承载数值；字形统一用实心块，避免字形和颜色重复编码
                    out.append("█", style=sequential(value, 0.0, 100.0, "cpu"))
                else:
                    out.append(blocks.heat_glyph(value, 0.0, 100.0),
                               style=grayscale(value, 0.0, 100.0))
            if start % group == 0:
                out.append_text(self._numa_cell(start // group, truecolor))
            out.append("\n")
            out.append_text(self._marker_row(start, len(row)))

        for note in self._annotations if self.show_annotations else ():
            span = f"core {min(note.cores)}-{max(note.cores)}"
            out.append(f"{note.glyph} AI: ", style=SEMANTIC[note.severity])
            out.append(f"{span} {note.message}\n", style=secondary)
        return out

    def _marker_row(self, start: int, length: int) -> Text:
        """AI 标注层单独占一行，画在对应核的正下方。

        第一版是把角标**插在单元格后面**的，结果每多一个标注，那一行就往右
        挤一格，NUMA 条跟着错位——热力网格靠的就是位置承载拓扑，一错位这张图
        就废了。标注是独立图层，所以它也该占独立的一行：数据网格一个字符不动，
        标记在下方对齐，整层还能一键开关。
        """
        out = Text()
        if not self.show_annotations or not self._annotations:
            return out
        marks = {
            offset: note
            for offset in range(length)
            if (note := self._annotation_for(start + offset)) is not None
        }
        if not marks:
            return out
        out.append(" " * 8)  # 与行首 "  0-15  " 的宽度对齐
        for offset in range(length):
            note = marks.get(offset)
            if note is None:
                out.append(" ")
            else:
                out.append(note.glyph, style=SEMANTIC[note.severity])
        out.append("\n")
        return out

    def _numa_cell(self, node: int, truecolor: bool) -> Text:
        out = Text()
        if node >= len(self._numa):
            return out
        value = self._numa[node]
        muted = foreground(SURFACE_1, "muted")
        out.append(f"   NUMA{node} ", style=muted)
        bar = blocks.gauge(value / 100.0, 8)
        out.append(bar, style=sequential(value, 0.0, 100.0, "cpu") if truecolor
                   else grayscale(value, 0.0, 100.0))
        out.append(f" {value:4.0f}%", style=foreground(SURFACE_1, "secondary"))
        return out
