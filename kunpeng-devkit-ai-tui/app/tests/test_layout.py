"""折叠降级链的单测（FRAMEWORK.md §8）。

竞品分析 F5：**窄屏无显式降级 = 列被挤压截断**。这类逻辑平时不会有人手动
把终端拖到 97 列去验，不测就等于没写。
"""

import pytest

from devkitai.layout import (
    CONSOLE_MAX_ROWS,
    CONSOLE_MIN_ROWS,
    PRIMITIVES,
    DockMode,
    InspectorMode,
    Shrink,
    canvas_columns,
    chart_box,
    drawable,
    fit_box,
    fits,
    resolve_layout,
    shrink_order,
)


@pytest.mark.parametrize(
    "width,dock,canvases,inspector",
    [
        (200, DockMode.FULL, 3, InspectorMode.FULL),
        (160, DockMode.FULL, 3, InspectorMode.FULL),
        (159, DockMode.FULL, 2, InspectorMode.STRIP),
        (140, DockMode.FULL, 2, InspectorMode.STRIP),
        (139, DockMode.FULL, 2, InspectorMode.HIDDEN),
        (120, DockMode.FULL, 2, InspectorMode.HIDDEN),
        (119, DockMode.RAIL, 2, InspectorMode.HIDDEN),
        (100, DockMode.RAIL, 2, InspectorMode.HIDDEN),
        (99, DockMode.RAIL, 1, InspectorMode.HIDDEN),
        (80, DockMode.RAIL, 1, InspectorMode.HIDDEN),
        (79, DockMode.OVERLAY, 1, InspectorMode.HIDDEN),
        (40, DockMode.OVERLAY, 1, InspectorMode.HIDDEN),
    ],
)
def test_each_breakpoint_lands_where_the_spec_says(width, dock, canvases, inspector):
    layout = resolve_layout(width, 44)
    assert layout.dock is dock
    assert layout.canvases == canvases
    assert layout.inspector is inspector


def test_degradation_is_monotonic_across_every_width():
    """越窄只能拿掉东西，不能凭空多出来——降级链不允许有回头路。"""
    previous = resolve_layout(240, 44)
    for width in range(240, 39, -1):
        current = resolve_layout(width, 44)
        assert current.canvases <= previous.canvases, f"{width} 列时 Canvas 变多了"
        assert current.dock.columns <= previous.dock.columns, f"{width} 列时 Dock 变宽了"
        assert current.inspector.columns <= previous.inspector.columns, width
        previous = current


def test_console_never_drops_below_the_floor():
    """Console 3 行是底线，低于它就没法看步骤流了。"""
    for height in range(4, 80):
        rows = resolve_layout(160, height).console_rows
        assert CONSOLE_MIN_ROWS <= rows <= CONSOLE_MAX_ROWS


def test_tabs_hidden_when_there_is_only_one_task():
    """一个标签的标签栏只是在占一行。"""
    assert resolve_layout(160, 44, tasks=1).show_tabs is False
    assert resolve_layout(160, 44, tasks=2).show_tabs is True


# ── Canvas 分栏 ───────────────────────────────────────────────────────────
def test_two_canvases_split_sixty_forty():
    """主力形态是「结论 ↔ 证据」，结论那栏该更宽。"""
    layout = resolve_layout(130, 44)  # Dock full + 2 canvas + inspector hidden
    cols = canvas_columns(130, layout)
    assert len(cols) == 2
    assert cols[0] > cols[1]
    assert abs(cols[0] / sum(cols) - 0.6) < 0.02


@pytest.mark.parametrize("width", [80, 100, 120, 140, 160, 200])
def test_canvas_columns_never_exceed_available_width(width):
    layout = resolve_layout(width, 44)
    cols = canvas_columns(width, layout)
    used = sum(cols) + layout.dock.columns + layout.inspector.columns
    assert used <= width, f"{width} 列时排布超宽了：{used}"
    assert all(c >= 0 for c in cols)


def test_three_canvases_sacrifice_the_third_column_first():
    """三分时第三栏最窄——下一档它就折叠成 Inspector 条了。"""
    layout = resolve_layout(200, 44)
    cols = canvas_columns(200, layout)
    assert len(cols) == 3
    assert cols[0] >= cols[1] >= cols[2]


# ── 外壳接线 ──────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_shell_applies_the_new_size_not_the_previous_one():
    """resize 时必须用事件带来的尺寸。

    ``self.size`` 在 on_resize 里还是**改之前**的值，拿它算布局会永远慢一拍：
    拖窄一次没反应，再拖一次才跳到上一次该有的档位。
    """
    from devkitai.layout import DockMode
    from devkitai.shell import DevKitShell

    app = DevKitShell()
    async with app.run_test(size=(200, 44)) as pilot:
        await pilot.pause()
        assert app._layout.canvases == 3

        await pilot.resize_terminal(130, 44)
        await pilot.pause()
        assert app._layout.canvases == 2, "130 列就该是双栏，不能等下一次 resize"

        await pilot.resize_terminal(90, 44)
        await pilot.pause()
        assert app._layout.dock is DockMode.RAIL
        assert app._layout.canvases == 1


