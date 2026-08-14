"""组件评审门槛（``docs/VISUAL.md`` §6，继承 PTO 的 preview-gate 流程）。

规范要求每个组件在实现时必须声明四件事：**所属渲染层 · 降级路径 ·
键盘等价操作 · 使用的 PTO token**。

写在文档里的门槛会被绕过，写成类型的不会。所以这里把它做成组件必须挂上的
:class:`ComponentSpec`，并由 ``tests/test_spec.py`` 遍历所有组件强制检查——
漏声明是测试失败，不是评审时才发现。

其中"键盘等价"是硬性要求而不是可选项：无鼠标的 SSH 场景是 DevKit 主战场，
T4 的每个鼠标操作都必须有键盘路径。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .tiers import Tier, degradation_path


@dataclass(frozen=True)
class ComponentSpec:
    """一个组件的评审声明。"""

    #: 组件想要的渲染层。实际生效的层由 :func:`devkitai.tiers.resolve` 压出来。
    tier: Tier
    #: 鼠标 / 指针操作 → 键盘等价键。T4 组件不许为空。
    keyboard: Mapping[str, str]
    #: 用到的 PTO token 名（``devkitai.tokens`` 里的常量名或 ``$pto-*`` 变量名）。
    tokens: tuple[str, ...]
    #: 这个组件在低层上退化成什么样子，一句话说清。
    degraded_as: str = ""
    #: 额外备注，比如"密度依赖等宽字体的 Braille 字形宽度"。
    notes: str = ""

    @property
    def degradation(self) -> tuple[Tier, ...]:
        return degradation_path(self.tier)

    def describe(self) -> str:
        chain = " → ".join(t.label for t in self.degradation)
        keys = "  ".join(f"[{k}] {v}" for k, v in self.keyboard.items())
        return f"{chain}\n键盘：{keys}\ntoken：{', '.join(self.tokens)}"


def declared_components() -> dict[str, ComponentSpec]:
    """收集所有挂了 :class:`ComponentSpec` 的组件，供 preview 页与测试使用。"""
    from . import widgets

    out: dict[str, ComponentSpec] = {}
    for name in widgets.__all__:
        obj = getattr(widgets, name)
        spec = getattr(obj, "SPEC", None)
        if isinstance(spec, ComponentSpec):
            out[name] = spec
    return out
