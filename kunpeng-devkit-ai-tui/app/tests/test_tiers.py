"""降级链的单测。每一条分支都要能在测试里覆盖，不需要真的去开 SSH 会话。"""

import pytest

from devkitai.tiers import Capabilities, Tier, degradation_path, detect, resolve

FULL = Capabilities(truecolor=True, braille=True, mouse=True, graphics=True)
NONE = Capabilities(truecolor=False, braille=False, mouse=False, graphics=False)


def test_degradation_targets_follow_the_spec():
    """T3 掉的是 T1 不是 T2——掉到 Braille 只会得到一张更密但没有数值的图。"""
    assert degradation_path(Tier.TRUECOLOR) == (Tier.TRUECOLOR, Tier.BLOCK, Tier.TEXT)
    assert degradation_path(Tier.BRAILLE) == (Tier.BRAILLE, Tier.BLOCK, Tier.TEXT)
    assert degradation_path(Tier.GRAPHICS) == (Tier.GRAPHICS, Tier.BLOCK, Tier.TEXT)
    assert degradation_path(Tier.INTERACTIVE) == (Tier.INTERACTIVE, Tier.TEXT)


@pytest.mark.parametrize("wanted", list(Tier))
def test_every_tier_resolves_to_something_usable(wanted):
    """兜底：最差落在 T0，任何终端都成立。"""
    assert resolve(wanted, NONE) in (Tier.TEXT, Tier.BLOCK)
    assert resolve(wanted, FULL) == wanted


def test_no_colour_terminal_drops_truecolor_to_blocks():
    caps = Capabilities(truecolor=False, braille=True, mouse=True, graphics=False)
    assert resolve(Tier.TRUECOLOR, caps) is Tier.BLOCK


def test_missing_braille_font_drops_curve_to_sparkline():
    caps = Capabilities(truecolor=True, braille=False, mouse=True, graphics=False)
    assert resolve(Tier.BRAILLE, caps) is Tier.BLOCK


def test_no_mouse_drops_interaction_to_keyboard_only_text():
    caps = Capabilities(truecolor=True, braille=True, mouse=False, graphics=False)
    assert resolve(Tier.INTERACTIVE, caps) is Tier.TEXT


# ── 环境探测：探不准一律往低了猜 ────────────────────────────────────────────
def test_dumb_terminal_is_floored():
    caps = detect({"TERM": "dumb"})
    assert caps.max_tier is Tier.BLOCK
    assert not any((caps.truecolor, caps.braille, caps.mouse, caps.graphics))


def test_empty_term_is_treated_as_no_terminal():
    """CI 日志与管道里根本没有终端可问。"""
    assert detect({}).max_tier is Tier.BLOCK


def test_no_color_env_disables_truecolor():
    env = {"TERM": "xterm-256color", "COLORTERM": "truecolor", "NO_COLOR": "1"}
    assert detect(env).truecolor is False


def test_colorterm_truecolor_is_honoured():
    assert detect({"TERM": "xterm", "COLORTERM": "truecolor"}).truecolor is True


def test_kitty_reports_graphics_protocol():
    caps = detect({"TERM": "xterm-kitty", "KITTY_WINDOW_ID": "1"})
    assert caps.graphics is True
    assert caps.max_tier is Tier.GRAPHICS


def test_braille_can_be_disabled_explicitly():
    """字形宽度探测不出来，所以给一个显式开关：对不上就自己关掉。"""
    env = {"TERM": "xterm-256color", "DEVKITAI_NO_BRAILLE": "1"}
    assert detect(env).braille is False


def test_linux_console_has_neither_braille_nor_mouse():
    caps = detect({"TERM": "linux"})
    assert caps.braille is False and caps.mouse is False


def test_high_latency_turns_off_transitions():
    """RTT > 80ms 时关掉所有过渡动画——远程每一帧都是带宽。"""
    assert Capabilities(True, True, True, False, rtt_ms=20).animations is True
    assert Capabilities(True, True, True, False, rtt_ms=200).animations is False
    assert Capabilities(True, True, True, False).animations is True
