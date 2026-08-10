"""组件层的行为测试：宽度计算、对齐、排序稳定性。"""

import pytest
from rich.cells import cell_len

from devkitai.tiers import Capabilities, Tier
from devkitai.widgets import Annotation, Column, CoreHeatmap, BrailleChart, KernelTable

TRUECOLOR = Capabilities(truecolor=True, braille=True, mouse=True, graphics=False)
PLAIN = Capabilities(truecolor=False, braille=False, mouse=False, graphics=False)


def _render_lines(widget) -> list[str]:
    return widget.render().plain.split("\n")


def test_chart_border_accounts_for_double_width_cjk():
    """含中文的串必须按 cell 宽度算，不能按 len()。

    "当前 / 峰值"每个汉字占 2 格，用 len() 算出来的底边框会短 4 格、整行折行。
    这类 bug 只在中文标签下出现，纯英文界面上测不出来。
    """
    chart = BrailleChart("cpu", "cpu", rows=2, caps=TRUECOLOR)
    chart.extend([50.0] * 40)
    width = 60
    footer = chart._footer(width, 50.0, 90.0)
    assert cell_len(footer.plain) == width
    assert cell_len(footer.plain) != len(footer.plain), "这个断言要真的踩到 CJK"


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
