"""组件层的行为测试：宽度计算、对齐、排序稳定性。"""

import pytest

from devkitai.tiers import Capabilities, Tier
from devkitai.widgets import Annotation, Column, CoreHeatmap, BrailleChart, KernelTable

TRUECOLOR = Capabilities(truecolor=True, braille=True, mouse=True, graphics=False)
PLAIN = Capabilities(truecolor=False, braille=False, mouse=False, graphics=False)


def _render_lines(widget) -> list[str]:
    return widget.render().plain.split("\n")


# ── 标题在框线里 —— border_title / border_subtitle ─────────────────────────
# 手画边框那版靠 cell_len 去凑 "─" 的填充长度，中文标签一多就会算错、边框
# 折行（这类 bug 只在中文下出现，纯英文界面上测不出来，跟 web 端字符画
# 对齐事故是同一类）。原生边框把这类算术交给 Rich 内部处理，所以这里不用
# 再测"宽度算对了没有"——测的是"标题真的进了 border_title/subtitle，
# 不是又悄悄退回到手画"。
def test_chart_title_lives_in_the_border_not_the_content():
    """标题必须走 border_title，不能出现在 render() 的内容区里。

    内容区是数据（braille 曲线），混进标题文字就是退回手画那版的老路。
    """
    chart = BrailleChart("cpu · kunpeng-920", "cpu", rows=2, caps=TRUECOLOR)
    chart.extend([50.0] * 40)
    assert chart.border_title is None  # 还没 on_mount，尚未设置
    body = chart.render().plain
    assert "cpu" not in body, "标题混进内容区了——应该只在 border_title 里"


def test_chart_subtitle_carries_cjk_status_and_updates_with_data():
    """底边框状态随数据变，且含中文（"当前"/"峰值"/层名）也能正常设置。

    过去这类中文状态字符串是手画边框自己拼 "└─...─┘" 时最容易算错宽度的
    地方；现在它只是传给 border_subtitle 的一个 Text，宽度由 Rich 自己管。
    """
    chart = BrailleChart("cpu", "cpu", rows=2, caps=TRUECOLOR)
    chart.extend([50.0] * 10)
    chart.render()
    first = chart.border_subtitle
    assert "当前" in first and "峰值" in first and "T2" in first

    chart.extend([90.0])
    chart.render()
    assert chart.border_subtitle != first, "峰值变了，subtitle 必须跟着变"


def test_frozen_chart_marks_it_in_the_subtitle():
    chart = BrailleChart("cpu", "cpu", rows=2, caps=TRUECOLOR)
    chart.extend([50.0] * 10)
    chart.frozen = True
    chart.render()
    assert "冻结" in chart.border_subtitle


def test_heatmap_title_is_set_once_and_subtitle_tracks_tier():
    """CoreHeatmap 原来完全没有边框——标题只是内容区顶上一行文字。

    补边框之后必须真的用上 border_title/subtitle，不能只是加了个框、
    文字还留在原地。``on_mount`` 手动调一次而不整套挂 App——它只碰
    ``self.cores`` / ``self.border_title``，不依赖真实挂载上下文。
    """
    heat = CoreHeatmap(16, 16, caps=TRUECOLOR)
    heat.on_mount()
    assert "16-core" in heat.border_title
    heat.update_utilisation([50.0] * 16)
    body = heat.render().plain
    assert "T3" in heat.border_subtitle
    assert "16-core heatmap" not in body, "标题不该留在内容区"


def test_kernel_table_title_identifies_which_table_this_is():
    """KernelTable 一个类服务四种表，边框标题是唯一区分"这是哪张表"的地方。"""
    table = KernelTable((Column("name", "Kernel"),), title="进程表")
    assert table.title == "进程表"


@pytest.mark.asyncio
async def test_chart_renders_inside_a_running_app_without_crashing():
    """真的挂进一个 App、跑一帧——不只是调用 render()，而是走 Textual 完整的
    布局 + 边框合成路径。这条覆盖的正是原生边框相对手画版本最大的差异：
    宽度计算不再是我们自己的算术，得在真实合成器里跑过一遍才算数。
    """
    from textual.app import App, ComposeResult

    from devkitai.theme import pto_variables

    class _Host(App):
        # 样式表在 mount 之前就解析，$pto-* 必须从这里进去——只在 on_mount
        # 里注册主题会撞上 UnresolvedVariableError（shell.py 已经踩过一次）。
        def get_theme_variable_defaults(self) -> dict[str, str]:
            return pto_variables()

        def compose(self) -> ComposeResult:
            yield BrailleChart("cpu · kunpeng-920", "cpu", rows=3, caps=TRUECOLOR)

    app = _Host()
    async with app.run_test(size=(40, 10)) as pilot:
        chart = app.query_one(BrailleChart)
        chart.extend([50.0 + i for i in range(40)])
        await pilot.pause()
        assert chart.border_title is not None
        assert "cpu" in chart.border_title


