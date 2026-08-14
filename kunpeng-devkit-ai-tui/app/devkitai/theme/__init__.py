"""PTO 主题：由 :mod:`devkitai.tokens` 生成，不手写第二份色值。

Textual 的 :class:`~textual.theme.Theme` 会从 ``primary`` 等基色**自动派生**
一批变体（``$primary-lighten-1`` 之类）。派生出来的东西我们一概不用——
规范里每一档都是**预合成过的实色**，让框架再算一遍等于引入第二套真值。

所以这里的做法是：基色交给 Theme（Textual 内部组件要用），规范里那些档位
全部走 ``variables`` 显式塞进去，TCSS 里只引用 ``$pto-*``。
"""

from __future__ import annotations

from textual.theme import Theme

from .. import tokens as t


def pto_variables() -> dict[str, str]:
    """规范里那些预合成档位，作为 CSS 变量。

    单独拿出来是因为 App 的样式表在 mount **之前**就解析了，而主题是 mount
    之后才注册的——只挂在 Theme 上会得到 ``UnresolvedVariableError``。
    这份要经 ``App.get_theme_variable_defaults()`` 在解析前喂进去。
    """
    surface = t.SURFACE_1
    return {
        # ── surfaces §1.1 ──
        "pto-background": t.BACKGROUND,
        "pto-background-elevated": t.BACKGROUND_ELEVATED,
        "pto-surface-1": t.SURFACE_1,
        "pto-surface-2": t.SURFACE_2,
        "pto-surface-3": t.SURFACE_3,
        "pto-surface-4": t.SURFACE_4,
        # ── foreground §1.2，预合成在 surface-2 上 ──
        "pto-fg": t.foreground(t.SURFACE_2, "fg"),
        "pto-fg-secondary": t.foreground(t.SURFACE_2, "secondary"),
        "pto-fg-muted": t.foreground(t.SURFACE_2, "muted"),
        # disabled 档只给分隔线与装饰字符，文本不许用（见 tokens.MIN_TEXT_LEVEL）
        "pto-rule": t.FOREGROUND_ON[t.SURFACE_2]["disabled"],
        # ── border §4，预合成在 surface-2 上 ──
        "pto-border-subtle": t.BORDER_ON[t.SURFACE_2]["subtle"],
        "pto-border-default": t.BORDER_ON[t.SURFACE_2]["default"],
        "pto-border-strong": t.BORDER_ON[t.SURFACE_2]["strong"],
        # ── state overlays §1.4 ──
        "pto-hover": t.STATE_HOVER,
        "pto-press": t.STATE_PRESS,
        "pto-selected": t.STATE_SELECTED,
        "pto-focus": t.STATE_FOCUS,
        # ── 身份 / 交互 / 语义 §1.6 ──
        "pto-kunpeng": t.KUNPENG_RED,
        "pto-primary": t.PRIMARY,
        "pto-primary-text": t.PRIMARY_TEXT,
        "pto-accent": t.ACCENT,
        "pto-success": t.SEMANTIC["success"],
        "pto-warning": t.SEMANTIC["warning"],
        "pto-danger": t.SEMANTIC["danger"],
        "pto-fg-on-surface-1": t.foreground(surface, "fg"),
    }


def pto_theme() -> Theme:
    """构造 Dark-first 的 PTO 主题。"""
    surface = t.SURFACE_1
    return Theme(
        name="pto",
        dark=True,
        # 品牌蓝只做填充 / 边框 / 焦点底色——Textual 用它画选中与焦点，正好对上。
        primary=t.PRIMARY,
        secondary=t.ACCENT,
        accent=t.ACCENT,
        success=t.SEMANTIC["success"],
        warning=t.SEMANTIC["warning"],
        error=t.SEMANTIC["danger"],
        background=t.BACKGROUND,
        surface=surface,
        panel=t.SURFACE_2,
        foreground=t.foreground(surface, "fg"),
        variables=pto_variables(),
    )
