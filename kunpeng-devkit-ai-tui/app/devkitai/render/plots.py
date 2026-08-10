"""坐标系图元：折线 · 散点 · 面积 · 火焰图 · 泳道 Timeline。

这一族全部建立在 :mod:`devkitai.render.braille` 的点阵画布上（T2），因为它们
共同的需求是**在有限行高里表达连续量**——2×4 = 8 倍密度是终端里唯一能做到
这件事的手段。

一条贯穿的规则：**多系列必须共用量程**。分别归一化的多条曲线放在一起，
每条都填满画布，看着都一样忙——而并置的全部意义就是比较。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .braille import BrailleCanvas, plot_series


@dataclass(frozen=True)
class Axis:
    """坐标轴刻度。终端画不出连续轴，只能给端点与中点。"""

    lo: float
    hi: float
    unit: str = ""

    def ticks(self, count: int = 3) -> list[str]:
        if count < 2:
            return [f"{self.hi:g}{self.unit}"]
        step = (self.hi - self.lo) / (count - 1)
        return [f"{self.lo + step * i:g}{self.unit}" for i in range(count)]


def multi_series(
    series: Sequence[Sequence[float]],
    cols: int,
    rows: int,
    *,
    lo: float | None = None,
    hi: float | None = None,
    area: bool = False,
) -> list[BrailleCanvas]:
    """多条曲线，**共用量程**，每条一张画布。

    每条单独返回是为了让调用方分别着色——色阶定身份（哪条泳道），
    档位定强度（多忙）。合并成一张画布就没法分色了，而在终端里
    位置和粗细都不足以区分曲线，只剩颜色可用。
    """
    flat = [v for s in series for v in s]
    scale_lo = min(flat, default=0.0) if lo is None else lo
    scale_hi = max(flat, default=1.0) if hi is None else hi
    return [
        plot_series(s, cols, rows, lo=scale_lo, hi=scale_hi, area=area) for s in series
    ]


def scatter(
    points: Sequence[tuple[float, float]],
    cols: int,
    rows: int,
    *,
    x: Axis | None = None,
    y: Axis | None = None,
) -> BrailleCanvas:
    """散点图：Roofline、batch-latency、量化前后的精度-性能。

    点阵画布天然适合散点——一个字符格能放 8 个独立的点，密集区域会自然
    加深，稀疏区域仍然看得见单点。这是块字符做不到的：一格一个方块，
    两个点落在同一格就只剩一个。
    """
    canvas = BrailleCanvas(cols, rows)
    if not points:
        return canvas
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    ax = x or Axis(min(xs), max(xs))
    ay = y or Axis(min(ys), max(ys))
    x_span = ax.hi - ax.lo
    y_span = ay.hi - ay.lo
    for px, py in points:
        cx = 0 if x_span <= 0 else (px - ax.lo) / x_span
        cy = 0 if y_span <= 0 else (py - ay.lo) / y_span
        canvas.set(
            int(round(max(0.0, min(1.0, cx)) * (canvas.width - 1))),
            # y 翻转：值越大越靠上
            int(round((1.0 - max(0.0, min(1.0, cy))) * (canvas.height - 1))),
        )
    return canvas


@dataclass(frozen=True)
class Frame:
    """火焰图的一个栈帧。"""

    name: str
    #: 自身 + 子树的总耗时（或采样数）。
    value: float
    depth: int
    #: 相对整图起点的偏移，与 value 同单位。
    offset: float = 0.0


def flame(frames: Sequence[Frame], width: int, *, total: float | None = None
          ) -> list[list[tuple[Frame, int, int]]]:
    """火焰图：按深度分行，每行返回 ``(帧, 起始列, 宽度)``。

    终端里的火焰图有个硬约束：**一帧窄于 1 格就画不出来**，而真实火焰图
    永远有一大堆窄帧。这里不做"最小宽度 1 格"的兜底——那会让窄帧集体
    虚胖，把宽帧挤走，图就假了。窄帧直接丢弃，由调用方在图下方标出
    "N 帧过窄未显示"，让人知道自己没看全。

    深度方向不做降采样：火焰图的价值在于栈的形状，压扁了就没了。
    """
    if width <= 0 or not frames:
        return []
    span = total if total is not None else max(
        (f.offset + f.value for f in frames), default=1.0
    )
    if span <= 0:
        return []

    by_depth: dict[int, list[tuple[Frame, int, int]]] = {}
    for f in frames:
        start = int(f.offset / span * width)
        cells = int(round(f.value / span * width))
        if cells < 1:
            continue  # 过窄的帧宁可不画，也不虚胖
        by_depth.setdefault(f.depth, []).append((f, start, min(cells, width - start)))
    return [by_depth.get(d, []) for d in range(max(by_depth) + 1)] if by_depth else []


def dropped_frames(frames: Sequence[Frame], width: int, *, total: float | None = None) -> int:
    """有多少帧因为太窄没画出来——必须显式告诉用户，否则"看全了"是个错觉。"""
    if width <= 0 or not frames:
        return 0
    span = total if total is not None else max(
        (f.offset + f.value for f in frames), default=1.0
    )
    if span <= 0:
        return len(frames)
    return sum(1 for f in frames if int(round(f.value / span * width)) < 1)


@dataclass(frozen=True)
class Span:
    """Timeline 泳道上的一段。"""

    lane: str
    start: float
    end: float
    label: str = ""


def timeline(spans: Sequence[Span], width: int, *, window: tuple[float, float] | None = None
             ) -> list[tuple[str, list[tuple[Span, int, int]]]]:
    """泳道 Timeline：每条泳道一行，返回 ``(泳道名, [(段, 起始列, 宽度)])``。

    泳道顺序按**首次出现**排，不按字母序——Trace 的阅读顺序是执行顺序，
    按字母排会把 CPU / NPU / HBM 打散，而"谁在等谁"正是要靠相邻行看出来的。
    """
    if width <= 0 or not spans:
        return []
    lo = window[0] if window else min(s.start for s in spans)
    hi = window[1] if window else max(s.end for s in spans)
    span_len = hi - lo
    if span_len <= 0:
        return []

    lanes: list[str] = []
    for s in spans:
        if s.lane not in lanes:
            lanes.append(s.lane)

    out: list[tuple[str, list[tuple[Span, int, int]]]] = []
    for lane in lanes:
        cells: list[tuple[Span, int, int]] = []
        for s in (s for s in spans if s.lane == lane):
            start = int((s.start - lo) / span_len * width)
            end = int((s.end - lo) / span_len * width)
            cells.append((s, max(0, start), max(1, min(end, width) - max(0, start))))
        out.append((lane, cells))
    return out
