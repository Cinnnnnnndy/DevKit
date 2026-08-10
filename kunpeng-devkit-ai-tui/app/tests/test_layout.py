"""折叠降级链的单测（FRAMEWORK.md §8）。

竞品分析 F5：**窄屏无显式降级 = 列被挤压截断**。这类逻辑平时不会有人手动
把终端拖到 97 列去验，不测就等于没写。
"""

import pytest

from devkitai.layout import (
    CONSOLE_MAX_ROWS,
    CONSOLE_MIN_ROWS,
    DockMode,
    InspectorMode,
    canvas_columns,
    resolve_layout,
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
