"""图元画廊的网页版 —— 把 ``render/`` 的真实输出导成 ``pre.dense`` 标记。

    python -m tools.gallery_html > /tmp/gallery.html

**为什么不继续用 tools/screenshots.py 导出的 SVG。** 那条路子把终端截图存成
矢量 SVG，每个字符按"一个单元格"推进 x 坐标，而终端里一个汉字恰好占 2 格。
浏览器不吃这套：CJK 字形的实际步进由字体决定，和 2 倍 Latin 步进对不上，
于是中文标注一律叠在一起——``assets/tui/gallery.svg`` 上就是这个症状。

改成 ``<pre>`` 之后由浏览器自己排字，重叠消失。代价是**再也不能拿 CJK 做列
对齐**，所以这里立一条硬规矩：

    标签列一律 ASCII，中文只允许出现在行尾。

:func:`_assert_ascii_prefix` 在生成期检查这条，违反直接报错——否则等到页面上
看出歪列时，已经不知道是哪一行的锅了。

输出仍然是**程序真跑出来的**：色值来自 :func:`render.ramp.sequential`，字符
来自 ``render/`` 的各个函数，和 ``python -m devkitai gallery`` 同源。
"""

from __future__ import annotations

import html
import math
from typing import Iterable

from devkitai.render import bars, bignum, blocks, braille, plots
from devkitai.render.ramp import sequential
from devkitai.tokens import SEMANTIC

W = 30           # 图元统一宽度，便于横向对照
LABEL = 14       # 标签列（ASCII，用于列对齐）

#: 色值 → 页面 CSS 里已有的 span class。两边本来就是同一套 PTO 色阶，
#: 所以这里是一一对应而不是"取个近似"——对不上的色值会走 fallback 内联样式，
#: 那说明有人改了一边没改另一边。
CLASS_BY_HEX = {
    "#4d7209": "g8", "#86c70f": "g6", "#b3f141": "g4", "#caf57a": "g3",  # cpu   ub-green
    "#3f0675": "v8", "#6e0acd": "v6", "#9b3cf6": "v4", "#b977f9": "v3",  # npu   l0a-violet
    "#773303": "o8", "#d15905": "o6", "#fa8838": "o4", "#fbab74": "o3",  # mem   accum-orange
    "#713f12": "a8", "#ca8a04": "a6", "#f4cb22": "a4", "#fbdc59": "a3",  # io    mte-amber
    "#04d793": "ok", "#ffaa3b": "wn", "#ff4b7b": "er",                   # 语义色
    "#737373": "cm",                                                      # muted
    "#a2a2a2": "s2",                                                      # secondary
}

MUTED = "#737373"
SECONDARY = "#a2a2a2"


# ── 行的搭建 ──────────────────────────────────────────────────────────────
#: 行距档位。哪一档不看字形范围，看**语义**——行与行之间是「并列」还是
#: 「同一张图的上下半」：
#:
#:   chart 24px  一行 = 一条独立数据。热力网格的一行是一组核、Trace 的一行是
#:               一条泳道、Metric Bar 的一行是一个指标。块字形贴着 em 盒画满，
#:               不拉开就粘成一块。
#:   tight 16px  多行拼成**一张**图。braille 曲线的三行是同一条曲线被切成三段，
#:               像素数字的五行是同一个字。拉开就断了——终端里这类图的行距恰好
#:               等于字形高度，网页上得把这份连续性还回去。
CHART, TIGHT = "chart", "tight"


class Row:
    """一行 = 若干 ``(文本, 色值)`` 片段。色值 ``None`` 表示走 pre 的默认前景。"""

    def __init__(self, density: str | None = CHART) -> None:
        self.parts: list[tuple[str, str | None]] = []
        #: 行距档位；``None`` = 空行，跟随相邻块。
        self.density = density
        #: 从第几段起不再参与列对齐。``None`` = 只豁免最后一段。
        self.free_from: int | None = None

    def free(self) -> "Row":
        """声明「本行从这里往后不参与跨行对齐」，宽度不定的字符就此放行。

        用在 Before/After 这种行上：中间那个 ``→`` 是 Ambiguous 宽度，可它后面
        的东西**不需要和别的行对齐**，顶歪了也看不出来。显式声明比放宽规则好——
        规则一旦放宽，下次真顶歪了就没人拦得住。
        """
        self.free_from = len(self.parts)
        return self

    def add(self, text: str, color: str | None = None) -> "Row":
        if text:
            self.parts.append((text, color))
        return self

    def label(self, text: str) -> "Row":
        """标签列。**必须 ASCII**——它承担列对齐，CJK 在浏览器里对不齐。"""
        _assert_ascii_prefix(text)
        return self.add(text.ljust(LABEL), SECONDARY if text.strip() else None)

    def tail(self, text: str, color: str | None = MUTED) -> "Row":
        """行尾注释。这里允许中文，因为后面没有需要对齐的东西了。"""
        return self.add("  " + text, color)

    @property
    def plain(self) -> str:
        return "".join(t for t, _ in self.parts)