# ══ 图元尺寸与排布 ═══════════════════════════════════════════════════════
# 上面测的是"给几个 Canvas、每个多宽"，下面测的是"每个 Canvas 里的图怎么缩"。
# 这两套必须对得上，所以最后一组测试把它们放在一起压。

ALL = tuple(PRIMITIVES)


@pytest.mark.parametrize("key", ALL)
def test_every_primitive_declares_a_usable_spec(key):
    """规格自洽：最小 ≤ 推荐，且两者都得是自己画得下的尺寸。

    自己在自己声明的尺寸上画不下，说明这四个数是分别拍的、没对过。
    """
    spec = PRIMITIVES[key]
    assert spec.min_cols <= spec.rec_cols
    assert spec.min_rows <= spec.rec_rows
    assert fit_box(key, spec.min_cols, spec.min_rows) is not None
    assert fit_box(key, spec.rec_cols, spec.rec_rows) is not None


@pytest.mark.parametrize("key", ALL)
def test_every_primitive_says_where_it_degrades_to(key):
    """"画不下"必须写清楚退到哪儿——空着的 fallback 不算规格。

    这条对应 COMPONENT.md §3.0 规则③：画不下的东西要显式说。悄悄不画
    和悄悄省略是同一种错。
    """
    assert PRIMITIVES[key].fallback.strip()


@pytest.mark.parametrize("key", ALL)
def test_declared_sizes_sit_inside_their_own_ratio_band(key):
    """声明的最小 / 推荐尺寸必须落在自己的比例带里。"""
    spec = PRIMITIVES[key]
    if spec.ratio is None:
        return
    lo, hi = spec.ratio
    for cols, rows in ((spec.min_cols, spec.min_rows), (spec.rec_cols, spec.rec_rows)):
        assert lo <= cols / rows <= hi, f"{key} 的 {cols}×{rows} 掉出了比例带 {spec.ratio}"


@pytest.mark.parametrize("key", ALL)
def test_fit_box_never_exceeds_the_box_it_was_given(key):
    """判决出来的尺寸永远不许超出可用盒子——超了就是把邻居挤掉。"""
    for cols in range(1, 90, 7):
        for rows in range(1, 40, 3):
            box = fit_box(key, cols, rows)
            if box is None:
                continue
            assert box[0] <= cols and box[1] <= rows, f"{key} 在 {cols}×{rows} 里要了 {box}"
            assert box[0] > 0 and box[1] > 0


@pytest.mark.parametrize("key", ALL)
def test_below_the_minimum_the_answer_is_do_not_draw(key):
    """低于最小可读尺寸必须返回 None，而不是硬画一张读不出的图。

    这是整节规格的立足点：**"画得下"和"读得出"不是一回事**。
    """
    spec = PRIMITIVES[key]
    assert fit_box(key, spec.min_cols - 1, spec.min_rows) is None
    assert fit_box(key, spec.min_cols, spec.min_rows - 1) is None


def test_mirrored_area_always_gets_an_even_number_of_rows():
    """双向面积上下两半必须等高——奇数行劈不开。

    不等高的话「上下一样高」就不再等于「收发一样多」，而这正是这张图
    唯一的读法（COMPONENT.md §3.5）。
    """
    for rows in range(1, 30):
        box = fit_box("mirrored", 40, rows)
        if box is not None:
            assert box[1] % 2 == 0, f"{rows} 行时劈出了 {box[1]}"


def test_scatter_stays_square_because_both_axes_carry_data():
    """散点两根轴都是数据轴，拉扁就是把斜率画错——Roofline 上斜率就是结论。"""
    for cols, rows in ((24, 12), (60, 12), (24, 40), (100, 9)):
        box = fit_box("scatter", cols, rows)
        if box is not None:
            assert box[0] == box[1] * 2, f"{cols}×{rows} 画出了非正方的 {box}"


def test_water_level_never_becomes_a_horizontal_bar():
    """水位必须比宽的时候更高，扁了就读成横向 bar——而两者答的不是一个问题。"""
    for cols, rows in ((3, 4), (24, 12), (60, 8), (9, 40)):
        box = fit_box("water", cols, rows)
        if box is not None:
            assert box[0] < box[1], f"{cols}×{rows} 画出了躺倒的水位 {box}"


def test_flame_and_timeline_take_every_column_they_can_get():
    """这两种图元宽度不封顶。

    火焰图的宽度就是丢帧阈值（30 列丢 <3.3% 的帧，60 列只丢 <1.7%），
    泳道的宽度就是时间分辨率。给多少用多少，不该在推荐值上封顶。
    """
    for key in ("flame", "timeline"):
        assert fit_box(key, 120, 8)[0] == 120, key
    # 反面：普通图元吃到推荐值就停，不摊成 120 列的长条
    assert fit_box("metric_bar", 120, 4)[0] == PRIMITIVES["metric_bar"].rec_cols