def test_chart_degrades_through_the_declared_chain():
    chart_hi = BrailleChart("cpu", "cpu", caps=TRUECOLOR)
    chart_lo = BrailleChart("cpu", "cpu", caps=PLAIN)
    assert chart_hi.tier is Tier.BRAILLE
    assert chart_lo.tier is Tier.BLOCK


def test_chart_rejects_unknown_domain():
    with pytest.raises(ValueError, match="未知的域"):
        BrailleChart("x", "gpu-that-does-not-exist")


def test_frozen_chart_still_accumulates_history():
    """冻结只是不重绘，数据继续收——解冻后历史必须是连续的。"""
    chart = BrailleChart("cpu", "cpu", caps=TRUECOLOR)
    chart.frozen = True
    chart.extend([1.0, 2.0, 3.0])
    assert len(chart._samples) == 3


def test_interval_cycles_through_all_presets():
    chart = BrailleChart("cpu", "cpu", caps=TRUECOLOR)
    seen = {chart.cycle_interval() for _ in range(8)}
    assert seen == {250, 500, 2000, 5000}


# ── 热力网格 ──────────────────────────────────────────────────────────────
def test_annotation_layer_does_not_shift_the_grid():
    """标注是独立图层，必须占独立的行。

    第一版把角标插在单元格后面，每多一个标注那行就往右挤一格，NUMA 条跟着
    错位——热力网格靠位置承载拓扑，一错位这张图就废了。
    """
    heat = CoreHeatmap(64, 16, caps=TRUECOLOR)
    heat.update_utilisation([50.0] * 64)
    before = [line for line in _render_lines(heat) if line.startswith(" 32-")]

    heat.annotate([Annotation(tuple(range(34, 39)), "warning", "疑似跨 NUMA 访问")])
    after = [line for line in _render_lines(heat) if line.startswith(" 32-")]

    assert before == after, "标注不能改动数据网格那一行"


def test_annotation_marker_aligns_under_its_cores():
    heat = CoreHeatmap(64, 16, caps=TRUECOLOR)
    heat.update_utilisation([50.0] * 64)
    heat.annotate([Annotation((34, 35), "danger", "x")])
    lines = _render_lines(heat)
    grid = next(i for i, line in enumerate(lines) if line.startswith(" 32-"))
    marker = lines[grid + 1]
    # 行首 8 格标签 + 核 34/35 相对本行起点的偏移 2、3
    assert marker[8 + 2] == "✕" and marker[8 + 3] == "✕"
    assert marker[8 + 1] == " " and marker[8 + 4] == " "


def test_annotation_layer_can_be_switched_off_entirely():
    heat = CoreHeatmap(64, 16, caps=TRUECOLOR)
    heat.update_utilisation([50.0] * 64)
    heat.annotate([Annotation((5,), "warning", "x")])
    heat.show_annotations = False
    assert "⚠" not in heat.render().plain


def test_heatmap_rejects_wrong_sample_count():
    heat = CoreHeatmap(64, 16, caps=TRUECOLOR)
    with pytest.raises(ValueError, match="需要 64"):
        heat.update_utilisation([1.0] * 32)


def test_heatmap_falls_back_to_glyph_gradient_without_colour():
    heat = CoreHeatmap(16, 16, caps=PLAIN)
    heat.update_utilisation([float(i * 6) for i in range(16)])
    assert heat.tier is Tier.BLOCK
    body = heat.render().plain
    assert any(g in body for g in "░▒▓█"), "颜色没了，强度得由字形接住"


# ── 算子表 ────────────────────────────────────────────────────────────────
COLUMNS = (Column("name", "Kernel", width=12), Column("total", "Total", width=8, numeric=True))


def test_sorting_tolerates_missing_values():
    """算子表里"这一行没采到"是常态，不是异常——混排不能抛 TypeError。"""
    table = KernelTable(COLUMNS)
    table._rows_raw = [
        {"name": "a", "total": 3.0},
        {"name": "b", "total": None},
        {"name": "c", "total": 1.0},
    ]
    table._sort_key, table._reverse = "total", True
    order = [r["name"] for r in table.visible_rows()]
    assert order[0] == "a" and order[-1] == "b", "None 应垫底"


def test_filter_matches_any_column():
    table = KernelTable(COLUMNS)
    table._rows_raw = [{"name": "matmul", "total": 1.0}, {"name": "softmax", "total": 2.0}]
    table._filter = "soft"
    assert [r["name"] for r in table.visible_rows()] == ["softmax"]


def test_cycle_sort_visits_every_column():
    table = KernelTable(COLUMNS)
    seen = {table.cycle_sort() for _ in range(4)}
    assert seen == {"name", "total"}


def test_sort_by_same_column_toggles_direction():
    table = KernelTable(COLUMNS)
    table.sort_by("name")
    first = table._reverse
    table.sort_by("name")
    assert table._reverse is not first
