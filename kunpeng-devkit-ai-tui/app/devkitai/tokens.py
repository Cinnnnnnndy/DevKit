"""PTO Design System → TUI token 直译。

本模块是 ``docs/VISUAL.md`` 的可执行版本，**唯一的真值来源是那份文档**——
改色之前先去改文档，这里只做转录。所有值都是预合成后的实色十六进制，
终端没有 alpha 通道，运行期不做任何混色。

三条用色纪律（VISUAL.md §1.6）在这里由类型体现，不靠自觉：

* :data:`KUNPENG_RED` 只做身份，不出现在任何其它常量组里
* :data:`PRIMARY` 只做填充 / 边框 / 焦点底色；文本用 :data:`PRIMARY_TEXT`
* :data:`SEMANTIC` 只给字符与短标签用；:data:`DOMAIN_RAMPS` 只给色块与点阵用

后两者的分离在 :mod:`devkitai.render.ramp` 里有运行期检查——把语义色传进
色阶函数会直接抛错，而不是渲染出一张看不出问题的图。
"""

from __future__ import annotations

from typing import Final

# ── §1.1 Surfaces —— 1:1 直译，truecolor 下完全可复现 ────────────────────────
BACKGROUND: Final = "#101010"  # 应用底
BACKGROUND_ELEVATED: Final = "#141414"  # 面板底
SURFACE_1: Final = "#161616"  # 卡片
SURFACE_2: Final = "#1c1c1c"  # 表头 / 工具栏
SURFACE_3: Final = "#262626"  # hover
SURFACE_4: Final = "#313131"  # 选中 / 节点高亮

SURFACES: Final = (
    BACKGROUND,
    BACKGROUND_ELEVATED,
    SURFACE_1,
    SURFACE_2,
    SURFACE_3,
    SURFACE_4,
)

# ── §1.2 Foreground —— 按所叠表面离线拍平为实色 ─────────────────────────────
# 行 = 透明度档位，列 = 所叠表面。终端无 alpha，只能查表。
FOREGROUND_ON: Final = {
    BACKGROUND: {"fg": "#e7e7e7", "secondary": "#9f9f9f", "muted": "#707070", "disabled": "#4c4c4c"},
    SURFACE_1: {"fg": "#e8e8e8", "secondary": "#a2a2a2", "muted": "#737373", "disabled": "#505050"},
    SURFACE_2: {"fg": "#e8e8e8", "secondary": "#a4a4a4", "muted": "#777777", "disabled": "#555555"},
    SURFACE_3: {"fg": "#e9e9e9", "secondary": "#a8a8a8", "muted": "#7d7d7d", "disabled": "#5c5c5c"},
    SURFACE_4: {"fg": "#eaeaea", "secondary": "#adadad", "muted": "#838383", "disabled": "#646464"},
}

#: disabled 档拍平后对比度约 2.2:1，终端上比 Web 更难读（无字体抗锯齿加持）。
#: 规范：TUI 中 disabled **文本**最低使用 muted 档，disabled 档只留给分隔线与装饰字符。
MIN_TEXT_LEVEL: Final = "muted"


def foreground(surface: str, level: str = "fg") -> str:
    """取某个表面上某一档前景色的预合成实色。

    ``level`` 传 ``"disabled"`` 时会被抬到 ``muted``——见 :data:`MIN_TEXT_LEVEL`。
    需要真正的 disabled 档（分隔线、装饰字符）请直接查 :data:`FOREGROUND_ON`。
    """
    if level == "disabled":
        level = MIN_TEXT_LEVEL
    return FOREGROUND_ON[surface][level]


# ── §1.4 State overlays —— 预合成（叠在 surface-2） ─────────────────────────
STATE_BASE: Final = SURFACE_2
STATE_HOVER: Final = "#2a2a2a"  # +6%
STATE_PRESS: Final = "#333333"  # +10%
STATE_SELECTED: Final = "#18293c"
STATE_FOCUS: Final = "#162e49"

#: 终端画不出焦点外发光轮廓。替代方案是三者组合，三选二即可辨识，16 色下依然成立：
#: 焦点底色 + 左侧 ``▎`` 标记 + 边框升为 border-strong。
FOCUS_MARKER: Final = "▎"

