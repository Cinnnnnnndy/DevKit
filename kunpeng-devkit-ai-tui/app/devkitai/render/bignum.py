"""像素数字与数图（stat tile）。

VISUAL.md §7 给了明确边界：**像素字仅用于 Logo 与数字**（成就计数、Act 编号、
Session Summary 里的关键指标），**正文永不像素化**。所以这里只有 0–9 与几个
符号，没有字母——想拿它拼标题的话，那已经越过边界了。

字形是 5 行 × 3 列。试过 3×3，太小：只用 █ 和空格的话 2 / 3 / 8 在 3×3 里
画出来几乎一样，得靠 ▄▟▛ 这类半块去凑，而混着半块的数字在不同等宽字体下
基线会飘。5 行足够让每个数字有唯一轮廓，且仍然只用一种字符。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .bars import bar
from .blocks import sparkline

ROWS = 5
_GLYPHS: dict[str, tuple[str, ...]] = {
    "0": ("███", "█ █", "█ █", "█ █", "███"),
    "1": ("  █", "  █", "  █", "  █", "  █"),
    "2": ("███", "  █", "███", "█  ", "███"),
    "3": ("███", "  █", "███", "  █", "███"),
    "4": ("█ █", "█ █", "███", "  █", "  █"),
    "5": ("███", "█  ", "███", "  █", "███"),
    "6": ("███", "█  ", "███", "█ █", "███"),
    "7": ("███", "  █", "  █", "  █", "  █"),
    "8": ("███", "█ █", "███", "█ █", "███"),
    "9": ("███", "█ █", "███", "  █", "███"),
    ".": ("   ", "   ", "   ", "   ", "█  "),
    "%": ("█ █", "  █", " █ ", "█  ", "█ █"),
    "+": ("   ", " █ ", "███", " █ ", "   "),
    "-": ("   ", "   ", "███", "   ", "   "),
    "×": ("   ", "█ █", " █ ", "█ █", "   "),
    "/": ("  █", "  █", " █ ", "█  ", "█  "),
    ":": ("   ", " █ ", "   ", " █ ", "   "),
    " ": ("   ", "   ", "   ", "   ", "   "),
}


class UnsupportedGlyph(KeyError):
    """像素字只有数字与几个符号——字母是刻意不支持的。"""


def big(text: str, *, gap: int = 1) -> list[str]:
    """把一串数字渲染成 5 行像素字。

    遇到不支持的字符直接抛 :class:`UnsupportedGlyph`，而不是静默替换成空格——
    静默降级的后果是"12.3GB"渲染成"12.3"，一个丢了单位的数字比没有数字更糟。
    """
    if not text:
        return [""] * ROWS
    glyphs = []
    for ch in text:
        try:
            glyphs.append(_GLYPHS[ch])
        except KeyError:
            raise UnsupportedGlyph(
                f"像素字不支持 {ch!r}——它只用于数字与 . % + - × / :。"
                f"单位与标签请用常规字号排在旁边（VISUAL.md §7：正文永不像素化）"
            ) from None
    joiner = " " * gap
    return [joiner.join(g[row] for g in glyphs) for row in range(ROWS)]


def width_of(text: str, *, gap: int = 1) -> int:
    """像素字渲染后的列宽——排版时先算宽再决定放不放得下。"""
    if not text:
        return 0
    return len(text) * 3 + (len(text) - 1) * gap


@dataclass(frozen=True)
class Stat:
    """数图（stat tile）：一个读数该带的全部上下文。

    光有数字是不够的——"QPS 61k"本身无法判断好坏。所以一块 tile 至少要能回答
    三个问题：现在多少（value）· 和之前比如何（delta）· 最近怎么走的（history）。
    """

    label: str
    value: float
    unit: str = ""
    #: 相对基线的变化率；``None`` 表示没有可比基线。
    delta: float | None = None
    #: 最近的采样，用于右侧 sparkline。
    history: Sequence[float] = ()
    #: 越大越好还是越小越好——决定 delta 的正负该被读成"改善"还是"退化"。
    higher_is_better: bool = True
    #: 有容量上限时给出，渲染成占用条。
    capacity: float | None = None

    @property
    def improved(self) -> bool | None:
        """这次变化算不算改善。``None`` = 没有基线，不下结论。

        这是 tile 上**唯一**该出现语义色的地方——它是结论不是数据。
        数值本身与 bar 一律走中性或域色阶。
        """
        if self.delta is None or self.delta == 0:
            return None
        return (self.delta > 0) == self.higher_is_better

    def delta_text(self) -> str:
        if self.delta is None:
            return ""
        return f"{self.delta:+.0%}"

    def value_text(self, digits: int = 1) -> str:
        return f"{self.value:.{digits}f}".rstrip("0").rstrip(".") or "0"

    def spark(self, width: int) -> str:
        return sparkline(self.history, width) if self.history else ""

    def capacity_bar(self, width: int) -> str:
        if self.capacity is None or self.capacity <= 0:
            return ""
        return bar(self.value, 0.0, self.capacity, width)
