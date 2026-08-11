"""图元画廊 —— 设计系统里"图表原语"那一节的活样本。

    python -m devkitai gallery

规范里写着每种图长什么样，但字符图最终好不好使，只有渲染出来才知道。
这一页把 ``docs/COMPONENT.md`` §3 的全部图元排在一起，附上每种图的
**渲染层 · 降级形态 · 用色规则**，评审时对着看。

排序不是按字母，是按"回答什么问题"分组：

    比大小   条形 · 排行 · 多列 · Before/After
    看趋势   折线 · 面积 · Sparkline · 双向
    找位置   散点 · 火焰图 · 泳道
    看余量   水位 · 进度 · 分段
    读单值   像素数字 · 数图
    看分布   热力
"""

from __future__ import annotations

import math

from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from .render import bars, bignum, blocks, braille, plots
from rich.cells import cell_len

from .render.text import fit
from .render.ramp import sequential
from .theme import pto_theme, pto_variables
from .tokens import ACCENT, SEMANTIC, SURFACE_1, foreground

W = 30  # 图元统一宽度，便于横向对照

_MUTED = foreground(SURFACE_1, "muted")
_FG = foreground(SURFACE_1, "fg")
_SEC = foreground(SURFACE_1, "secondary")


# ── 版面：固定列网格 ────────────────────────────────────────────────────
# 第一版把注释直接追加在图形后面，而图形宽度是不固定的（bar 长短随数值变、
# Braille 行满宽、火焰图带前导空格），于是注释落在参差不齐的 x 上，撞进
# 隔壁内容里——看着就是"挤"。
#
# 借 GUI 图标库的排法：**列位置固定，内容再短也不前移**。宁可留白，
# 也不让同一类信息在不同行出现在不同位置——眼睛扫一列比追一行省力得多。
#
# 列宽只取 VISUAL.md §3 的六档间距（这里用到 space-2 / space-4 / space-6），
# 代码里不出现裸数字缩进。
COL_LABEL = 16   # 标签列
COL_BODY = 36    # 图形列：W=30 + 左右各 space-5 的留白
GUTTER = 3       # space-5：列间距——舒展优先于塞满


def _pad_text(body: Text, width: int) -> Text:
    """把带样式的 Text 补到固定单元格宽——按 cell 算，不是按字符数。"""
    out = Text()
    out.append_text(body)
    missing = width - cell_len(body.plain)
    if missing > 0:
        out.append(" " * missing)
    return out


def _heading(title: str, tier: str, rule: str) -> Text:
    """组标题：上方 space-6（2 空行）拉开，下方点阵分隔线收口。

    分隔线用方点而非实线——比实线轻、比留白明确（VISUAL.md 里 AwesomeTUI
    那条"点阵分隔线"）。组与组之间必须看得出断点，否则十四种图元连成一片。
    """
    out = Text()
    out.append("\n\n")                                    # space-6
    out.append(f"{' '.join(title)}\n", style=f"{_MUTED} bold")
    out.append(f"{' ' * GUTTER}{tier}\n", style=ACCENT)
    out.append(f"{' ' * GUTTER}{rule}\n", style=_MUTED)
    out.append(f"{'·' * (COL_LABEL + COL_BODY + 24)}\n", style="#3a3a3a")
    return out


def _row(label: str, body: Text | str, note: str = "") -> Text:
    """一行：标签列 | 图形列 | 注释列，三列都定死起点。"""
    out = Text()
    # fit 而不是 f"{label:<12}"——中文标签按字符数补空格会让整列歪掉
    out.append(fit(label, COL_LABEL), style=_SEC)
    out.append_text(_pad_text(body if isinstance(body, Text) else Text(body, style=_FG),
                              COL_BODY))
    if note:
        out.append(" " * GUTTER + note, style=_MUTED)
    out.append("\n")
    return out


def _gap() -> Text:
    """同组内两个图元之间留一行——space-4 的纵向档位。"""
    return Text("\n")


def _sample() -> list[float]:
    """确定性假数据——用 random 的话每次重绘图都在抖，看不出是组件在动。"""
    return [50 + 42 * math.sin(i / 9) + 6 * math.sin(i / 2.3) for i in range(120)]


