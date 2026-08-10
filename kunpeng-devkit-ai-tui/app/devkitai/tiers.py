"""渲染分层 T0–T5 与降级链（``docs/TUI-CAPABILITY.md`` §2）。

统一分六层，**高层必须能向低层降级**——SSH 老终端、CI 日志、不支持真彩的
环境都是 DevKit 的真实战场，不是边角情况。

    T0 文本      纯字符 + 状态符号            —（兼容底线）
    T1 块字符    ▁▂▃▅▇█ / 半块 / 象限        → T0 数字 + 百分比
    T2 Braille   ⠁⡀⣿ 点阵，2×4 = 8× 密度     → T1 Sparkline
    T3 真彩热力  bgcolor 承载数值             → T1 灰阶块字符
    T4 交互      mouse + focus + scroll       → 纯键盘等价（必须全覆盖）
    T5 图形协议  Kitty / Sixel / iTerm2       → T1 半块像素

降级是**能力驱动**的：组件声明自己想要哪一层，:func:`resolve` 拿探测到的
终端能力把它压到实际可用的那一层。组件自己不判断环境。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import IntEnum
from typing import Mapping


class Tier(IntEnum):
    """渲染层。数值可比较，但**不要**用大小直接推降级目标——见 :data:`DEGRADES_TO`。"""

    TEXT = 0
    BLOCK = 1
    BRAILLE = 2
    TRUECOLOR = 3
    INTERACTIVE = 4
    GRAPHICS = 5

    @property
    def label(self) -> str:
        return f"T{int(self)} {_LABELS[self]}"


_LABELS = {
    Tier.TEXT: "文本",
    Tier.BLOCK: "块字符",
    Tier.BRAILLE: "Braille",
    Tier.TRUECOLOR: "真彩热力",
    Tier.INTERACTIVE: "交互",
    Tier.GRAPHICS: "图形协议",
}

#: 每一层掉下去落在哪一层。注意 T3 → T1 而不是 T2：颜色承载的是数值，
#: 掉到 Braille 只会得到一张更密但没有数值的图，掉到灰阶块字符才保住语义。
DEGRADES_TO: Mapping[Tier, Tier | None] = {
    Tier.TEXT: None,
    Tier.BLOCK: Tier.TEXT,
    Tier.BRAILLE: Tier.BLOCK,
    Tier.TRUECOLOR: Tier.BLOCK,
    Tier.INTERACTIVE: Tier.TEXT,
    Tier.GRAPHICS: Tier.BLOCK,
}


@dataclass(frozen=True)
class Capabilities:
    """探测到的终端能力。字段都是"能不能"，不含任何取舍判断。"""

    truecolor: bool
    braille: bool
    mouse: bool
    graphics: bool
    #: 远程链路往返延迟（毫秒）；``None`` 表示本地或未测。
    rtt_ms: float | None = None

    @property
    def animations(self) -> bool:
        """RTT > 80ms 时关掉所有过渡动画——每一帧都是带宽（VISUAL.md §5）。"""
        from .tokens import HIGH_LATENCY_MS

        return self.rtt_ms is None or self.rtt_ms <= HIGH_LATENCY_MS

    @property
    def max_tier(self) -> Tier:
        if self.graphics:
            return Tier.GRAPHICS
        if self.mouse:
            return Tier.INTERACTIVE
        if self.truecolor:
            return Tier.TRUECOLOR
        if self.braille:
            return Tier.BRAILLE
        return Tier.BLOCK


def detect(env: Mapping[str, str] | None = None, *, rtt_ms: float | None = None) -> Capabilities:
    """从环境变量探测终端能力。

    刻意只读环境变量、不发查询序列：启动路径上不做同步 IO，且 CI / 管道里
    根本没有终端可问。探不准的一律往低了猜——**降级是安全的，误判成高层不是**。
    """
    env = os.environ if env is None else env
    term = env.get("TERM", "")
    color_term = env.get("COLORTERM", "").lower()
    program = env.get("TERM_PROGRAM", "").lower()

    if term in ("dumb", ""):
        # 没有终端可言：CI 日志、管道。一路压到兼容底线。
        return Capabilities(False, False, False, False, rtt_ms)

    no_color = "NO_COLOR" in env
    truecolor = not no_color and (
        color_term in ("truecolor", "24bit") or "256color" in term or "direct" in term
    )

    # Braille 字形宽度没法靠环境变量问出来（要看用户装了什么字体），
    # 所以给一个显式开关：对不上就自己关掉，降到 T1。
    braille = env.get("DEVKITAI_NO_BRAILLE", "") == "" and term != "linux"

    mouse = term not in ("linux",) and env.get("DEVKITAI_NO_MOUSE", "") == ""

    graphics = bool(env.get("KITTY_WINDOW_ID")) or program in ("iterm.app", "wezterm") or bool(
        env.get("DEVKITAI_FORCE_GRAPHICS")
    )

    return Capabilities(truecolor, braille, mouse, graphics, rtt_ms)


def resolve(wanted: Tier, caps: Capabilities) -> Tier:
    """把组件想要的层压到当前终端实际能给的那一层。

    沿 :data:`DEGRADES_TO` 一路往下走，直到落在能力范围内。返回值一定可用，
    最差是 :attr:`Tier.TEXT`——那是兼容底线，任何终端都成立。
    """
    tier: Tier | None = wanted
    while tier is not None and not _supported(tier, caps):
        tier = DEGRADES_TO[tier]
    return Tier.TEXT if tier is None else tier


def _supported(tier: Tier, caps: Capabilities) -> bool:
    if tier is Tier.GRAPHICS:
        return caps.graphics
    if tier is Tier.INTERACTIVE:
        return caps.mouse
    if tier is Tier.TRUECOLOR:
        return caps.truecolor
    if tier is Tier.BRAILLE:
        return caps.braille
    return True  # T1 / T0 无条件成立


def degradation_path(wanted: Tier) -> tuple[Tier, ...]:
    """列出某一层完整的降级链，供组件在评审时声明。"""
    path: list[Tier] = []
    tier: Tier | None = wanted
    while tier is not None:
        path.append(tier)
        tier = DEGRADES_TO[tier]
    return tuple(path)
