"""左侧 Dock —— 从顶通到底（``docs/FRAMEWORK.md`` §7 · VISUAL.md「Shell 结构」）。

结构上这是整套框架里最关键的一条：**Dock 从标题栏下方一直通到状态栏**，
品牌标识进 Dock 的头部，tab 带缩回主区。原来那版是"全宽 appbar → 下面才分
左右"，屏幕上会出现两条起点不同的横向分割，左上角那块区域归属不明。改完之后
一条垂直分割贯穿全屏、一条水平分割横贯全屏，**两条线各只出现一次**。

Dock 里的东西全是 **Chrome 层**——用真组件，不是字符拼的。判据是那句：
用户在这里做的是选择、导航、切换、确认，所以必须有 hover / selected /
focus / disabled 四态。字符拼不出"我现在选中的是哪一项"。

一个细节：Dock 头和 tab 带**必须等高**，否则那条水平分割线会在中间断一截。
两边都写死同一个值（:data:`HEAD_ROWS`），不靠内容撑。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Label, ListItem, ListView, Static

from ..render.ramp import sequential
from ..spec import ComponentSpec
from ..tiers import Tier
from ..tokens import (
    ACCENT,
    KUNPENG_RED,
    STATUS_GLYPH,
    SURFACE_2,
    foreground,
)

#: Dock 头与 Tab 带共用的高度。改这个值要两边一起改，所以它只能有一份。
HEAD_ROWS = 1


@dataclass
class DockItem:
    """Dock 列表里的一行。"""

    label: str
    #: :data:`devkitai.tokens.STATUS_GLYPH` 的键。
    status: str = "pending"
    #: 右侧元信息（耗时、命中数、文件数）。
    meta: str = ""
    #: 徽标计数。0 表示不显示。
    badge: int = 0
    #: `NEW` 标——红被允许的唯一"功能位"。它必须是会消失的，
    #: 否则就不是徽章而是装饰，所以只开放给列表项，不进常态 Chrome。
    new: bool = False
    #: 0–100 的风险值；> 0 时在行尾画一条域色阶风险条（工程树用）。
    risk: float | None = None
    #: 缩进层级（工程树用）。
    depth: int = 0


@dataclass
class DockPanel:
    """Dock 的一个面板。"""

    key: str
    title: str
    #: 竖向标签条上的单字符。
    glyph: str
    items: list[DockItem] = field(default_factory=list)
    hint: str = ""


def default_panels() -> list[DockPanel]:
    """FRAMEWORK.md §7 的五个面板。"""
    return [
        DockPanel("tasks", "TASKS", "T", hint="[Alt+1..9]"),
        DockPanel("project", "PROJECT", "P", hint="⇄ 跟随"),
        DockPanel("tools", "TOOLS", "L"),
        DockPanel("kb", "KB", "K"),
        DockPanel("history", "HISTORY", "H"),
    ]


class DockRail(Static):
    """竖向标签条：折叠时只剩这一列。

    ``▮`` 当前面板，``▯`` 其它。这一列常驻——折叠掉的是内容区，不是导航本身，
    否则用户折叠之后就不知道还有哪些面板了。
    """

    active: reactive[int] = reactive(0)

    DEFAULT_CSS = """
    DockRail { width: 3; background: $pto-surface-2; }
    """

    def __init__(self, panels: list[DockPanel], **kwargs) -> None:
        super().__init__(**kwargs)
        self.panels = panels

    def render(self) -> Text:
        out = Text()
        muted = foreground(SURFACE_2, "muted")
        for i, panel in enumerate(self.panels):
            current = i == self.active
            # 当前项靠字形 + 明度双重编码：16 色降级下明度会塌，字形还在
            out.append(" ▮ " if current else " ▯ ",
                       style=foreground(SURFACE_2, "fg") if current else muted)
            out.append("\n")
        return out


class DockHeader(Static):
    """Dock 头部：品牌标识。

    顶栏的最终形态是 **Kunpeng 标识（唯一的红）+ KUNPENG（中性描边）+
    DEVKIT AI（中性反色）**——整条只有一处彩色。`NEW` 标曾经挂在这里，
    试过就撤了：顶栏全程常驻，一个永远亮着的 `NEW` 既失去时效意义，
    又让本该只有一处红的顶栏出现第二处红，两块红互相削弱。
    """

    DEFAULT_CSS = """
    DockHeader { height: 1; background: $pto-surface-2; }
    """

    def render(self) -> Text:
        out = Text()
        out.append(" ▪ ", style=KUNPENG_RED)  # 唯一的红：身份
        out.append("KUNPENG ", style=foreground(SURFACE_2, "muted"))
        out.append(" DEVKIT AI ", style=f"{foreground(SURFACE_2, 'fg')} reverse")
        return out


class DockItemRow(ListItem):
    """一个列表项。

    刻意做成 :class:`~textual.widgets.ListItem` 的子类而不是自绘的字符行——
    hover / selected 的层次感字符拼不出来，而"我现在选中的是哪一项"是工作台
    的基本诉求。四态交给 TCSS，这里只管内容。
    """

    def __init__(self, item: DockItem, domain: str = "cpu") -> None:
        super().__init__()
        self.item = item
        self.domain = domain

    def compose(self) -> ComposeResult:
        yield Label(self._line())

    def _line(self) -> Text:
        item = self.item
        out = Text()
        out.append("  " * item.depth)
        out.append(f"{STATUS_GLYPH.get(item.status, '·')} ", style=self._status_style())
        out.append(item.label)
        if item.new:
            # 小尺寸、方形、红底白字、全大写紧字距——红被允许的唯一功能位
            out.append(" NEW ", style=f"reverse {KUNPENG_RED}")
        if item.badge:
            out.append(f" {item.badge}", style=ACCENT)
        if item.meta:
            out.append(f"  {item.meta}", style=foreground(SURFACE_2, "muted"))
        if item.risk is not None and item.risk > 0:
            out.append(" ")
            # 风险条是**色块**，走域色阶顺序取档；语义色不参与数值大小的表达
            out.append("█" * max(1, round(item.risk / 34)),
                       style=sequential(item.risk, 0.0, 100.0, "memory"))
        return out

    def _status_style(self) -> str:
        from ..tokens import PRIMARY_TEXT, SEMANTIC

        return {
            "done": SEMANTIC["success"],
            "warning": SEMANTIC["warning"],
            "failed": SEMANTIC["danger"],
            "paused": SEMANTIC["warning"],
            "running": PRIMARY_TEXT,  # 当前对象——蓝的配额之一
        }.get(self.item.status, foreground(SURFACE_2, "muted"))


class DockSection(Vertical):
    """分区标题 + 列表。"""

    DEFAULT_CSS = """
    DockSection { height: auto; }
    DockSection > .section-title { height: 1; }
    DockSection ListView { height: auto; max-height: 12; background: $pto-background; }
    """

    def __init__(self, panel: DockPanel, **kwargs) -> None:
        super().__init__(**kwargs)
        self.panel = panel

    def compose(self) -> ComposeResult:
        yield Static(self._title(), classes="section-title")
        yield ListView(*(DockItemRow(item) for item in self.panel.items))

    def _title(self) -> Text:
        """分区标题：全大写 + 字间插空格模拟 letter-spacing。

        PTO 的 label 有 +0.5px 字距，终端没有亚字符，只能在字符间插空格。
        仅用于分区标签这类短文本，长文本禁用——插空格会毁掉可读性。
        **CJK 标题不做全大写**（无大小写形态），只保留字距。
        """
        out = Text()
        out.append(" " + " ".join(self.panel.title), style=foreground(SURFACE_2, "muted"))
        if self.panel.items:
            out.append(f"  {len(self.panel.items)}", style=ACCENT)
        if self.panel.hint:
            out.append(f"   {self.panel.hint}", style=foreground(SURFACE_2, "muted"))
        return out


class Dock(Horizontal):
    """竖向标签条 + 内容区，从顶通到底。"""

    SPEC = ComponentSpec(
        tier=Tier.INTERACTIVE,
        keyboard={
            "ctrl+b": "折叠 / 展开内容区（保留标签条）",
            "j/k · ↑↓": "列表上下",
            "enter": "下钻 / 展开",
            "alt+1..9": "直达任务",
            "tab": "区域焦点轮转",
        },
        tokens=("SURFACE_2", "KUNPENG_RED", "ACCENT", "STATUS_GLYPH", "$pto-selected"),
        degraded_as="窄于 100 列收成图标列；窄于 80 列转为浮层（layout.resolve_layout）",
        notes="Dock 头与 Tab 带写死同一高度，否则那条水平分割线会在中间断一截",
    )

    DEFAULT_CSS = """
    Dock { width: auto; background: $pto-surface-2; }
    Dock > #dock-body { width: 23; background: $pto-background; }
    Dock.-collapsed > #dock-body { display: none; }
    """

    collapsed: reactive[bool] = reactive(False)

    def __init__(self, panels: list[DockPanel] | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.panels = panels if panels is not None else default_panels()

    def compose(self) -> ComposeResult:
        yield DockRail(self.panels)
        with VerticalScroll(id="dock-body"):
            yield DockHeader()
            for panel in self.panels:
                yield DockSection(panel)

    def watch_collapsed(self, collapsed: bool) -> None:
        self.set_class(collapsed, "-collapsed")

    def follow(self, path: str) -> bool:
        """`⇄ 跟随`：Agent 改到哪个文件，工程树就定位到哪个文件。

        这是从 MobaXterm 的 SFTP「Follow terminal folder」搬来的，也是
        FRAMEWORK.md §7 里点名"最值得实现"的那个细节。价值在于**联动不只
        发生在用户点击时，也发生在 Agent 行动时**——用户不需要在"AI 说它改了
        crypto.c"和"我去树里找 crypto.c"之间做翻译。

        返回是否命中。没命中不报错：Agent 可能在动一个还没进树的新文件。
        """
        project = next((p for p in self.panels if p.key == "project"), None)
        if project is None:
            return False
        for index, item in enumerate(project.items):
            if item.label == path or path.endswith(item.label):
                try:
                    section = self.query(DockSection).filter(
                        lambda s: s.panel.key == "project"
                    ).first()
                except Exception:
                    return True  # 未挂载时只更新数据，不算失败
                section.query_one(ListView).index = index
                return True
        return False