def test_shrink_order_lets_go_of_the_cheapest_losses_first():
    """收缩顺序按「降级损失」排：掉成数字什么都不丢的先让，形状即信息的最后让。

    跟 resolve_layout 里「Console 先让、Canvas 后让」是同一条原则。
    """
    order = shrink_order(ALL)
    levels = [PRIMITIVES[k].shrink for k in order]
    assert levels == sorted(levels), "收缩顺序里出现了回头路"
    assert PRIMITIVES[order[0]].shrink is Shrink.FIRST
    assert PRIMITIVES[order[-1]].shrink is Shrink.LAST
    # 形状即信息的三种必须排在最后
    assert {order[-1], order[-2], order[-3]} == {"flame", "timeline", "heatmap"}


def test_shrink_order_is_stable_regardless_of_input_order():
    """同一批图元不管以什么顺序传进来，收缩顺序都得一样——否则重排一次布局就换一套。"""
    assert shrink_order(ALL) == shrink_order(reversed(ALL)) == shrink_order(sorted(ALL))


# ── 与 §8 整屏降级链对齐 ──────────────────────────────────────────────────
def _narrowest_chart_box(lo: int, hi: int, rows: int = 40) -> tuple[int, int, int]:
    """某一档宽度区间里最窄的 Canvas，及其图元可用盒子。

    只在列方向做对照——行方向要等 Console / Tab Bar 的实际占用定下来，
    这里统一给一个宽松的行数，免得把还没定的东西测死。
    """
    width = min(range(lo, hi + 1),
                key=lambda w: min(canvas_columns(w, resolve_layout(w, rows))))
    canvas = min(canvas_columns(width, resolve_layout(width, rows)))
    return (width, canvas, chart_box(canvas, rows)[0])


TIERS = [(160, 400), (140, 159), (120, 139), (100, 119), (80, 99), (40, 79)]


@pytest.mark.parametrize("lo,hi", TIERS)
def test_every_tier_can_still_host_the_cheap_primitives(lo, hi):
    """六档里每一档最窄的 Canvas 都必须容得下全部 FIRST 档图元。

    FIRST 档是「掉成一行数字也不丢结论」的那批——它们要是都放不下，
    这一档就只剩纯文本了，整屏降级链等于断在这里。
    """
    _, _, box_cols = _narrowest_chart_box(lo, hi)
    for key, spec in PRIMITIVES.items():
        if spec.shrink is Shrink.FIRST:
            assert fits(key, box_cols, 12), f"{lo}-{hi} 档 {box_cols} 列放不下 {spec.label}"


def test_the_tightest_canvas_in_the_whole_chain_is_the_third_column():
    """全链路最窄的 Canvas 出现在**最宽的终端**上——三分屏的第三栏。

    这条反直觉，所以钉死：160 列时第三栏只有 28 列，图元可用 24 列，
    比 40 列终端的单栏（36 列）还窄。第三栏本来就是「优先被牺牲」的那栏
    （见 canvas_columns 的注释），尺寸规格必须按它来卡，不能按终端宽度来卡。
    """
    worst = min((min(canvas_columns(w, resolve_layout(w, 44))), w) for w in range(40, 401))
    assert worst == (28, 160)
    assert chart_box(28, 44)[0] == 24


def test_shape_bearing_primitives_do_not_fit_the_third_column():
    """火焰图与泳道在三分屏第三栏画不下——而它们恰恰是最不该被压缩的两种。

    结论不是「把它们压进去」，而是**三分屏时这两种图必须放在第一栏**。
    最小 30 列是硬的：低于它火焰图要丢掉 >3.3% 的帧，泳道分不出先后。
    """
    box_cols = chart_box(28, 44)[0]  # ≥160 三分屏第三栏
    cannot = [k for k in ALL if not fits(k, box_cols, 12)]
    assert set(cannot) == {"flame", "timeline"}
    for key in cannot:
        assert PRIMITIVES[key].shrink is Shrink.LAST
    # 第一栏（160 列时 45 列）放得下
    first_col = chart_box(canvas_columns(160, resolve_layout(160, 44))[0], 44)[0]
    for key in cannot:
        assert fits(key, first_col, 12), f"第一栏 {first_col} 列也放不下 {key}"


def test_no_canvas_in_the_whole_chain_is_too_narrow_to_draw_anything():
    """扫全部宽度：整屏降级链不许交出一个「什么图都画不了」的 Canvas。

    真出现了就是两套降级链脱节了——整屏还在给栏，图元级已经全线拒绝画。
    """
    for width in range(40, 401):
        layout = resolve_layout(width, 44)
        for canvas in canvas_columns(width, layout):
            cols, rows = chart_box(canvas, 44)
            assert drawable(cols, rows), f"{width} 列时有一栏（{canvas} 列）画不了任何图元"
