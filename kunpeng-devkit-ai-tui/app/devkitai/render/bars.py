"""条形族图元：Metric Bar · 排行 · 多列 · Before/After · 水位 · 进度。

**八分之一格的水平精度**是这一族的地基。垂直方向早就有 ``▁▂▃▄▅▆▇█``，
水平方向同样有一套 ``▏▎▍▌▋▊▉█``——一个 10 格宽的 bar 因此能表达 80 档
而不是 10 档。不用它的话，10 格宽的 bar 上 82% 和 85% 画出来一模一样，
而"兼容性 82%"这种数字恰恰是要拿来做判断的。

一处规范冲突，在这里按 VISUAL.md 解：COMPONENT.md §3.1 写的是 Metric Bar
要按阈值着 warn / error 色，但 VISUAL.md §1.6 定死**语义色只上字符与短文本、
永不上色块**。VISUAL.md 是更新的那份（v0.5 对 v0.2）且是 ★ 主文档，所以：

    bar 本身  → 域色阶顺序取档（数据）
    阈值判断  → 落在数值文字与前缀符号上（结论）

这不是折中，是把"数据"和"结论"分到两套颜色系统里——一个 90% 的利用率本身
不是错误，只有当它被判定为问题时才该出现语义色。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

#: 水平八分块，索引 0–8 对应 0/8–8/8。
HBAR = " ▏▎▍▌▋▊▉█"
#: 垂直八分块，索引 0–8。
VBAR = " ▁▂▃▄▅▆▇█"
TRACK = "░"
FULL = "█"


def _fraction(value: float, lo: float, hi: float) -> float:
    if hi <= lo:
        return 0.0
    t = (value - lo) / (hi - lo)
    return 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)


def bar(value: float, lo: float, hi: float, width: int, *, track: str = TRACK) -> str:
    """一条水平 bar，带八分之一格精度。

    ``track`` 传空串时不画底槽——排行榜那种"长度即比较"的场景不需要底槽，
    有底槽反而把每一行都拉成等长，削弱了长短对比。
    """
    if width <= 0:
        return ""
    filled = _fraction(value, lo, hi) * width
    whole = int(filled)
    remainder = round((filled - whole) * 8)
    if remainder == 8:  # 进位，否则会画出 width+1 格
        whole, remainder = whole + 1, 0
    whole = min(whole, width)
    out = FULL * whole
    if remainder and whole < width:
        out += HBAR[remainder]
    return out.ljust(width, track) if track else out


def water_level(fraction: float, height: int, width: int = 1) -> list[str]:
    """水位图：竖直的槽，从下往上填。

    和横向 bar 的区别不只是方向——**水位是"还剩多少"，bar 是"占了多少"**。
    内存、显存、上下文水位这类"有容量上限、快满了要出事"的量用竖槽更直观，
    因为人对"液面高度"的直觉比对"条长度"更强。

    返回从上到下的行。
    """
    if height <= 0 or width <= 0:
        return []
    filled = _fraction(fraction, 0.0, 1.0) * height
    whole = int(filled)
    remainder = round((filled - whole) * 8)
    if remainder == 8:
        whole, remainder = whole + 1, 0

    rows: list[str] = []
    for row in range(height):
        from_bottom = height - 1 - row
        if from_bottom < whole:
            rows.append(FULL * width)
        elif from_bottom == whole and remainder:
            rows.append(VBAR[remainder] * width)
        else:
            rows.append(TRACK * width)
    return rows


@dataclass(frozen=True)
class RankRow:
    """排行榜的一行。"""

    label: str
    value: float
    #: 右侧附注（耗时、占比），已格式化好。
    note: str = ""


def ranking(
    rows: Sequence[RankRow],
    width: int,
    *,
    top: int = 10,
    label_width: int = 14,
) -> tuple[list[tuple[RankRow, str]], int]:
    """排行榜：默认 Top10，返回 ``(行, bar)`` 与被折叠的条数。

    量程用**最大值**而不是总和——排行看的是"谁比谁长"，用总和做分母会让
    长尾场景下所有 bar 都短到看不出差别。尾部的 "N more" 由调用方渲染，
    因为它是可展开的交互元素，属于 Chrome 层。
    """
    ordered = sorted(rows, key=lambda r: r.value, reverse=True)
    shown = ordered[:top]
    peak = max((r.value for r in ordered), default=0.0)
    return [(r, bar(r.value, 0.0, peak, width, track="")) for r in shown], len(ordered) - len(shown)


def grouped(
    series: Sequence[tuple[str, Sequence[float]]],
    width: int,
    *,
    hi: float | None = None,
) -> list[tuple[str, list[str]]]:
    """多列条形图：同一个类目下并排几个系列。

    **所有系列共用一个量程**，否则并排就没有意义——并排的唯一理由就是比较。
    每个系列一行，靠色阶区分身份（分类取色），靠长度表达数值。

    返回 ``[(系列名, [每个类目的 bar])]``。
    """
    peak = hi if hi is not None else max(
        (v for _, values in series for v in values), default=1.0
    )
    return [(name, [bar(v, 0.0, peak, width, track="") for v in values])
            for name, values in series]


def before_after(before: float, after: float, width: int) -> tuple[str, str, float]:
    """Before / After 对比：两条共用量程的 bar，加变化率。

    共用量程是关键。分别归一化会让"120ms → 70ms"和"120ms → 119ms"画出
    一样的图——而这张图存在的全部意义就是让改善幅度一眼可见。
    """
    peak = max(before, after, 1e-9)
    delta = (after - before) / before if before else 0.0
    return bar(before, 0.0, peak, width, track=""), bar(after, 0.0, peak, width, track=""), delta


def segmented(parts: Sequence[float], width: int) -> list[int]:
    """分段 bar：一条表达多个量（Weights / KV Cache / Activation）。

    返回每段的格数；颜色由调用方按段的语义决定。末段吸收取整误差，
    保证总宽恰好是 ``width``——差一格在终端里是看得见的。
    """
    total = sum(parts)
    if width <= 0 or total <= 0:
        return [max(0, width)]
    out: list[int] = []
    used = 0
    for p in parts[:-1]:
        n = int(round(p / total * width))
        out.append(n)
        used += n
    out.append(max(0, width - used))
    return out


# ── 进度 ──────────────────────────────────────────────────────────────────
#: Braille spinner，只在**真实 pending** 的工具调用上转。
#: 无进度信息时的假进度条是明确禁止的（VISUAL.md §5）。
SPINNER_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"


def spinner(frame: int) -> str:
    return SPINNER_FRAMES[frame % len(SPINNER_FRAMES)]


def progress(fraction: float | None, width: int, frame: int = 0) -> str:
    """进度条。``fraction`` 为 ``None`` 表示进度未知。

    未知时**不画假进度条**——画一个跑动的窄块，让它诚实地表达"在动，但不知道
    还有多久"。给不出进度却画一条匀速涨的条，是在骗用户。
    """
    if width <= 0:
        return ""
    if fraction is None:
        head = frame % max(1, width - 2)
        return (TRACK * head + FULL * 2 + TRACK * (width - head - 2))[:width]
    return bar(fraction, 0.0, 1.0, width)


def threshold_level(value: float, warn: float = 60.0, danger: float = 85.0,
                    *, inverted: bool = False) -> str:
    """阈值判断——返回 ``devkitai.tokens.SEMANTIC`` 的键或空串。

    **它的结果只该上数值文字与前缀符号，不该上 bar**。bar 是数据，
    这个返回值是结论，两者用不同的颜色系统表达。

    ``inverted=True`` 用于"越低越糟"的指标（命中率、剩余容量）。
    """
    if inverted:
        if value <= 100 - danger:
            return "danger"
        return "warning" if value <= 100 - warn else ""
    if value >= danger:
        return "danger"
    return "warning" if value >= warn else ""