def _compare() -> Text:
    """比大小：条形 · 排行 · 多列 · Before/After。"""
    out = _heading("比大小", "T1 块字符 → T0 数值",
                   "bar 走域色阶（数据）；阈值判断只上数值文字（结论）")

    for value in (28.0, 72.0, 91.0):
        level = bars.threshold_level(value)
        line = Text()
        line.append(bars.bar(value, 0, 100, W), style=sequential(value, 0, 100, "cpu"))
        line.append(f"  {value:5.1f}%",
                    style=SEMANTIC[level] if level else _FG)
        out.append_text(_row("Metric Bar", line,
                             "← 数值转语义色，bar 不变" if level else ""))

    rows = [
        bars.RankRow("attention_fwd", 18.6, "1024 calls"),
        bars.RankRow("matmul_4096", 6.3, "512 calls"),
        bars.RankRow("layernorm", 3.7, "2048 calls"),
        bars.RankRow("softmax", 2.1, "1024 calls"),
        bars.RankRow("gelu", 1.6, "4096 calls"),
    ]
    out.append_text(_gap())
    shown, more = bars.ranking(rows, W, top=3)
    for rank, (row, drawn) in enumerate(shown):
        line = Text()
        line.append(drawn, style=sequential(row.value, 0, shown[0][0].value, "npu"))
        line.append(f"  {row.value:.1f}s", style=_FG)
        out.append_text(_row("排行" if rank == 0 else "", line, row.label))
    out.append_text(_row("", Text(f"… {more} more", style=_MUTED)))

    out.append_text(_gap())
    for name, series in bars.grouped(
        [("baseline", [42, 18, 62]), ("方案 A", [61, 12, 78]), ("方案 B", [55, 9, 88])], 8
    ):
        line = Text()
        for i, drawn in enumerate(series):
            line.append(drawn.ljust(9), style=sequential(len(drawn), 0, 8,
                                                        ("cpu", "npu", "memory")[i]))
        out.append_text(_row("多列", line, name))
    out.append_text(_row("", Text("QPS       P99       CPU", style=_MUTED)))

    out.append_text(_gap())
    before, after, delta = bars.before_after(120, 70, 12)
    line = Text()
    line.append(before, style=sequential(120, 0, 120, "memory"))
    line.append("  →  ", style=_MUTED)
    line.append(after, style=sequential(70, 0, 120, "memory"))
    line.append(f"   120ms → 70ms ", style=_FG)
    line.append(f"({delta:+.0%})", style=SEMANTIC["success"])
    out.append_text(_row("Before/After", line))
    return out


def _trend() -> Text:
    """看趋势：折线 · 面积 · Sparkline · 双向。"""
    out = _heading("看趋势", "T2 Braille → T1 Sparkline → T0 当前值 + 峰值",
                   "多系列共用量程，否则并置就没有意义")
    data = _sample()

    curve = braille.plot_series(data, W, 3, lo=0, hi=100)
    for i, line in enumerate(curve.rows_text()):
        out.append_text(_row("折线 T2" if i == 0 else "",
                             Text(line, style=sequential(data[-1], 0, 100, "cpu"))))

    out.append_text(_gap())
    area = braille.plot_series(data, W, 2, lo=0, hi=100, area=True)
    for i, line in enumerate(area.rows_text()):
        out.append_text(_row("面积" if i == 0 else "",
                             Text(line, style=sequential(60, 0, 100, "npu"))))

    out.append_text(_gap())
    out.append_text(_row("Sparkline T1",
                         Text(blocks.sparkline(data, W, lo=0, hi=100),
                              style=sequential(data[-1], 0, 100, "cpu")),
                         "← T2 掉下来就是它"))

    out.append_text(_gap())
    up = [40 + 30 * math.sin(i / 7) for i in range(60)]
    down = [20 + 15 * math.sin(i / 5 + 1) for i in range(60)]
    top, bottom = braille.mirrored(up, down, W, 1)
    out.append_text(_row("双向 ↑", Text(top.rows_text()[0], style=sequential(70, 0, 100, "io")),
                         "1.30 KiB/s"))
    out.append_text(_row("     ↓", Text(bottom.rows_text()[0], style=sequential(30, 0, 100, "io")),
                         "346 B/s"))
    return out


def _locate() -> Text:
    """找位置：散点 · 火焰图 · 泳道。"""
    out = _heading("找位置", "T2 Braille / T1 块字符",
                   "火焰图里过窄的帧宁可不画，也不虚胖")

    points = [(i / 40, 0.3 + 0.6 * math.sin(i / 9) ** 2) for i in range(40)]
    sc = plots.scatter(points, W, 3, x=plots.Axis(0, 1), y=plots.Axis(0, 1))
    for i, line in enumerate(sc.rows_text()):
        out.append_text(_row("散点" if i == 0 else "",
                             Text(line, style=sequential(50, 0, 100, "npu")),
                             "Roofline" if i == 0 else ""))

    out.append_text(_gap())
    frames = [
        plots.Frame("main", 100, 0, 0),
        plots.Frame("ngx_http_process", 62, 1, 0),
        plots.Frame("ssl_handshake", 38, 1, 62),
        plots.Frame("crypto_aes", 30, 2, 0),
        plots.Frame("memcpy", 22, 2, 62),
        plots.Frame("tiny_leaf", 0.3, 3, 0),
    ]
    domains = ("cpu", "npu", "memory", "io")
    for depth, row in enumerate(plots.flame(frames, W)):
        line = Text(" " * W)
        rendered = Text()
        cursor = 0
        for frame, start, cells in row:
            rendered.append(" " * max(0, start - cursor))
            rendered.append("█" * cells,
                            style=sequential(frame.value, 0, 100, domains[depth % 4]))
            cursor = start + cells
        rendered.append(" " * max(0, W - cursor))
        out.append_text(_row("火焰图" if depth == 0 else "", rendered,
                             row[0][0].name if row else ""))
    dropped = plots.dropped_frames(frames, W)
    if dropped:
        out.append_text(_row("", Text(f"{dropped} 帧过窄未显示", style=SEMANTIC["warning"]),
                             "← 必须显式说，否则「看全了」是错觉"))

    out.append_text(_gap())
    spans = [
        plots.Span("CPU", 0, 30), plots.Span("CPU", 55, 70),
        plots.Span("NPU", 25, 80),
        plots.Span("HBM", 10, 95),
    ]
    for lane, cells in plots.timeline(spans, W):
        line = Text()
        cursor = 0
        domain = {"CPU": "cpu", "NPU": "npu", "HBM": "memory"}[lane]
        for _, start, cells_w in cells:
            line.append(" " * max(0, start - cursor))
            line.append("█" * cells_w, style=sequential(70, 0, 100, domain))
            cursor = start + cells_w
        out.append_text(_row(f"泳道 {lane}", line))
    return out


