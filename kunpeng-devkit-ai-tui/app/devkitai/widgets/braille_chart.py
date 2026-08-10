"""Braille 历史曲线 · T2（``docs/TUI-CAPABILITY.md`` §3 ①）。

CPU / NPU 利用率历史、算子 latency 趋势、内存增长。采样率随面板高度自适应，
档位可调（250ms / 500ms / 2s / 5s）——这是 btop 那条"渲染精度分档"的做法。

降级：T2 → T1 sparkline → T0 数字 + 百分比。三层用的是**同一份采样缓冲**和
**同一个右对齐规则**，所以切层时视线不用重新找位置。
"""

from __future__ import annotations

from collections import deque
from typing import Iterable

from rich.cells import cell_len
from rich.text import Text
from textual.reactive import reactive
from textual.widgets import Static

from ..render import blocks, braille
from ..render.ramp import sequential
from ..spec import ComponentSpec
from ..tiers import Capabilities, Tier, resolve
from ..tokens import DOMAIN_RAMPS, foreground, SURFACE_1

SAMPLE_INTERVALS_MS = (250, 500, 2000, 5000)


class BrailleChart(Static):
    """一条按域着色的历史曲线。

    ``domain`` 决定色相（CPU 绿 / NPU 紫 / Memory 橙 / IO 琥珀），
    **当前值**决定档位——色阶定身份，档位定强度。
    """

    SPEC = ComponentSpec(
        tier=Tier.BRAILLE,
        keyboard={
            "space": "冻结 / 解冻读数",
            "[ ]": "调采样率档位",
            "a": "折线 / 面积切换",
        },
        tokens=("DOMAIN_RAMPS", "SURFACE_1", "foreground(muted)"),
        degraded_as="T1 一行八分块 sparkline；再降为 T0 的『当前值 + 峰值』两个数字",
        notes="Braille 字形宽度在中文等宽字体下未必是 1，探测不到就靠 "
        "DEVKITAI_NO_BRAILLE 显式降级",
    )

    DEFAULT_CSS = """
    BrailleChart { width: 1fr; height: auto; background: $pto-surface-1; }
    """

    frozen: reactive[bool] = reactive(False)
    area: reactive[bool] = reactive(False)

    def __init__(
        self,
        title: str,
        domain: str = "cpu",
        *,
        rows: int = 3,
        capacity: int = 512,
        unit: str = "%",
        caps: Capabilities | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        if domain not in DOMAIN_RAMPS:
            raise ValueError(f"未知的域 {domain!r}；可选：{sorted(DOMAIN_RAMPS)}")
        self.title = title
        self.domain = domain
        self.rows = rows
        self.unit = unit
        self._samples: deque[float] = deque(maxlen=capacity)
        self._interval_idx = 2  # 默认 2000ms，对齐 btop
        self._caps = caps

    def on_mount(self) -> None:
        # 高度写死成"表头 + rows 行画布 + 底栏"，不靠 height:auto 去猜。
        # auto 要先渲染一次才知道多高，而这个组件的渲染宽度又依赖最终布局，
        # 一来一回会多留出几行空白。
        self.styles.height = self.rows + 2

    # ── 数据 ────────────────────────────────────────────────────────────
    def push(self, value: float) -> None:
        """喂一个采样。冻结时仍然收数据，只是不重绘——解冻后历史是连续的。"""
        self._samples.append(value)
        if not self.frozen:
            self.refresh()

    def extend(self, values: Iterable[float]) -> None:
        for v in values:
            self._samples.append(v)
        if not self.frozen:
            self.refresh()

    @property
    def sample_interval_ms(self) -> int:
        return SAMPLE_INTERVALS_MS[self._interval_idx]

    def cycle_interval(self, step: int = 1) -> int:
        self._interval_idx = (self._interval_idx + step) % len(SAMPLE_INTERVALS_MS)
        self.refresh()
        return self.sample_interval_ms

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
        width = max(8, self.size.width or 40)
        cur = self._samples[-1] if self._samples else 0.0
        peak = max(self._samples, default=0.0)
        tier = self.tier

        muted = foreground(SURFACE_1, "muted")
        head = Text()
        head.append(f"┌{self.title}", style=foreground(SURFACE_1, "secondary"))
        tail = f"{self.sample_interval_ms}ms─{tier.label}┐"
        # cell_len 而不是 len：层名里有 CJK（"块字符"/"真彩热力"），一个汉字占 2 格。
        # 用 len() 算出来的边框会短一截，整行折行——这类 bug 只在中文标签下出现，
        # 英文界面上测不出来。
        head.append(
            "─" * max(1, width - cell_len(self.title) - cell_len(tail) - 1), style=muted
        )
        head.append(tail, style=muted)

        body = Text()
        if tier >= Tier.BRAILLE:
            body = self._render_braille(width, cur, peak)
        elif tier is Tier.BLOCK:
            body = self._render_blocks(width, cur, peak)
        else:
            body = self._render_text(cur, peak)

        out = Text()
        out.append_text(head)
        out.append("\n")
        out.append_text(body)
        return out

    def _series_color(self, value: float) -> str:
        # 档位由**当前值**定，而不是逐点定——逐点上色会让一条线出现五种亮度，
        # 读起来是噪声不是信息。整条线一个亮度，亮度本身表达"现在多忙"。
        return sequential(value, 0.0, 100.0, self.domain)

    def _render_braille(self, width: int, cur: float, peak: float) -> Text:
        canvas = braille.plot_series(
            list(self._samples), cols=width - 2, rows=self.rows, lo=0.0, hi=100.0,
            area=self.area,
        )
        color = self._series_color(cur)
        muted = foreground(SURFACE_1, "muted")
        out = Text()
        for i, row in enumerate(canvas.rows_text()):
            out.append("│", style=muted)
            out.append(row, style=color)
            out.append("│", style=muted)
            out.append("\n")
        out.append_text(self._footer(width, cur, peak))
        return out

    def _render_blocks(self, width: int, cur: float, peak: float) -> Text:
        muted = foreground(SURFACE_1, "muted")
        out = Text()
        out.append("│", style=muted)
        out.append(blocks.sparkline(list(self._samples), width - 2, lo=0.0, hi=100.0),
                   style=self._series_color(cur))
        out.append("│\n", style=muted)
        out.append_text(self._footer(width, cur, peak))
        return out

    def _render_text(self, cur: float, peak: float) -> Text:
        # T0 兼容底线：图没了，但"现在多少、峰值多少"这两个判断依据必须留下。
        return Text(
            f"  {self.title}  当前 {cur:5.1f}{self.unit}   峰值 {peak:5.1f}{self.unit}",
            style=foreground(SURFACE_1, "fg"),
        )

    def _footer(self, width: int, cur: float, peak: float) -> Text:
        muted = foreground(SURFACE_1, "muted")
        stat = f" 当前 {cur:5.1f}{self.unit}  峰值 {peak:5.1f}{self.unit} "
        if self.frozen:
            stat = " ⏸ 冻结 " + stat
        out = Text()
        out.append("└", style=muted)
        out.append("─" * max(0, width - cell_len(stat) - 2), style=muted)
        # 数值走中性前景——进度与读数属于数据可视化，数值本身承担强调，不上品牌色
        out.append(stat, style=foreground(SURFACE_1, "secondary"))
        out.append("┘", style=muted)
        return out
