"""折叠降级链（``docs/FRAMEWORK.md`` §8）。

竞品分析里 F5 那条坑写得很直白：**窄屏无显式降级 = 列被挤压截断**（k9s 中招）。
lazygit 的 portraitMode 是正面样板。所以降级不能等布局引擎自己挤，必须**显式
按宽度分档**，而且每一档拿掉什么是写死的：

    ≥160  Dock + Canvas×3 + Inspector       全展开
    140-159  Dock + Canvas×2 + Inspector 条  Inspector 收成 1 列
    120-139  Dock + Canvas×2                 Inspector 隐藏，Ctrl+I 浮层调出
    100-119  Dock 图标列 + Canvas×2          Dock 收成 1 列
     80-99   Dock 图标列 + Canvas×1          取消分屏
      <80    单栏 + Tab 切换                 Dock 转为浮层

做成纯函数是为了能测：布局降级是那种"平时不会有人手动去把终端拖到 97 列"
的逻辑，不测就等于没写。

本模块下半部分是它的**图元级对应**（``docs/COMPONENT.md`` §3，网页版
"图元尺寸与排布"一节）：上面的整屏降级决定**给几个 Canvas、每个多宽**，
下面的图元尺寸决定**每个 Canvas 里那张图怎么缩**。两者必须对得上，
所以放在同一个模块里，由同一份单测同时压。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Mapping


class DockMode(Enum):
    """Dock 的三种形态。"""

    FULL = "full"  # 标签条 + 内容区
    RAIL = "rail"  # 只剩竖向标签条（图标列）
    OVERLAY = "overlay"  # 完全让位，Ctrl+B 以浮层调出

    @property
    def columns(self) -> int:
        return {DockMode.FULL: 26, DockMode.RAIL: 3, DockMode.OVERLAY: 0}[self]


class InspectorMode(Enum):
    """Canvas B / Inspector 的三种形态。"""

    FULL = "full"  # 18–24 列，承载"结论的依据"
    STRIP = "strip"  # 收成 1 列的条
    HIDDEN = "hidden"  # 隐藏，Ctrl+I 浮层调出

    @property
    def columns(self) -> int:
        return {InspectorMode.FULL: 22, InspectorMode.STRIP: 1, InspectorMode.HIDDEN: 0}[self]


@dataclass(frozen=True)
class Layout:
    """某个终端尺寸下的布局判决。"""

    dock: DockMode
    canvases: int
    inspector: InspectorMode
    #: Agent Console 的行数。3 行是底线，低于它就没法看步骤流了。
    console_rows: int
    #: 单任务时 Tab Bar 隐藏——一个标签的标签栏只是在占一行。
    show_tabs: bool

    @property
    def summary(self) -> str:
        return (
            f"Dock:{self.dock.value} Canvas×{self.canvases} "
            f"Inspector:{self.inspector.value} Console:{self.console_rows}行"
        )


CONSOLE_MIN_ROWS = 3
CONSOLE_MAX_ROWS = 12


def resolve_layout(width: int, height: int, *, tasks: int = 1) -> Layout:
    """按终端尺寸判定布局。

    宽度决定分栏，高度决定 Console 能留多少行。**Header / Input / Status 永不
    隐藏**——它们是方向感的锚点，宁可把 Canvas 压小。
    """
    if width >= 160:
        dock, canvases, inspector = DockMode.FULL, 3, InspectorMode.FULL
    elif width >= 140:
        dock, canvases, inspector = DockMode.FULL, 2, InspectorMode.STRIP
    elif width >= 120:
        dock, canvases, inspector = DockMode.FULL, 2, InspectorMode.HIDDEN
    elif width >= 100:
        dock, canvases, inspector = DockMode.RAIL, 2, InspectorMode.HIDDEN
    elif width >= 80:
        dock, canvases, inspector = DockMode.RAIL, 1, InspectorMode.HIDDEN
    else:
        dock, canvases, inspector = DockMode.OVERLAY, 1, InspectorMode.HIDDEN

    # 高度收缩优先级：Console → Canvas → Tab Bar。
    # Console 先让，因为它是过程信息；Canvas 是结论，最后才动。
    console_rows = max(CONSOLE_MIN_ROWS, min(CONSOLE_MAX_ROWS, (height - 8) // 4))

    return Layout(
        dock=dock,
        canvases=canvases,
        inspector=inspector,
        console_rows=console_rows,
        # 单任务时隐藏——一个标签的标签栏只是在占一行
        show_tabs=tasks > 1,
    )


def canvas_columns(total: int, layout: Layout) -> tuple[int, ...]:
    """把主区宽度分给各 Canvas。

    左右分默认 60/40——主力形态是"结论 ↔ 证据"，结论那栏该更宽。
    三分时第三栏最窄，因为它优先被牺牲（下一档就折叠成 Inspector 条了）。
    """
    usable = max(0, total - layout.dock.columns - layout.inspector.columns)
    if layout.canvases <= 1:
        return (usable,)
    if layout.canvases == 2:
        left = round(usable * 0.6)
        return (left, usable - left)
    left = round(usable * 0.4)
    mid = round(usable * 0.35)
    return (left, mid, usable - left - mid)


# ══ 图元尺寸与排布 ═══════════════════════════════════════════════════════
#
# 上面那套决定"给几个 Canvas、每个多宽"，这一套决定"每个 Canvas 里的图怎么缩"。
#
# 起因是多图元同屏：一屏上同时挂着 braille 曲线、热力网格、gauge、双向面积、
# 算子表、Trace 泳道，每种图的尺寸如果各自临时定，结果就是谁也不知道某张图
# 在 24 列的栏里到底该画还是不该画——**"画得下"和"读得出"不是一回事**。
#
# 所以每种图元定四个数：最小可读尺寸 · 推荐尺寸 · 纵横比约束 · 收缩优先级。

#: Canvas 边框（1）+ 内边距（1），左右各一份。
CHART_TRIM = 2
#: 上下框线各一行。标题排在上框线里（不额外占行），所以只减 2。
ROW_TRIM = 2

#: 终端字符格的宽高比约 1:2。视觉纵横比 = 列 ÷ (2 × 行)——本模块里所有
#: ``ratio`` 都是**列÷行**的原始格子比，换算成眼睛看到的比例要再除以 2。
CELL_ASPECT = 2


class Shrink(IntEnum):
    """同屏并置时谁先让出空间。数值小的先收缩。

    排序依据是**降级损失**，不是重要性：掉一层还能答同一个问题的先让，
    形状本身就是信息的最后让。这跟 :func:`resolve_layout` 里"Console 先让、
    Canvas 后让"是同一条原则——过程信息让位给结论。
    """

    #: 掉成一行数字，结论零损失（Metric Bar 掉成 "84.3%" 什么都没丢）。
    FIRST = 1
    #: 掉一层仍在回答同一个问题（面积 → Sparkline）。
    EARLY = 2
    #: 压缩会丢掉比较能力（排行少几行就少几个可比对象）。
    LATE = 3
    #: 形状即信息，压扁等于没画（火焰图的栈形、泳道的先后、热力的拓扑）。
    LAST = 4


@dataclass(frozen=True)
class PrimitiveSize:
    """一种图元的尺寸规格。单位是**字符格**，不是像素。"""

    #: ``docs/COMPONENT.md`` §3 的小节号。
    section: str
    label: str
    #: 最小可读尺寸。低于它这张图就不该画——该走 :attr:`fallback`。
    min_cols: int
    min_rows: int
    #: 推荐尺寸。给得起就给到这个数。
    rec_cols: int
    rec_rows: int
    #: 列÷行的允许区间；``None`` 表示行数不由宽度决定（恒定行高，或由数据定）。
    ratio: tuple[float, float] | None
    shrink: Shrink
    #: 画不下时退成什么。空着不算规格——"不画"也必须写清楚退到哪儿。
    fallback: str
    #: 宽度越大越好、不封顶。只有两种图元是这样，理由写在各自的注释里。
    fills_width: bool = False
    #: 行数必须是它的整数倍。默认 1（无约束）；双向面积是 2，因为上下两半
    #: **必须等高**——奇数行劈不开，而"上下一样高 = 收发一样多"正是它的读法。
    rows_step: int = 1

    @property
    def visual_aspect(self) -> tuple[float, float] | None:
        """换算成眼睛看到的宽高比（列÷行 再除以字符格的 1:2）。"""
        if self.ratio is None:
            return None
        return (self.ratio[0] / CELL_ASPECT, self.ratio[1] / CELL_ASPECT)


#: 十四节规格（``COMPONENT.md`` §3.1–3.14）拆成十七种画法——§3.4 一节含
#: 折线 / 面积 / Sparkline 三种，三者行数差着数量级，合成一行没法用；
#: Before/After 在 §3.1 的"比大小"组里，实现是 ``bars.before_after``。
#:
#: 每个数字的来历都写在行尾，因为**没有理由的尺寸下次就会被人随手改掉**。
PRIMITIVES: Mapping[str, PrimitiveSize] = {
    # ── 比大小 ───────────────────────────────────────────────────────────
    # 10 / 20 两档是 COMPONENT.md §3.1 写死的。10 格 × 八分块 = 80 档，
    # 刚好够把 82% 和 85% 分开——这正是 §3.0 规则①存在的理由。
    "metric_bar": PrimitiveSize("3.1", "Metric Bar", 10, 1, 20, 1, None,
                                Shrink.FIRST, "T0 数值 + 单位"),
    # 3 行才叫排行（第一 vs 第二 vs 第三），2 行只是对比；外加 1 行"… N more"，
    # 那行是 §3.0 规则③的硬性要求，不能省。宽度 = 标签列 14 + bar 10。
    "ranking": PrimitiveSize("3.2", "排行 Ranking", 24, 4, 34, 11, None,
                             Shrink.LATE, "Top-1 + 数值，尾部仍标 … N more"),
    # 2 系列 × 2 类目才有并排的意义；每组 8 列 + 1 列间隔。行数 = 系列数 + 类目标签行。
    "grouped": PrimitiveSize("3.3", "多列条形", 17, 3, 26, 4, None,
                             Shrink.EARLY, "拆成各自独立的 Metric Bar"),
    # 两条共用量程的 bar（各 10）+ 箭头 4。压到一行文本仍然保住了改善幅度。
    "before_after": PrimitiveSize("3.1", "Before/After", 24, 1, 32, 1, None,
                                  Shrink.EARLY, "120ms → 70ms (−42%) 纯文本"),

    # ── 看趋势 ───────────────────────────────────────────────────────────
    # 3 行 × 20 列 = 40 × 12 点阵。再窄，braille 的 2×4 密度就换不来形状。
    # 比例下界 5 是硬的：太高太窄的曲线读成竖直乱涂；上界松，扁的折线仍可读
    # （扁到极致就是 Sparkline，本来就是它的降级形态）。
    "line": PrimitiveSize("3.4", "折线", 20, 3, 40, 6, (5.0, 24.0),
                          Shrink.LATE, "T1 Sparkline"),
    # 面积从底边填起，比折线少一行也读得出，所以最小值比折线低一行。
    # 比例带和折线**一样**：两者是同一套几何，只差填不填，没有理由要求面积更扁——
    # 早先给它 (8, 30) 是拍脑袋，结果 30 列时最多只能画 3 行，图挤成一条。
    "area": PrimitiveSize("3.4", "面积", 20, 2, 40, 5, (5.0, 24.0),
                          Shrink.EARLY, "T1 Sparkline"),
    # 8 列 = 8 个采样点。再少就不是趋势，是三个数。
    "sparkline": PrimitiveSize("3.4", "Sparkline", 8, 1, 20, 1, None,
                               Shrink.FIRST, "T0 当前值 + 峰值"),
    # 上下各 1 行是底线，且**上下行数必须相等**——不等的话"上下一样高"就不
    # 代表"收发一样多"，而这张图的全部意义就是对称比较（§3.5）。
    "mirrored": PrimitiveSize("3.5", "双向面积", 20, 2, 40, 4, (5.0, 24.0),
                              Shrink.EARLY, "两行数值：↑ 1.30 KiB/s ↓ 346 B/s",
                              rows_step=2),

    # ── 找位置 ───────────────────────────────────────────────────────────
    # 比例锁死 2.0：16 列 × 8 行 = 32 × 32 点阵，视觉上也是正方。
    # 散点**两根轴都是数据轴**，拉扁就是把斜率画错——Roofline 上斜率就是结论。
    "scatter": PrimitiveSize("3.6", "散点", 16, 8, 24, 12, (2.0, 2.0),
                             Shrink.LATE, "不画。散点没有一维等价物，退成 compute/memory-bound 判定文字"),
    # 行数 = 栈深，深度方向不做降采样（§3.7）——压扁了火焰图就没有价值了。
    # 宽度决定丢帧阈值：30 列丢掉 <3.3% 的帧，60 列只丢 <1.7%，所以宽度不封顶。
    "flame": PrimitiveSize("3.7", "火焰图", 30, 3, 60, 8, None,
                           Shrink.LAST, "Top-N 自耗时表", fills_width=True),
    # 2 条泳道 + 1 行时间轴。少于 2 条就答不了"谁在等谁"。
    # 宽度即时间分辨率，同样不封顶。
    "timeline": PrimitiveSize("3.8", "泳道 Timeline", 30, 3, 56, 6, None,
                              Shrink.LAST, "每条泳道一行占用百分比", fills_width=True),

    # ── 看余量 ───────────────────────────────────────────────────────────
    # 比例上界 0.8 < 1 是硬的：**水位必须比它宽的时候更高**，扁了就读成横向
    # bar，而水位答的是"还剩多少"、bar 答的是"占了多少"（§3.9）。
    "water": PrimitiveSize("3.9", "水位", 3, 4, 3, 8, (0.25, 0.8),
                           Shrink.FIRST, "38.2 / 64 GiB 纯文本"),
    # 12 列是被**未知进度**卡住的：跑动窄块占 2 格，跑道要看得出在跑。
    # 已知进度 8 列就够（八分块 64 档），但两种形态必须同宽，否则一切换就跳。
    "progress": PrimitiveSize("3.10", "进度", 12, 1, 28, 1, None,
                              Shrink.FIRST, "百分比数字；未知进度改为 ⠹ + 已耗时"),
    # 每段至少 3 列才分得清边界 → **段数上限 = 宽度 ÷ 3**，超出的并进"其他"。
    # 4 段是典型（used / cached / kv / free），所以最小 16 列 + 1 行图例。
    "segmented": PrimitiveSize("3.11", "分段", 16, 2, 30, 2, None,
                               Shrink.FIRST, "各段数值列表"),

    # ── 读单值 ───────────────────────────────────────────────────────────
    # 行数恒 5，由字形定死（§3.12 试过 3×3，只用 █ 的话 2/3/8 几乎一样）。
    # 宽度 = 位数 × 3 + 间隔：3 位 → 11，5 位 → 19。不取 4 的倍数，
    # 因为这个数来自字形几何，凑整就是把规格编出来。
    "bignum": PrimitiveSize("3.12", "像素数字", 11, 5, 19, 5, None,
                            Shrink.FIRST, "常规字号数字"),
    # 值 6 + 单位 4 + delta 8 = 18，是"现在多少 + 和之前比"的底线。
    # 走势条要 ≥12 列才有意义，放不下就**整条省略**而不是压成 6 列的假趋势。
    "stat": PrimitiveSize("3.13", "数图 Stat", 18, 1, 32, 1, None,
                          Shrink.FIRST, "值 + delta 一行文本"),

    # ── 看分布 ───────────────────────────────────────────────────────────
    # 16 × 4 是鲲鹏 920 六十四核的自然分块：每行 16 核 = 一个 NUMA node。
    # 行列由**拓扑**定，不由可用空间定——所以没有比例约束，也不吃满宽度。
    # 推荐尺寸多出来的列和行是右侧 NUMA 汇总条与顶部图例。
    "heatmap": PrimitiveSize("3.14", "热力网格", 16, 4, 32, 6, None,
                             Shrink.LAST, "按 NUMA 聚合成 4 行，每行一个数"),
}


def chart_box(canvas_cols: int, canvas_rows: int) -> tuple[int, int]:
    """Canvas 的外尺寸 → 图元真正能画的格子数。

    列减掉左右各 :data:`CHART_TRIM`（框线 + 内边距），行只减上下框线——
    标题排在上框线里，不另占一行。
    """
    return (max(0, canvas_cols - 2 * CHART_TRIM), max(0, canvas_rows - ROW_TRIM))


def fit_box(key: str, cols: int, rows: int) -> tuple[int, int] | None:
    """在 ``cols × rows`` 的盒子里，这种图元实际该画多大。

    返回 ``None`` 表示**放不下，不该画**——调用方应改画
    :attr:`PrimitiveSize.fallback`。这是本模块存在的理由：判决只有一处，
    不是每个 widget 各自拍脑袋。
    """
    spec = PRIMITIVES[key]
    if cols <= 0 or rows <= 0:
        return None

    if spec.ratio is None:
        # 行数不由宽度决定：吃到推荐值为止（火焰图与泳道除外，它们不封顶）。
        w = cols if spec.fills_width else min(cols, spec.rec_cols)
        h = min(rows, spec.rec_rows)
    else:
        lo, hi = spec.ratio
        w, h = cols, rows
        if w > h * hi:      # 太扁：收窄，别把 20 列的曲线摊成 200 列
            w = int(h * hi)
        elif w < h * lo:    # 太高太窄：削行，比例失真比少画几行危险
            h = int(w / lo)

    # 行数步长最后压，且只往下取整——宁可少一行，不能超出给定的盒子。
    if spec.rows_step > 1:
        h -= h % spec.rows_step

    if w < spec.min_cols or h < spec.min_rows:
        return None
    return (w, h)


def fits(key: str, cols: int, rows: int) -> bool:
    """这种图元在这个盒子里画得下且读得出。"""
    return fit_box(key, cols, rows) is not None


def drawable(cols: int, rows: int) -> tuple[str, ...]:
    """这个盒子能承载哪些图元，按收缩优先级排序（最先让的在前）。"""
    return shrink_order(k for k in PRIMITIVES if fits(k, cols, rows))


def shrink_order(keys) -> tuple[str, ...]:
    """多图元同屏时的收缩顺序：谁先让出空间排在前面。

    同一档内先让**推荐面积大**的——从大图上收回一样多的格子，代价更小。
    """
    return tuple(sorted(
        keys,
        key=lambda k: (PRIMITIVES[k].shrink,
                       -(PRIMITIVES[k].rec_cols * PRIMITIVES[k].rec_rows),
                       k),
    ))
