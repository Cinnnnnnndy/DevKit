"""Tab 带 · 输入框 · keybar · 状态栏 —— Chrome 层剩下的四件。

分工判据只有一句（VISUAL.md「输入框归属会话」）：**切换页签会变的东西归页签，
不变的归窗口。** 所以输入框在主区内、与 tab 同列；全宽的只有 keybar 与状态栏。
输入框跨到 Dock 底下等于在说"这个输入是全窗口的"，而一个页签就是一个任务
会话，有自己的上下文、自己的历史、自己的输入。
"""

from __future__ import annotations

from dataclasses import dataclass

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Input, Static

from ..spec import ComponentSpec
from ..tiers import Tier
from ..tokens import (
    ACCENT,
    PRIMARY,
    PRIMARY_TEXT,
    SEMANTIC,
    STATUS_GLYPH,
    SURFACE_2,
    foreground,
)
from .dock import HEAD_ROWS


@dataclass
class Task:
    """一个任务会话 = 一个页签。"""

    title: str
    status: str = "pending"


class TabBar(Static):
    """任务标签 + 状态徽标 + 新建。

    选中态用**顶部一条实心品牌色**，这是蓝的配额里"当前对象"那一份。
    高度写死成和 Dock 头一样，否则那条水平分割线会在中间断一截。
    """

    SPEC = ComponentSpec(
        tier=Tier.INTERACTIVE,
        keyboard={
            "alt+1..9": "直达某个任务（等价于点标签）",
            "ctrl+t": "新建任务",
            "ctrl+w": "关闭当前任务",
        },
        tokens=("SURFACE_2", "PRIMARY", "STATUS_GLYPH", "$pto-selected"),
        degraded_as="单任务时整条隐藏——一个标签的标签栏只是在占一行",
        notes="与 DockHeader 共用 HEAD_ROWS，两边必须等高",
    )

    DEFAULT_CSS = """
    TabBar { height: 1; background: $pto-surface-2; }
    """

    active: reactive[int] = reactive(0)

    def __init__(self, tasks: list[Task] | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.styles.height = HEAD_ROWS
        self.tasks = tasks or []

    def render(self) -> Text:
        out = Text()
        muted = foreground(SURFACE_2, "muted")
        for i, task in enumerate(self.tasks):
            current = i == self.active
            style = f"{PRIMARY_TEXT} bold" if current else muted
            out.append(f" {STATUS_GLYPH.get(task.status, '·')} ", style=self._glyph_style(task))
            out.append(f"{i + 1} {task.title} ", style=style)
            if current:
                # 当前对象：一条实心品牌色贴边，不留缝、不圆角
                out.append("▔" * 2, style=PRIMARY)
            out.append(" ")
        out.append(" + ", style=muted)
        return out

    def _glyph_style(self, task: Task) -> str:
        return {
            "done": SEMANTIC["success"],
            "warning": SEMANTIC["warning"],
            "failed": SEMANTIC["danger"],
            "running": PRIMARY_TEXT,
        }.get(task.status, foreground(SURFACE_2, "muted"))


class PromptInput(Horizontal):
    """输入框——全场使用频率最高的交互面，所以必须是真组件。

    原来是一行裸提示符 ``❯ `` 加光标，这正是"Chrome 层要用真组件"的漏网之鱼，
    而且漏得最不该：十幕里每一幕都有它。现在是描边 + 焦点环 + 占位提示 +
    右侧快捷键槽。

    一个小细节：**光标要放在占位符前面**。真实输入框的插入点在位置 0，
    占位符是它右边的灰字；把光标放在占位符尾巴上，看着像用户已经输入了那段文字。
    Textual 的 Input 原生就是这个行为，所以这里只要不自己画光标就对了。
    """

    SPEC = ComponentSpec(
        tier=Tier.INTERACTIVE,
        keyboard={
            "ctrl+p": "命令面板",
            "enter": "提交",
            "esc": "中断 Agent / 返回上级",
            "/": "起手调命令",
        },
        tokens=("SURFACE_2", "PRIMARY", "$pto-focus", "foreground(muted)"),
        degraded_as="T0 下退回裸提示符 ❯，占位提示改为提交后的一行说明",
        notes="属于会话不属于窗口——所以它在主区内、与 tab 同列，不跨到 Dock 底下",
    )

    DEFAULT_CSS = """
    PromptInput {
        height: 3;
        background: $pto-surface-2;
        border: solid $pto-border-default;
        padding: 0 1;
    }
    PromptInput:focus-within { border: solid $pto-primary; background: $pto-focus; }
    PromptInput > .sigil { width: 2; color: $pto-primary-text; }
    PromptInput > Input { border: none; background: transparent; }
    PromptInput > .slot { width: auto; color: $pto-fg-muted; }
    """

    def __init__(self, placeholder: str = "描述你想做什么，或用 / 调命令",
                 slot: str = "Ctrl+P 命令面板", **kwargs) -> None:
        super().__init__(**kwargs)
        self.placeholder = placeholder
        self.slot = slot

    def compose(self) -> ComposeResult:
        # ❯ 是"当前动作入口"，属于蓝的配额里被保留的那几处之一
        yield Static("❯", classes="sigil")
        yield Input(placeholder=self.placeholder)
        yield Static(f" {self.slot} ", classes="slot")


class KeyBar(Static):
    """反色键位 chip + 常规文字动作。

    来自 Rebels in the Sky 的底栏：按键用反色小块，动作用常规文字——
    比纯文本 keybar 易扫读一个量级，且不占额外行。

    内容随上下文变，不是全局大键位表。这是竞品分析里 M1 那条行业共识：
    **帮助提示是"当前状态的函数"**（k9s 导航栈驱动 · lazygit context 驱动 ·
    Zellij 模式驱动）。全局大键位表是最差解。
    """

    SPEC = ComponentSpec(
        tier=Tier.TEXT,
        keyboard={"?": "快捷键速查浮层"},
        tokens=("SURFACE_2", "foreground(muted)"),
        degraded_as="本身就是 T0；窄屏时按优先级从右往左截断",
        notes="内容随当前上下文变，不做全局大键位表",
    )

    DEFAULT_CSS = """
    KeyBar { height: 1; background: $pto-surface-2; padding: 0 1; }
    """

    keys: reactive[tuple[tuple[str, str], ...]] = reactive(())

    def render(self) -> Text:
        out = Text()
        muted = foreground(SURFACE_2, "muted")
        for key, action in self.keys:
            out.append(f" {key} ", style=f"reverse {foreground(SURFACE_2, 'fg')}")
            out.append(f" {action}   ", style=muted)
        return out


class StatusBar(Static):
    """分段式状态栏，段间 1 列分隔。

    第一段曾经是实心品牌蓝底，改掉了——它常驻且面积大，占着蓝的配额却不指向
    任何"当前对象"。现在**靠明度分段而非色相**：首段中性反色，其余走 muted。

    上下文水位超阈值时用 warning 色，但只上**数字**不上底色——语义色只上字符
    与短文本这条纪律，在这里同样成立。
    """

    SPEC = ComponentSpec(
        tier=Tier.TEXT,
        keyboard={"ctrl+p": "命令面板（唯一的全局发现性入口）"},
        tokens=("SURFACE_2", "SEMANTIC", "foreground(secondary)"),
        degraded_as="本身就是 T0；窄屏时优先丢弃 model 段，保留 ctx 与待处理任务",
        notes="⏸ 等待配置必须常驻提示，否则那个任务会被彻底遗忘",
    )

    DEFAULT_CSS = """
    StatusBar { height: 1; background: $pto-surface-2; padding: 0 1; }
    """

    workspace: reactive[str] = reactive("Migrate")
    mode: reactive[str] = reactive("auto")
    model: reactive[str] = reactive("qwen")
    context_pct: reactive[int] = reactive(0)
    blocked_tasks: reactive[int] = reactive(0)

    #: 上下文水位到这个百分比就转 warning——留出的余量要够跑完当前这一步。
    CONTEXT_WARN_AT = 70

    def render(self) -> Text:
        out = Text()
        secondary = foreground(SURFACE_2, "secondary")
        muted = foreground(SURFACE_2, "muted")

        out.append(f" {self.workspace} ", style=f"reverse {foreground(SURFACE_2, 'fg')}")
        out.append(" │ ", style=muted)
        out.append(f"mode:{self.mode}", style=secondary)
        out.append(" │ ", style=muted)
        out.append(f"model:{self.model}", style=secondary)
        out.append(" │ ", style=muted)
        out.append("ctx:", style=secondary)
        warn = self.context_pct >= self.CONTEXT_WARN_AT
        out.append(f"{self.context_pct}%", style=SEMANTIC["warning"] if warn else secondary)
        if warn:
            out.append("⚠", style=SEMANTIC["warning"])
        if self.blocked_tasks:
            # ⏸ 等待配置卡着不动且需要人介入，必须常驻提示——这是 P29 里
            # 唯一被列为"最高优先级"的状态
            out.append(" │ ", style=muted)
            out.append(f"⏸ {self.blocked_tasks} 任务待配置", style=SEMANTIC["warning"])
            out.append(" [↵] 去处理", style=ACCENT)
        return out