#: 允许出现在对齐列里的非 ASCII 字符：框线 / 块元素（U+2500–U+259F）与
#: 点阵（U+2800–U+28FF）。页面的等宽字体把这两段渲染成单宽，所以它们参与
#: 列对齐是安全的。**其余非 ASCII 一律不行**——汉字是双宽，而箭头 ↑↓ 这类
#: 是 East-Asian Ambiguous，在 CJK 字体下也会变双宽。
_DRAWING = ((0x2500, 0x259F), (0x2800, 0x28FF))


def _safe_for_columns(text: str) -> bool:
    return all(
        ch.isascii() or any(lo <= ord(ch) <= hi for lo, hi in _DRAWING)
        for ch in text
    )


def _assert_ascii_prefix(text: str) -> None:
    if not text.isascii():
        raise ValueError(
            f"标签列出现非 ASCII 字符 {text!r}——浏览器里 CJK 步进和终端的 2 格宽"
            f"对不上，拿它做列对齐就会歪（gallery.svg 上的原始 bug）。"
            f"请把中文挪到行尾的 tail() 里。"
        )


def _assert_alignment_safe(row: "Row") -> None:
    """一行里除**最后一段**外都得是列安全的字符。

    最后一段随便写——它后面没有需要对齐的东西了。这条不变式是这次从 SVG 换成
    ``<pre>`` 的全部代价所在：``ljust`` 数的是**码位**，浏览器排的是**字形宽度**，
    ``"1 帧过窄未显示".ljust(30)`` 补出来的是 30 个码位、约 36 格的宽度，
    后面的注释就顶歪了。这类 bug 只在中文下出现，纯英文界面上怎么看都是对的。
    """
    cut = row.free_from if row.free_from is not None else len(row.parts) - 1
    for text, _ in row.parts[:cut]:
        if not _safe_for_columns(text):
            bad = [c for c in text if not _safe_for_columns(c)]
            raise ValueError(
                f"对齐列里出现了宽度不定的字符 {bad!r}（整段：{text!r}）。"
                f"ljust 按码位补白，浏览器按字形宽度排字，两者对不上就会顶歪后面的列。"
                f"把它挪到本行最后一段去。"
            )


def _merge(parts: Iterable[tuple[str, str | None]]) -> list[tuple[str, str | None]]:
    """合并相邻同色片段——不合并的话 64 核热力网格会展开成 64 个 span。"""
    out: list[tuple[str, str | None]] = []
    for text, color in parts:
        if out and out[-1][1] == color:
            out[-1] = (out[-1][0] + text, color)
        else:
            out.append((text, color))
    return out


def render_rows(rows: Iterable[Row]) -> str:
    lines = []
    for row in rows:
        _assert_alignment_safe(row)
        buf = []
        for text, color in _merge(row.parts):
            esc = html.escape(text, quote=False)
            if color is None:
                buf.append(esc)
                continue
            cls = CLASS_BY_HEX.get(color.lower())
            if cls:
                buf.append(f'<span class="{cls}">{esc}</span>')
            else:  # 两边的色阶脱钩了，先保证页面对，但别静默
                buf.append(f'<span style="color:{color}">{esc}</span>')
        lines.append("".join(buf))
    return "\n".join(lines)


def _sample() -> list[float]:
    """确定性假数据——用 random 的话每次重绘都在抖，看不出是组件在动。"""
    return [50 + 42 * math.sin(i / 9) + 6 * math.sin(i / 2.3) for i in range(120)]


