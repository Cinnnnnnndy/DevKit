"""Chrome 层的行为测试。

这一层的价值全在"状态表达"——用户在这里做的是选择、导航、切换、确认。
所以测的是：四态在不在、当前对象指向对不对、纪律有没有被破坏。
"""

import pytest
from rich.cells import cell_len

from devkitai.tokens import KUNPENG_RED, PRIMARY, SEMANTIC
from devkitai.widgets import (
    Dock,
    DockItem,
    DockPanel,
    KeyBar,
    StatusBar,
    TabBar,
    Task,
    default_panels,
)
from devkitai.widgets.dock import HEAD_ROWS, DockHeader, DockItemRow, DockRail


def _plain(widget) -> str:
    return widget.render().plain


# ── Dock ──────────────────────────────────────────────────────────────────
def test_dock_head_and_tab_bar_are_the_same_height():
    """两边必须等高，否则那条水平分割线会在中间断一截。

    高度只能有一份定义（HEAD_ROWS），不靠内容撑——内容一变高度就变，
    分割线就又断了。
    """
    assert TabBar([]).styles.height.value == HEAD_ROWS
    assert "height: 1" in DockHeader.DEFAULT_CSS


def test_dock_header_carries_exactly_one_colour():
    """整条顶栏只有一处彩色：Kunpeng 标识。

    `NEW` 标曾经挂在这里，试过就撤了——顶栏全程常驻，一个永远亮着的 NEW
    既失去时效意义，又让本该只有一处红的顶栏出现第二处红。
    """
    header = DockHeader()
    spans = header.render().spans
    coloured = [s for s in spans if KUNPENG_RED in str(s.style)]
    assert len(coloured) == 1
    assert "NEW" not in _plain(header)


def test_rail_marks_the_current_panel_by_glyph_not_only_colour():
    """16 色降级下明度会塌，字形还在——所以当前项必须双重编码。"""
    rail = DockRail(default_panels())
    rail.active = 2
    lines = [line for line in _plain(rail).split("\n") if line.strip()]
    assert lines[2].strip() == "▮"
    assert all(line.strip() == "▯" for i, line in enumerate(lines) if i != 2)


def test_new_badge_is_only_available_to_list_items():
    """红被允许的唯一功能位。它必须是会消失的，否则就不是徽章而是装饰。"""
    row = DockItemRow(DockItem("profiler", "warning", new=True))
    assert "NEW" in row._line().plain
    plain = DockItemRow(DockItem("cpp_migrator", "done"))._line().plain
    assert "NEW" not in plain


def test_risk_bar_uses_a_data_ramp_not_a_semantic_colour():
    """风险条是**色块**，走域色阶顺序取档。

    语义色只上字符与短标签——把 danger 红刷进风险条会让"数值大"和
    "AI 判定有问题"变成同一种表达。
    """
    row = DockItemRow(DockItem("crypto.c", "warning", risk=92))
    text = row._line()
    block_styles = [str(s.style) for s in text.spans if "█" in text.plain[s.start:s.end]]
    assert block_styles, "应该画出了风险条"
    for style in block_styles:
        assert not any(c in style for c in SEMANTIC.values())


def test_follow_locates_a_file_without_raising_when_absent():
    """Agent 可能在动一个还没进树的新文件——没命中不该是异常。"""
    dock = Dock(default_panels())
    assert dock.follow("nowhere.c") is False


def test_follow_matches_by_suffix():
    panels = [DockPanel("project", "PROJECT", "P", items=[DockItem("crypto.c")])]
    dock = Dock(panels)
    assert dock.follow("nginx/src/crypto.c") is True


# ── TabBar ────────────────────────────────────────────────────────────────
def test_active_tab_gets_the_brand_colour_and_others_do_not():
    """蓝的配额：当前对象。一屏一个。"""
    bar = TabBar([Task("a", "done"), Task("b", "running")])
    bar.active = 1
    styles = [str(s.style) for s in bar.render().spans]
    assert sum(PRIMARY in s for s in styles) == 1


# ── StatusBar ─────────────────────────────────────────────────────────────
def test_context_gauge_turns_warning_past_the_threshold():
    bar = StatusBar()
    bar.context_pct = StatusBar.CONTEXT_WARN_AT - 1
    assert "⚠" not in _plain(bar)
    bar.context_pct = StatusBar.CONTEXT_WARN_AT
    assert "⚠" in _plain(bar)


def test_blocked_tasks_are_always_surfaced():
    """⏸ 等待配置卡着不动且需要人介入，必须常驻提示，否则任务会被遗忘。"""
    bar = StatusBar()
    bar.blocked_tasks = 0
    assert "待配置" not in _plain(bar)
    bar.blocked_tasks = 2
    text = _plain(bar)
    assert "⏸ 2 任务待配置" in text and "去处理" in text


def test_status_segments_use_lightness_not_hue():
    """首段曾经是实心品牌蓝底——它常驻且面积大，却不指向任何"当前对象"。"""
    bar = StatusBar()
    assert all(PRIMARY not in str(s.style) for s in bar.render().spans)


# ── KeyBar ────────────────────────────────────────────────────────────────
def test_keybar_is_context_scoped_not_a_global_table():
    """帮助提示是"当前状态的函数"——全局大键位表是最差解（竞品分析 M1）。"""
    bar = KeyBar()
    assert _plain(bar) == ""
    bar.keys = (("Ctrl+B", "折叠 Dock"),)
    assert "Ctrl+B" in _plain(bar) and "折叠 Dock" in _plain(bar)


def test_keybar_width_is_measured_in_cells():
    bar = KeyBar()
    bar.keys = (("Ctrl+B", "折叠 Dock"), ("?", "快捷键"))
    text = _plain(bar)
    assert cell_len(text) > len(text), "含 CJK，宽度必须按 cell 算"
