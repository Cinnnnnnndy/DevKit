"""三条硬约束的失真对比图 —— docs 网页「图元尺寸与排布」用。

    python -m tools.constraint_diagram

那一节的"三条硬约束"原来只有文字：散点比例锁死 2.0、水位比例上界 0.8、
双向面积行数必为偶数。文字说得清道理，但**看不出失真长什么样**——而这三条
恰恰都是"看一眼就懂，说十句都绕"的那类。这里用真实的 ``render/`` 函数各生成
一组"正确 vs 越界"的对照，不是手画的示意图。
"""

from __future__ import annotations

import math

from devkitai.render import bars, braille, plots
from devkitai.render.ramp import sequential

from .gallery_html import Row, render_rows


# ── ① 散点：比例锁死 2.0，拉宽就把斜率画错 ──────────────────────────────
def _scatter_pair() -> list[Row]:
    # Roofline 形状的知识点云：compute-bound 平台 + memory-bound 斜坡，
    # 斜率是唯一的结论——拉宽图会让斜坡看起来更缓，读出"没那么 memory-bound"。
    points = [(i / 60, min(0.85, 0.15 + i / 60 * 1.6)) for i in range(60)]
    correct = plots.scatter(points, 16, 8, x=plots.Axis(0, 1), y=plots.Axis(0, 1))
    distorted = plots.scatter(points, 32, 8, x=plots.Axis(0, 1), y=plots.Axis(0, 1))

    rows = []
    c_lines, d_lines = correct.rows_text(), distorted.rows_text()
    for i in range(8):
        r = Row().label("16x8 ok" if i == 0 else "")
        r.add(c_lines[i], sequential(50, 0, 100, "npu"))
        r.add("  32x8 too-wide  " if i == 0 else "                 ")
        r.add(d_lines[i], sequential(50, 0, 100, "memory"))
        if i == 0:
            r.tail("← 同一份知识点，拉宽后斜率读起来更缓")
        rows.append(r)
    return rows


# ── ② 水位：比例上界 0.8，扁了就读成横向 bar ────────────────────────────
def _water_pair() -> list[Row]:
    fraction = 0.62
    correct = bars.water_level(fraction, 8, width=3)   # 3x8 = 0.375，在带内
    # 越界演示：同样的占比横着摊开，读起来变成了"占了多少"的 bar，
    # 而不是"还剩多少"的水位——这正是比例上界要防的那种误读。
    flat = bars.bar(fraction, 0.0, 1.0, 24)

    rows = []
    for i, line in enumerate(correct):
        r = Row().label("3x8 ok" if i == 0 else "")
        r.add(line, sequential(62, 0, 100, "memory"))
        if i == 0:
            r.tail("38.2 / 64 GiB —— 竖着读「还剩多少」")
        rows.append(r)
    rows.append(Row(None))
    r = Row().label("24x1 over")
    r.add(flat, sequential(62, 0, 100, "memory"))
    r.tail("同一个 62%，横着摊开就读成了「占了多少」——比例越界，问题都读错了")
    rows.append(r)
    return rows


# ── ③ 双向面积：行数必为偶数，奇数劈不开上下两半 ────────────────────────
def _mirrored_pair() -> list[Row]:
    up = [40 + 30 * math.sin(i / 7) for i in range(60)]
    down = [20 + 15 * math.sin(i / 5 + 1) for i in range(60)]
    peak = max([*up, *down])

    rows = []
    top, bottom = braille.mirrored(up, down, 30, 2, hi=peak)
    for i, line in enumerate(top.rows_text()):
        r = Row().label("4 rows ok" if i == 0 else "")
        r.add(line, sequential(70, 0, 100, "io"))
        if i == 0:
            r.tail("↑ 1.30 KiB/s")
        rows.append(r)
    for i, line in enumerate(bottom.rows_text()):
        r = Row().label("")
        r.add(line, sequential(30, 0, 100, "io"))
        if i == 0:
            r.tail("↓ 346 B/s —— 上下等高，一眼看出「发得比收得多」")
        rows.append(r)

    rows.append(Row(None))
    # 越界演示：故意不经过 mirrored()，直接给上下两半不同的行数——
    # 这正是"行数必须是它的整数倍"这条约束想拦住的误用。
    bad_top = braille.plot_series(up, 30, 3, lo=0.0, hi=peak, area=True)
    bad_bottom = braille.plot_series(down, 30, 1, lo=0.0, hi=peak, area=True, invert=True)
    for i, line in enumerate(bad_top.rows_text()):
        r = Row().label("3+1 over" if i == 0 else "")
        r.add(line, sequential(70, 0, 100, "io"))
        rows.append(r)
    for i, line in enumerate(bad_bottom.rows_text()):
        r = Row().label("")
        r.add(line, sequential(30, 0, 100, "io"))
        if i == 0:
            r.tail("上下不等高——「谁更高」变成了格子数的巧合，不再是数据本身")
        rows.append(r)
    return rows


GROUPS = (
    ("① 散点比例锁死 2.0", _scatter_pair),
    ("② 水位比例上界 0.8", _water_pair),
    ("③ 双向面积行数必为偶数", _mirrored_pair),
)


def main() -> None:
    for title, build in GROUPS:
        rows = build()
        density = "tight"
        print(f'<pre class="dense {density}" aria-label="{title}">'
              f'{render_rows(rows)}</pre>')


if __name__ == "__main__":
    main()