# ── 六个分组 ──────────────────────────────────────────────────────────────
def compare() -> list[Row]:
    """比大小：条形 · 排行 · 多列 · Before/After。"""
    rows = []
    for value in (28.0, 72.0, 91.0):
        level = bars.threshold_level(value)
        r = Row().label("Metric Bar")
        r.add(bars.bar(value, 0, 100, W), sequential(value, 0, 100, "cpu"))
        r.add(f"  {value:5.1f}%", SEMANTIC[level] if level else None)
        if level:
            r.tail("← 数值转语义色，bar 不变")
        rows.append(r)

    rows.append(Row(None))
    ranked = [
        bars.RankRow("attention_fwd", 18.6, ""), bars.RankRow("matmul_4096", 6.3, ""),
        bars.RankRow("layernorm", 3.7, ""), bars.RankRow("softmax", 2.1, ""),
        bars.RankRow("gelu", 1.6, ""),
    ]
    shown, more = bars.ranking(ranked, W, top=3)
    for i, (row, drawn) in enumerate(shown):
        r = Row().label("Ranking" if i == 0 else "")
        r.add(drawn.ljust(W), sequential(row.value, 0, shown[0][0].value, "npu"))
        r.add(f"  {row.value:5.1f}s")
        r.tail(row.label)
        rows.append(r)
    rows.append(Row().label("").add(f"… {more} more", MUTED))

    rows.append(Row(None))
    for name, series in bars.grouped(
        [("baseline", [42, 18, 62]), ("scheme A", [61, 12, 78]), ("scheme B", [55, 9, 88])], 8
    ):
        r = Row().label("Grouped" if name == "baseline" else "")
        for i, drawn in enumerate(series):
            r.add(drawn.ljust(9), sequential(len(drawn), 0, 8, ("cpu", "npu", "memory")[i]))
        r.tail(name)
        rows.append(r)
    rows.append(Row().label("").add("QPS      P99      CPU", MUTED))

    rows.append(Row(None))
    before, after, delta = bars.before_after(120, 70, 12)
    r = Row().label("Before/After")
    r.add(before, sequential(120, 0, 120, "memory"))
    r.free()  # 往后只剩这一行自己的内容，不和别的行对齐
    r.add("  →  ", MUTED)
    r.add(after, sequential(70, 0, 120, "memory"))
    r.add("   120ms → 70ms ")
    r.add(f"({delta:+.0%})", SEMANTIC["success"])
    rows.append(r)
    return rows


def trend() -> list[Row]:
    """看趋势：折线 · 面积 · Sparkline · 双向。"""
    rows, data = [], _sample()
    curve = braille.plot_series(data, W, 3, lo=0, hi=100)
    for i, line in enumerate(curve.rows_text()):
        rows.append(Row(TIGHT).label("Line  T2" if i == 0 else "")
                    .add(line, sequential(data[-1], 0, 100, "cpu")))

    rows.append(Row(None))
    area = braille.plot_series(data, W, 2, lo=0, hi=100, area=True)
    for i, line in enumerate(area.rows_text()):
        rows.append(Row(TIGHT).label("Area  T2" if i == 0 else "")
                    .add(line, sequential(60, 0, 100, "npu")))

    rows.append(Row(None))
    rows.append(Row().label("Sparkline T1")
                .add(blocks.sparkline(data, W, lo=0, hi=100),
                     sequential(data[-1], 0, 100, "cpu"))
                .tail("← T2 掉下来就是它"))

    rows.append(Row(None))
    up = [40 + 30 * math.sin(i / 7) for i in range(60)]
    down = [20 + 15 * math.sin(i / 5 + 1) for i in range(60)]
    top, bottom = braille.mirrored(up, down, W, 1)
    # 箭头 ↑↓ 是 East-Asian Ambiguous 宽度，在 CJK 字体下会渲染成双宽——
    # 放进标签列会把整列顶歪。标签列只留 ASCII，方向标记挪到行尾。
    rows.append(Row(TIGHT).label("Mirrored up").add(top.rows_text()[0],
                sequential(70, 0, 100, "io")).tail("↑ 1.30 KiB/s"))
    rows.append(Row(TIGHT).label("      down").add(bottom.rows_text()[0],
                sequential(30, 0, 100, "io")).tail("↓ 346 B/s"))
    return rows


