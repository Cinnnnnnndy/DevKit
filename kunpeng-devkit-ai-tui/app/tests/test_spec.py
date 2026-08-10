"""评审门槛的强制检查（VISUAL.md §6）。

写在文档里的门槛会被绕过，写成测试的不会：漏声明是测试失败，
不是评审时才发现。
"""

import pytest

from devkitai.spec import ComponentSpec, declared_components
from devkitai.tiers import Tier

COMPONENTS = sorted(declared_components().items())


def test_every_widget_is_declared():
    from devkitai import widgets

    declared = set(declared_components())
    exported = {
        name for name in widgets.__all__
        if isinstance(getattr(getattr(widgets, name), "SPEC", None), ComponentSpec)
    }
    assert declared == exported
    assert declared, "组件表不能是空的"


@pytest.mark.parametrize("name,spec", COMPONENTS)
def test_declares_keyboard_equivalents(name, spec):
    """T4 的每个鼠标操作都必须有键盘等价路径——无鼠标 SSH 是主战场。"""
    assert spec.keyboard, f"{name} 没声明键盘等价操作"
    assert all(k and v for k, v in spec.keyboard.items())


@pytest.mark.parametrize("name,spec", COMPONENTS)
def test_declares_tokens_and_degradation(name, spec):
    assert spec.tokens, f"{name} 没声明用到的 PTO token"
    assert spec.degradation[-1] is Tier.TEXT, f"{name} 的降级链没落到兼容底线"
    assert spec.degraded_as, f"{name} 没说清降级后长什么样"


@pytest.mark.parametrize("name,spec", COMPONENTS)
def test_describe_is_renderable(name, spec):
    text = spec.describe()
    assert "→" in text and "键盘" in text and "token" in text