# ── §1.3 品牌与语义 ────────────────────────────────────────────────────────
#: Kunpeng 红——**只做身份**：splash 字标、顶栏迷你标识、``NEW`` 新增标。
#: 禁止用于强调 / 选中 / 焦点 / 链接 / 语义 / 任何数据可视化。
KUNPENG_RED: Final = "#ed1c24"

#: 品牌蓝——**只做交互**，且只上填充 / 边框 / 焦点底色。
#: 实测对比度：on #1C1C1C 只有 4.12，不达 AA，所以不能直接上文本。
PRIMARY: Final = "#0077ff"
#: 一切文本 / 链接 / 图标用这一档（on #1C1C1C = 5.79，达标）。
PRIMARY_TEXT: Final = "#3d98ff"
#: 元数据 / ID / 次级强调——替代 PTO 用 mono 字族表达的"这是数据"。
ACCENT: Final = "#7c8db8"

#: 语义色——**只上字符与短文本**（``✓ ⚠ ✕``、状态标签），永不上色块。
SEMANTIC: Final = {
    "success": "#04d793",
    "warning": "#ffaa3b",
    "danger": "#ff4b7b",
}

#: 全局状态符号体系（UX-SPEC.md §5）。16 色降级下这层编码仍然成立，
#: 所以任何状态都必须先有符号、再谈颜色。
STATUS_GLYPH: Final = {
    "done": "✓",
    "running": "▶",
    "pending": "○",
    "warning": "⚠",
    "failed": "✕",
    "paused": "⏸",
}

# ── §1.6 域色映射 —— 蓝专属品牌，数据色从非蓝取 ────────────────────────────
# 档位 800 → 300（暗 → 亮 = 低 → 高）。copy-blue 与品牌色相差 7°，已退役。
DOMAIN_RAMPS: Final = {
    "cpu": ("#4d7209", "#86c70f", "#b3f141", "#caf57a"),  # ub-green
    "npu": ("#3f0675", "#6e0acd", "#9b3cf6", "#b977f9"),  # l0a-violet
    "memory": ("#773303", "#d15905", "#fa8838", "#fbab74"),  # accum-orange
    "io": ("#713f12", "#ca8a04", "#f4cb22", "#fbdc59"),  # mte-amber
}

#: 分类取色用的档位——每个域取自己的 -400 档表达"这是谁"。
CATEGORICAL_INDEX: Final = 2

# ── §4 Border —— 预合成 ────────────────────────────────────────────────────
BORDER_ON: Final = {
    BACKGROUND: {"subtle": "#1e1e1e", "default": "#282828", "strong": "#363636"},
    SURFACE_1: {"subtle": "#242424", "default": "#2d2d2d", "strong": "#3b3b3b"},
    SURFACE_2: {"subtle": "#2a2a2a", "default": "#333333", "strong": "#404040"},
    SURFACE_3: {"subtle": "#333333", "default": "#3c3c3c", "strong": "#494949"},
}

# ── §3 Spacing —— 单轴间距必须拆成双轴 ─────────────────────────────────────
# 终端单元格约 1:2（宽 ≈ 8px，高 ≈ 17–20px），一套阶梯管两个方向必然失真。
# (space_x 列, space_y 行)。代码里禁止裸数字 padding，只能取这六档。
SPACE: Final = {
    1: (0, 0),  # 终端无法表达，向上取到 space-2
    2: (1, 0),  # 行内元素间隙
    3: (2, 0),  # 表格列间距
    4: (2, 1),  # 面板内边距、区块间距
    5: (3, 1),  # 面板之间
    6: (3, 2),  # 大区块分隔
}

# ── §5 Motion —— @30fps 换算，动效只服务于功能 ─────────────────────────────
FRAMES: Final = {"fast": 3, "base": 6, "slow": 10}
#: 检测到高延迟（RTT > 该阈值，毫秒）时关掉所有过渡动画，spinner 降到 4fps。
HIGH_LATENCY_MS: Final = 80
