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
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


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