def locate() -> list[Row]:
    """找位置：散点 · 火焰图 · 泳道。"""
    rows = []
    points = [(i / 40, 0.3 + 0.6 * math.sin(i / 9) ** 2) for i in range(40)]
    sc = plots.scatter(points, W, 3, x=plots.Axis(0, 1), y=plots.Axis(0, 1))
    for i, line in enumerate(sc.rows_text()):
        r = Row(TIGHT).label("Scatter" if i == 0 else "").add(line, sequential(50, 0, 100, "npu"))
        if i == 0:
            r.tail("Roofline")
        rows.append(r)

    rows.append(Row(None))
    frames = [
        plots.Frame("main", 100, 0, 0), plots.Frame("ngx_http_process", 62, 1, 0),
        plots.Frame("ssl_handshake", 38, 1, 62), plots.Frame("crypto_aes", 30, 2, 0),
        plots.Frame("memcpy", 22, 2, 62), plots.Frame("tiny_leaf", 0.3, 3, 0),
    ]
    domains = ("cpu", "npu", "memory", "io")
    for depth, row in enumerate(plots.flame(frames, W)):
        r = Row().label("Flame" if depth == 0 else "")
        cursor = 0
        for frame, start, cells in row:
            r.add(" " * max(0, start - cursor))
            r.add("█" * cells, sequential(frame.value, 0, 100, domains[depth % 4]))
            cursor = start + cells
        r.add(" " * max(0, W - cursor))
        r.tail(row[0][0].name if row else "")
        rows.append(r)
    dropped = plots.dropped_frames(frames, W)
    if dropped:
        # 提示文字整段挪到行尾：ljust 会按码位给中文补白，补出来的宽度不对。
        rows.append(Row().label("").add(" " * W).free()
                    .add(f"  {dropped} 帧过窄未显示", SEMANTIC["warning"])
                    .tail("← 必须显式说，否则「看全了」是错觉"))

    rows.append(Row(None))
    spans = [plots.Span("CPU", 0, 30), plots.Span("CPU", 55, 70),
             plots.Span("NPU", 25, 80), plots.Span("HBM", 10, 95)]
    for lane, cells in plots.timeline(spans, W):
        r = Row().label(f"Timeline {lane}")
        cursor = 0
        domain = {"CPU": "cpu", "NPU": "npu", "HBM": "memory"}[lane]
        for _, start, cells_w in cells:
            r.add(" " * max(0, start - cursor))
            r.add("█" * cells_w, sequential(70, 0, 100, domain))
            cursor = start + cells_w
        rows.append(r)
    return rows


def headroom() -> list[Row]:
    """看余量：水位 · 进度 · 分段。"""
    rows = []
    for i, line in enumerate(bars.water_level(0.62, 5, width=3)):
        r = Row(TIGHT).label("Water" if i == 0 else "")
        r.add(line.ljust(W), sequential(62, 0, 100, "memory"))
        if i == 0:
            r.tail("38.2 / 64 GiB")
        rows.append(r)

    rows.append(Row(None))
    for label, frac, frame in (("Progress", 0.68, 0), ("Progress ?", None, 3)):
        r = Row().label(label)
        r.add(bars.progress(frac, W, frame), sequential(68 if frac else 40, 0, 100, "cpu"))
        r.tail("68%" if frac else f"{bars.spinner(frame)} 采集中 · 不画假进度条")
        rows.append(r)

    rows.append(Row(None))
    r = Row().label("Segmented")
    for i, cells in enumerate(bars.segmented([22, 12, 4, 26], W)):
        r.add("█" * cells, sequential((i + 1) * 25, 0, 100, "memory"))
    r.tail("used 22G  cached 12G  kv 4G  free 26G")
    rows.append(r)
    return rows


def single_value() -> list[Row]:
    """读单值：像素数字 · 数图。"""
    rows = []
    for i, line in enumerate(bignum.big("61.2")):
        r = Row(TIGHT).label("Bignum" if i == 0 else "").add(line.ljust(W))
        if i == 2:
            r.tail("k QPS")
        rows.append(r)

    rows.append(Row(None))
    stats = [
        bignum.Stat("QPS", 61.2, "k", delta=0.45, history=_sample()[-24:]),
        bignum.Stat("P99", 12.0, "ms", delta=-0.33, history=_sample()[-24:],
                    higher_is_better=False),
        bignum.Stat("Memory", 38.2, "GiB", capacity=64.0),
    ]
    for i, stat in enumerate(stats):
        r = Row().label("Stat" if i == 0 else "")
        r.add(f"{stat.value_text():>6}{stat.unit:<4}")
        if stat.delta is not None:
            r.add(f"{stat.delta_text():>7} ",
                  SEMANTIC["success"] if stat.improved else SEMANTIC["danger"])
        else:
            r.add(" " * 8)
        if stat.capacity:
            r.add(stat.capacity_bar(14), sequential(stat.value, 0, stat.capacity, "memory"))
        else:
            r.add(stat.spark(14), sequential(60, 0, 100, "cpu"))
        r.tail(stat.label)
        rows.append(r)
    return rows


