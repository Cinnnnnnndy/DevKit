"""T1 · 块字符 —— Braille 掉下来的那一层，也是 T3 掉下来的那一层。

三组字形，各有各的用处：

* **垂直八分块** ``▁▂▃▄▅▆▇█`` —— 一格 8 个台阶，做 sparkline 与柱状
* **半块** ``▀▄█`` —— 一格承载 2 个垂直像素，**把终端的垂直分辨率翻倍**，
  是标识降级、稀疏火焰图、小尺寸 sparkline 的性价比之王
* **实心 / 空槽** ``█░`` —— gauge 与进度条

半块那一招还有个额外好处：前景色配背景色可以在**一格里表达两种颜色**，
所以 36×13 字符能画出 36×26 像素的位图。
"""

from __future__ import annotations

from typing import Sequence

#: 索引 0 是空格；1–8 是 1/8 到 8/8。
VERTICAL = " ▁▂▃▄▅▆▇█"
UPPER_HALF = "▀"
LOWER_HALF = "▄"
FULL = "█"
EMPTY = "░"


def _level(value: float, lo: float, hi: float, steps: int) -> int:
    if hi <= lo:
        return 0
    t = (value - lo) / (hi - lo)
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return int(round(t * steps))


def sparkline(values: Sequence[float], width: int, *, lo: float | None = None,
              hi: float | None = None) -> str:
    """T2 Braille 曲线的降级形态：一行八分块。

    右对齐，和 Braille 版一致——同一份数据在两层之间切换时，最新的样本
    始终贴着右边缘，视线不用重新找位置。
    """
    if width <= 0:
        return ""
    if not values:
        return " " * width
    window = list(values[-width:])
    data_lo = min(window) if lo is None else lo
    data_hi = max(window) if hi is None else hi
    cells = "".join(VERTICAL[_level(v, data_lo, data_hi, 8)] for v in window)
    return cells.rjust(width)


def gauge(fraction: float, width: int) -> str:
    """进度 / 占用条。``fraction`` 超出 [0,1] 会被夹住。

    注意这里只出**字形**不出颜色：进度条属于数据可视化，按 §「强调色配额」
    它一律走中性，数值本身承担强调——所以着色由调用方按域色阶决定，
    而不是这个函数替它决定。
    """
    if width <= 0:
        return ""
    f = 0.0 if fraction < 0.0 else (1.0 if fraction > 1.0 else fraction)
    filled = int(round(f * width))
    return FULL * filled + EMPTY * (width - filled)


def segmented(parts: Sequence[float], width: int) -> list[tuple[str, int]]:
    """分段 gauge：一条 bar 表达多个量（Weights / KV Cache / Activation）。

    返回 ``(字形, 段长)`` 列表，颜色由调用方按段的语义决定。
    末段吸收取整误差，保证总宽恰好是 ``width``——差一格在终端里是看得见的。
    """
    total = sum(parts)
    if width <= 0 or total <= 0:
        return [(EMPTY, max(0, width))]
    out: list[tuple[str, int]] = []
    used = 0
    for p in parts[:-1]:
        n = int(round(p / total * width))
        out.append((FULL, n))
        used += n
    out.append((FULL, max(0, width - used)))
    return out


def half_block_column(top_lit: bool, bottom_lit: bool) -> str:
    """一格两像素：把两个垂直像素压进一个字符格。

    四种组合里只有三种要字形——两个都不亮就是空格。真正的用法是配合
    前景色 / 背景色：上半像素走前景色，下半像素走背景色，一格两色。
    """
    if top_lit and bottom_lit:
        return FULL
    if top_lit:
        return UPPER_HALF
    if bottom_lit:
        return LOWER_HALF
    return " "


def heat_glyph(value: float, lo: float, hi: float) -> str:
    """T3 真彩热力掉到 T1 时用的字形梯度。

    颜色被抽掉之后，**强度必须由字形接住**，否则一张热力图会退化成
    一片同样的方块——那就等于把信息丢了，而不是降级。
    """
    ramp = "░▒▓█"
    return ramp[min(_level(value, lo, hi, len(ramp) - 1), len(ramp) - 1)]
