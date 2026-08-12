"""可排序 / 可筛选算子表 · T4（``docs/TUI-CAPABILITY.md`` §3 ⑥）。

算子排行、进程表、Issue 表、文件风险表共用这一个组件。列头排序带 ``▾`` 标记，
行选中反色，Enter 下钻。

T4 的硬性要求在这里最直接：**每个鼠标操作都必须有键盘等价路径**——
无鼠标的 SSH 场景是 DevKit 主战场。点列头排序 ↔ ``s`` 循环排序列；
滚轮 ↔ 方向键；点行下钻 ↔ Enter。

标题嵌在上边框、当前排序 + 行数嵌在下边框，和
:class:`~devkitai.widgets.braille_chart.BrailleChart` 用同一套约定
（Textual 原生 ``border_title`` / ``border_subtitle``，见
``docs/COMPONENT.md`` "Canvas 层的框"）。原来这张表完全没有边框、
也没地方放"这是哪张表"，四张表拼在同一屏上只能靠行数猜。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

from rich.text import Text
from textual.widgets import DataTable

from ..render import blocks
from ..render.ramp import sequential
from ..spec import ComponentSpec
from ..tiers import Tier
from ..tokens import ACCENT, SURFACE_2, foreground


@dataclass(frozen=True)
class Column:
    """一列的规格。

    ``bar_domain`` 不为空时，单元格里画一条按域色阶着色的 bar——
    百分比必带 bar 是 P06 的规则。bar 是**色块**，所以只能用数据色阶。
    """

    key: str
    label: str
    width: int = 10
    numeric: bool = False
    bar_domain: str | None = None
    #: 数值列右对齐 + 固定小数位，替代 PTO 里用 mono 字族表达"这是数据"
    fmt: Callable[[object], str] | None = None


class KernelTable(DataTable):
    """按列排序、按表达式筛选的数据表。"""

    SPEC = ComponentSpec(
        tier=Tier.INTERACTIVE,
        keyboard={
            "↑↓": "移动行焦点（等价于滚轮）",
            "s": "循环切换排序列（等价于点列头）",
            "r": "正序 / 倒序",
            "enter": "下钻（等价于点行）",
            "/": "筛选表达式",
        },
        tokens=("SURFACE_2", "ACCENT", "DOMAIN_RAMPS", "$pto-selected"),
        degraded_as="T0 纯文本表，排序与筛选改由命令行参数给定",
        notes="列头点击与滚轮都必须有键盘等价——无鼠标 SSH 是主战场",
    )

    DEFAULT_CSS = """
    KernelTable { border: solid $pto-border-subtle; }
    KernelTable:focus-within { border: solid $pto-border-strong; }
    """

    def __init__(self, columns: Sequence[Column], title: str = "table", **kwargs) -> None:
        super().__init__(zebra_stripes=False, cursor_type="row", **kwargs)
        self.columns_spec = tuple(columns)
        #: 表名——算子排行 / 进程表 / Issue 表 / 文件风险表都用这一个类，
        #: 边框标题是唯一区分"这是哪张表"的地方。
        self.title = title
        self._rows_raw: list[dict] = []
        self._sort_key: str = columns[0].key
        self._reverse = True
        self._filter: str = ""

    def on_mount(self) -> None:
        for col in self.columns_spec:
            self.add_column(self._header(col), key=col.key, width=col.width)
        self.border_title = Text(self.title, style=foreground(SURFACE_2, "secondary"))
        self._rebuild()

    # ── 数据 ────────────────────────────────────────────────────────────
    def set_rows(self, rows: Sequence[dict]) -> None:
        self._rows_raw = list(rows)
        self._rebuild()

    def set_filter(self, expr: str) -> None:
        """子串筛选。刻意不做表达式语言——先把最常用的那 90% 做对。"""
        self._filter = expr.strip().lower()
        self._rebuild()

    def sort_by(self, key: str) -> None:
        if key == self._sort_key:
            self._reverse = not self._reverse
        else:
            self._sort_key = key
            self._reverse = True
        self._rebuild()

    def cycle_sort(self, step: int = 1) -> str:
        keys = [c.key for c in self.columns_spec]
        idx = (keys.index(self._sort_key) + step) % len(keys)
        self._sort_key = keys[idx]
        self._reverse = True
        self._rebuild()
        return self._sort_key

    @property
    def sort_key(self) -> str:
        return self._sort_key

    # ── 渲染 ────────────────────────────────────────────────────────────
    def _header(self, col: Column) -> Text:
        muted = foreground(SURFACE_2, "muted")
        text = Text(col.label, style=muted)
        if col.key == self._sort_key:
            # ▾ 标记当前排序列，方向由字形表达而不是颜色——16 色下依然成立
            text = Text(f"{col.label} {'▾' if self._reverse else '▴'}",
                        style=foreground(SURFACE_2, "fg"))
        return text

    def visible_rows(self) -> list[dict]:
        rows = self._rows_raw
        if self._filter:
            rows = [
                r for r in rows
                if any(self._filter in str(v).lower() for v in r.values())
            ]
        return sorted(
            rows,
            key=lambda r: _sort_value(r.get(self._sort_key)),
            reverse=self._reverse,
        )

    def _rebuild(self) -> None:
        if not self.is_mounted:
            return
        self.clear()
        for i, col in enumerate(self.columns_spec):
            self.columns[list(self.columns.keys())[i]].label = self._header(col)
        rows = self.visible_rows()
        peak = {
            c.key: max((_num(r.get(c.key)) for r in rows), default=1.0) or 1.0
            for c in self.columns_spec
            if c.bar_domain
        }
        for row in rows:
            self.add_row(*(self._cell(col, row, peak) for col in self.columns_spec))

        sort_col = next(c.label for c in self.columns_spec if c.key == self._sort_key)
        arrow = "▾" if self._reverse else "▴"
        filtered = f"/{self._filter} · " if self._filter else ""
        self.border_subtitle = Text(
            f"{filtered}{len(rows)} 行 · {sort_col} {arrow}",
            style=foreground(SURFACE_2, "secondary"),
        )

    def _cell(self, col: Column, row: dict, peak: dict[str, float]) -> Text:
        raw = row.get(col.key)
        if col.bar_domain:
            value = _num(raw)
            hi = peak[col.key]
            bar = blocks.gauge(value / hi if hi else 0.0, max(3, col.width - 7))
            out = Text()
            out.append(bar, style=sequential(value, 0.0, hi, col.bar_domain))
            out.append(f" {col.fmt(raw) if col.fmt else raw}",
                       style=foreground(SURFACE_2, "secondary"))
            return out
        text = col.fmt(raw) if col.fmt else str(raw)
        if col.numeric:
            return Text(text.rjust(col.width - 1), style=foreground(SURFACE_2, "secondary"))
        # 算子名 / ID 走 accent——替代 PTO 用 mono 字族表达的"这是数据"
        return Text(text, style=ACCENT if col.key in ("name", "id") else
                    foreground(SURFACE_2, "fg"))


def _num(value: object) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.0


def _sort_value(value: object) -> tuple[int, float, str]:
    """混排安全的排序键：数字归数字比，字符串归字符串比，None 永远垫底。

    直接把 ``None`` 丢进 ``sorted`` 会在混列上抛 TypeError，而算子表里
    "这一列这一行没采到"是常态，不是异常。
    """
    if value is None:
        return (0, 0.0, "")
    try:
        return (1, float(value), "")  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return (2, 0.0, str(value))
