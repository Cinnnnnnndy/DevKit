"""Braille 历史曲线 · T2（``docs/TUI-CAPABILITY.md`` §3 ①）。

CPU / NPU 利用率历史、算子 latency 趋势、内存增长。采样率随面板高度自适应，
档位可调（250ms / 500ms / 2s / 5s）——这是 btop 那条"渲染精度分档"的做法。

降级：T2 → T1 sparkline → T0 数字 + 百分比。三层用的是**同一份采样缓冲**和
**同一个右对齐规则**，所以切层时视线不用重新找位置。

标题嵌在上边框、状态嵌在下边框——用的是 Textual 原生的
``border_title`` / ``border_subtitle``，不是手画 ``┌─┐``。第一版是手画的，
按码位而不是按 cell 拼接 ``─`` 的填充长度，中文标签下会算错宽度、边框折行
（``COMPONENT.md`` 那条"标题嵌入上边框"的约定因此有了两种互相打架的实现）。
原生边框在 Rich 内部按 cell 宽度截断/填充，这整类 bug 连测都不用测了——
详见 ``docs/COMPONENT.md`` "Canvas 层的框" 一节。
"""

from __future__ import annotations

from collections import deque
from typing import Iterable

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
    BrailleChart {
        width: 1fr; height: auto; background: $pto-surface-1;
        border: solid $pto-border-subtle;
    }
    BrailleChart:focus-within { border: solid $pto-border-strong; }
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
        # 高度写死成"rows 行画布 + 上下各一行边框"，不靠 height:auto 去猜。
        # auto 要先渲染一次才知道多高，而这个组件的渲染宽度又依赖最终布局，
        # 一来一回会多留出几行空白。边框现在是原生的，占用的两行不再由
        # render() 自己吐出来，Textual 会在内容区外面单独画。
        self.styles.height = self.rows + 2
        # 标题是身份，构造时就定了，不随数据变——只设一次，省得每帧都触发
        # border_title 的 setter（它会主动调一次 refresh()）。
        self.border_title = Text(self.title, style=foreground(SURFACE_1, "secondary"))

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
        # self.size 是**内容区**尺寸，边框占的那两行两列已经被 Textual 减掉了——
        # 不用再像手画边框那版一样自己 -2、拿 cell_len 去凑填充长度。
        width = max(8, self.size.width or 40)
        cur = self._samples[-1] if self._samples else 0.0
        peak = max(self._samples, default=0.0)
        tier = self.tier
        self.border_subtitle = self._status_text(cur, peak, tier)

        if tier >= Tier.BRAILLE:
            return self._render_braille(width, cur)
        if tier is Tier.BLOCK:
            return self._render_blocks(width, cur)
        return self._render_text(cur, peak)

    def _status_text(self, cur: float, peak: float, tier: Tier) -> Text:
        """下边框里的状态：采样间隔 · 当前 / 峰值 · 当前降级层。

        随 tier / 冻结态 / 数据变，所以每次 render() 都重算，不像标题
        （身份，只在 on_mount 设一次）。
        """
        secondary = foreground(SURFACE_1, "secondary")
        out = Text()
        if self.frozen:
            out.append("⏸ 冻结  ", style=secondary)
        out.append(f"{self.sample_interval_ms}ms · 当前 {cur:5.1f}{self.unit}"
                    f"  峰值 {peak:5.1f}{self.unit} · {tier.label}", style=secondary)
        return out

    def _series_color(self, value: float) -> str:
        # 档位由**当前值**定，而不是逐点定——逐点上色会让一条线出现五种亮度，
        # 读起来是噪声不是信息。整条线一个亮度，亮度本身表达"现在多忙"。
        return sequential(value, 0.0, 100.0, self.domain)

    def _render_braille(self, width: int, cur: float) -> Text:
        canvas = braille.plot_series(
            list(self._samples), cols=width, rows=self.rows, lo=0.0, hi=100.0,
            area=self.area,
        )
        color = self._series_color(cur)
        out = Text()
        for i, row in enumerate(canvas.rows_text()):
            if i:
                out.append("\n")
            out.append(row, style=color)
        return out

    def _render_blocks(self, width: int, cur: float) -> Text:
        return Text(
            blocks.sparkline(list(self._samples), width, lo=0.0, hi=100.0),
            style=self._series_color(cur),
        )

    def _render_text(self, cur: float, peak: float) -> Text:
        # T0 兼容底线：图没了，但"现在多少、峰值多少"这两个判断依据必须留下——
        # 边框已经把它们放进了 border_subtitle，内容区只留标题一句话。
        return Text(f"  {self.title}", style=foreground(SURFACE_1, "fg"))