def _headroom() -> Text:
    """看余量：水位 · 进度 · 分段。"""
    out = _heading("看余量", "T1 块字符 → T0 百分比",
                   "水位是「还剩多少」，bar 是「占了多少」——不是同一个问题")

    tank = bars.water_level(0.62, 5, width=3)
    for i, line in enumerate(tank):
        body = Text(line, style=sequential(62, 0, 100, "memory"))
        out.append_text(_row("水位" if i == 0 else "", body,
                             "38.2 / 64 GiB" if i == 0 else ""))

    for label, frac, frame in (("进度 已知", 0.68, 0), ("进度 未知", None, 3)):
        line = Text(bars.progress(frac, W, frame),
                    style=sequential(68 if frac else 40, 0, 100, "cpu"))
        note = "68%" if frac else f"{bars.spinner(frame)} 采集中 · 不画假进度条"
        out.append_text(_row(label, line, note))

    parts = [22, 12, 4, 26]
    line = Text()
    for i, cells in enumerate(bars.segmented(parts, W)):
        line.append("█" * cells, style=sequential((i + 1) * 25, 0, 100, "memory"))
    out.append_text(_row("分段", line, "used 22G  cached 12G  kv 4G  free 26G"))
    return out


def _single_value() -> Text:
    """读单值：像素数字 · 数图。"""
    out = _heading("读单值", "T1 块字符 → T0 常规数字",
                   "像素字仅用于数字，正文永不像素化")

    for i, line in enumerate(bignum.big("61.2")):
        out.append_text(_row("像素数字" if i == 0 else "", Text(line, style=_FG),
                             "k QPS" if i == 2 else ""))

    stats = [
        bignum.Stat("QPS", 61.2, "k", delta=0.45, history=_sample()[-24:]),
        bignum.Stat("P99", 12.0, "ms", delta=-0.33, history=_sample()[-24:],
                    higher_is_better=False),
        bignum.Stat("内存", 38.2, "GiB", capacity=64.0),
    ]
    for stat in stats:
        line = Text()
        line.append(f"{stat.value_text():>6}{stat.unit:<4}", style=_FG)
        if stat.delta is not None:
            improved = stat.improved
            line.append(f"{stat.delta_text():>7} ",
                        style=SEMANTIC["success"] if improved else SEMANTIC["danger"])
        else:
            line.append(" " * 8)
        if stat.capacity:
            line.append(stat.capacity_bar(14),
                        style=sequential(stat.value, 0, stat.capacity, "memory"))
        else:
            line.append(stat.spark(14), style=sequential(60, 0, 100, "cpu"))
        out.append_text(_row("数图", line, stat.label))
    return out


def _distribution() -> Text:
    """看分布：热力。"""
    out = _heading("看分布", "T3 真彩 → T1 灰阶 + ░▒▓█",
                   "颜色承载数值，位置承载拓扑")
    for start in range(0, 64, 16):
        line = Text()
        for core in range(start, start + 16):
            value = abs(50 + 45 * math.sin(core / 5.5)) % 100
            line.append("█", style=sequential(value, 0, 100, "cpu"))
        out.append_text(_row(f"{start}-{start + 15}", line))
    line = Text()
    for core in range(16):
        value = abs(50 + 45 * math.sin(core / 5.5)) % 100
        line.append(blocks.heat_glyph(value, 0, 100), style=_SEC)
    out.append_text(_row("T1 降级", line, "颜色没了，强度由字形接住"))
    return out


class GalleryApp(App):
    """图元画廊。"""

    CSS_PATH = "theme/pto.tcss"
    TITLE = "Kunpeng DevKit AI · 图表原语"
    BINDINGS = [("q", "quit", "退出")]

    def get_theme_variable_defaults(self) -> dict[str, str]:
        return pto_variables()

    def compose(self) -> ComposeResult:
        body = Text()
        for section in (_compare, _trend, _locate, _headroom, _single_value, _distribution):
            body.append_text(section())
        with VerticalScroll(id="gallery"):
            yield Static(body)

    def on_mount(self) -> None:
        self.register_theme(pto_theme())
        self.theme = "pto"


def main() -> None:
    GalleryApp().run()
