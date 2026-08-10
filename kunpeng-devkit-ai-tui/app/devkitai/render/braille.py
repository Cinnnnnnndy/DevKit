"""T2 · Braille 点阵画布 —— 一个字符格 2×4 = 8 倍密度。

这是 T1 层最高性价比的一招之外、密度上真正的跳变：同样一行高度，块字符能
表达 8 个台阶，Braille 能表达 4 个像素行 × 2 列，画出来是真折线而不是柱子。

Unicode Braille (U+2800) 的点位编号是历史遗留，不是从左到右从上到下：

    1 4
    2 5
    3 6
    7 8

所以 (行, 列) → 位 的映射必须查表，不能算。写错这张表的症状是曲线看着
"对但抖"——第 4 行像素跑到了别的位上。
"""

from __future__ import annotations

from typing import Iterable, Sequence

BRAILLE_BASE = 0x2800

#: ``_DOTS[row][col]`` → 该像素在字符里占的位。row ∈ [0,4)，col ∈ [0,2)。
_DOTS = (
    (0x01, 0x08),
    (0x02, 0x10),
    (0x04, 0x20),
    (0x40, 0x80),
)

CELL_W = 2
CELL_H = 4


class BrailleCanvas:
    """按字符格计尺寸、按像素点绘制的点阵画布。

    坐标原点在**左上**，和终端一致；调用方不需要在脑子里翻转 y。
    """

    __slots__ = ("cols", "rows", "_bits")

    def __init__(self, cols: int, rows: int) -> None:
        if cols <= 0 or rows <= 0:
            raise ValueError(f"画布尺寸必须为正，收到 {cols}×{rows}")
        self.cols = cols
        self.rows = rows
        self._bits = bytearray(cols * rows)

    @property
    def width(self) -> int:
        """像素宽。"""
        return self.cols * CELL_W

    @property
    def height(self) -> int:
        """像素高。"""
        return self.rows * CELL_H

    def clear(self) -> None:
        self._bits[:] = bytes(len(self._bits))

    def set(self, x: int, y: int) -> bool:
        """点亮一个像素。越界静默忽略并返回 ``False``——绘图循环里夹坐标比
        到处写边界判断更容易漏，这里统一兜住。"""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        cell = (y // CELL_H) * self.cols + (x // CELL_W)
        self._bits[cell] |= _DOTS[y % CELL_H][x % CELL_W]
        return True

    def line(self, x0: int, y0: int, x1: int, y1: int) -> None:
        """Bresenham 直线。相邻采样点之间连线，曲线才不会在陡变处断成点。"""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def column(self, x: int, y_top: int, y_bottom: int) -> None:
        """填一整列（面积图用）。"""
        if y_top > y_bottom:
            y_top, y_bottom = y_bottom, y_top
        for y in range(max(0, y_top), min(self.height, y_bottom + 1)):
            self.set(x, y)

    def rows_text(self) -> list[str]:
        """渲染成每行一个字符串。空格用 U+2800（空白盲文），**不能用普通空格**
        ——否则等宽字体下空白格与有点的格宽度可能不同，整张图会错位。"""
        out: list[str] = []
        for r in range(self.rows):
            base = r * self.cols
            out.append("".join(chr(BRAILLE_BASE + self._bits[base + c]) for c in range(self.cols)))
        return out

    def __str__(self) -> str:
        return "\n".join(self.rows_text())


def plot_series(
    values: Sequence[float],
    cols: int,
    rows: int,
    *,
    lo: float | None = None,
    hi: float | None = None,
    area: bool = False,
    invert: bool = False,
) -> BrailleCanvas:
    """把一串采样值画成折线（``area=True`` 时画成面积图）。

    只取最后 ``cols * 2`` 个采样——画布有多宽就看多久的历史，多余的样本
    留在缓冲里没有意义。量程可以显式给，用于让多张图共用同一把尺子；
    不给就按数据自适应。

    ``invert=True`` 让数值向下增长（面积从顶边往下填），供双向图的下半幅使用。
    """
    canvas = BrailleCanvas(cols, rows)
    if not values:
        return canvas

    window = list(values[-canvas.width :])
    data_lo = min(window) if lo is None else lo
    data_hi = max(window) if hi is None else hi
    span = data_hi - data_lo

    def to_y(v: float) -> int:
        if span <= 0:
            return 0 if invert else canvas.height - 1
        t = (v - data_lo) / span
        t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
        # 常态是翻转的：值越大越靠上。减 1 是因为像素行是 0-based。
        return int(round((t if invert else 1.0 - t) * (canvas.height - 1)))

    # 右对齐：最新的样本贴右边缘，这样窗口没填满时曲线不会"浮"在左边。
    x0 = canvas.width - len(window)
    prev: tuple[int, int] | None = None
    for i, v in enumerate(window):
        x = x0 + i
        y = to_y(v)
        if area:
            canvas.column(x, y, 0 if invert else canvas.height - 1)
        elif prev is not None:
            canvas.line(prev[0], prev[1], x, y)
        else:
            canvas.set(x, y)
        prev = (x, y)
    return canvas


def mirrored(
    up: Sequence[float],
    down: Sequence[float],
    cols: int,
    rows_each: int,
    *,
    hi: float | None = None,
) -> tuple[BrailleCanvas, BrailleCanvas]:
    """双向面积图（收/发、读/写、Host↔Device）。

    两半**共用同一个量程**，否则上下两条曲线的"高"不是一个意思，
    并置就失去了意义——而并置正是这张图存在的理由。
    """
    peak = hi if hi is not None else max([*up, *down], default=1.0)
    top = plot_series(up, cols, rows_each, lo=0.0, hi=peak, area=True)
    bottom = plot_series(down, cols, rows_each, lo=0.0, hi=peak, area=True, invert=True)
    return top, bottom