def distribution() -> list[Row]:
    """看分布：热力。"""
    rows = []
    for start in range(0, 64, 16):
        r = Row().label(f"{start}-{start + 15}")
        for core in range(start, start + 16):
            value = abs(50 + 45 * math.sin(core / 5.5)) % 100
            r.add("█", sequential(value, 0, 100, "cpu"))
        rows.append(r)
    r = Row().label("T1 fallback")
    for core in range(16):
        value = abs(50 + 45 * math.sin(core / 5.5)) % 100
        r.add(blocks.heat_glyph(value, 0, 100), SECONDARY)
    r.tail("颜色没了，强度由字形接住")
    rows.append(r)
    return rows


#: (组名, 问题, 渲染层徽章, 降级链, 这一组的规矩, 构造函数)
GROUPS = (
    ("比大小", "谁比谁大", "T1", "T1 块字符 → T0 数值",
     "bar 走<b>域色阶</b>（它是数据），阈值判断只上<b>数值文字</b>（它是结论）——"
     "一个 90% 的利用率本身不是错误。", compare),
    ("看趋势", "怎么走的", "T2", "T2 Braille → T1 Sparkline → T0 当前值 + 峰值",
     "多系列<b>共用量程</b>，否则并置就没有意义：分别归一化会让每条都填满画布，"
     "而并置的全部意义就是比较。", trend),
    ("找位置", "在哪儿 / 谁在等谁", "T2", "T2 Braille / T1 块字符",
     "火焰图里过窄的帧<b>宁可不画，也不虚胖</b>，并把丢掉的条数显式标出来——"
     "悄悄丢掉会让「我看全了」变成错觉。", locate),
    ("看余量", "还剩多少", "T1", "T1 块字符 → T0 百分比",
     "水位是「还剩多少」，bar 是「占了多少」——不是同一个问题，所以一个竖一个横。"
     "给不出进度就<b>不画进度条</b>。", headroom),
    ("读单值", "现在多少", "T1", "T1 块字符 → T0 常规数字",
     "像素字<b>仅用于数字</b>，正文永不像素化。数图上 delta 是唯一该出现语义色的地方。",
     single_value),
    ("看分布", "热点在哪", "T3", "T3 真彩 → T1 灰阶 + ░▒▓█",
     "<b>颜色承载数值，位置承载拓扑</b>。掉到 T1 时颜色没了，强度由字形 <code>░▒▓█</code> 接住。",
     distribution),
)


def chunk(rows: list[Row]) -> list[tuple[str, list[Row]]]:
    """把一组行按行距档位切成连续块，每块出一个 ``<pre>``。

    切开是必须的：``line-height`` 作用在整个 ``<pre>`` 上，而"看趋势"这一组里
    braille 曲线要紧、Sparkline 要松，同一个 ``<pre>`` 装不下两种行距。
    密度为 ``None`` 的空行落在边界上就丢掉——两个 ``<pre>`` 之间本来就有间距。
    """
    out: list[tuple[str, list[Row]]] = []
    pending: list[Row] = []          # 尚未归属的空行
    for row in rows:
        if row.density is None:
            pending.append(row)
            continue
        if out and out[-1][0] == row.density:
            out[-1][1].extend(pending)   # 块内的空行留着，它是图元之间的分隔
        pending = []
        if out and out[-1][0] == row.density:
            out[-1][1].append(row)
        else:
            out.append((row.density, [row]))
    return out


def main() -> None:
    for title, question, tier, chain, rule, build in GROUPS:
        print(f'<h3>{title} <span class="badge p">{tier}</span> '
              f'<span class="chipm">{question}</span></h3>')
        for density, rows in chunk(build()):
            print(f'<pre class="dense {density}">{render_rows(rows)}</pre>')
        print(f'<p class="rule"><b>降级链：</b><code>{chain}</code>。{rule}</p>')


if __name__ == "__main__":
    main()
