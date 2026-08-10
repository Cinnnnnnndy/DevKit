"""纯渲染层的单测。不碰 Textual —— 降级行为必须可测，不能靠开 SSH 会话验。"""

import math

import pytest

from devkitai.render import blocks, braille
from devkitai.render.ramp import ColorDisciplineError, categorical, grayscale, sequential
from devkitai.tokens import DOMAIN_RAMPS, SEMANTIC


# ── Braille 点位映射 ───────────────────────────────────────────────────────
def test_dot_bits_match_unicode_layout():
    """点位编号是历史遗留（1 4 / 2 5 / 3 6 / 7 8），写错的症状是曲线"对但抖"。"""
    for (x, y), expected in {
        (0, 0): "⠁", (1, 0): "⠈",
        (0, 1): "⠂", (1, 1): "⠐",
        (0, 2): "⠄", (1, 2): "⠠",
        (0, 3): "⡀", (1, 3): "⢀",
    }.items():
        c = braille.BrailleCanvas(1, 1)
        c.set(x, y)
        assert c.rows_text() == [expected], f"像素 ({x},{y}) 映射错了"


def test_all_dots_lit_is_full_cell():
    c = braille.BrailleCanvas(1, 1)
    for y in range(4):
        for x in range(2):
            c.set(x, y)
    assert c.rows_text() == ["⣿"]


def test_blank_cell_uses_braille_space_not_ascii_space():
    """空白必须是 U+2800——用普通空格会让空格与有点的格宽度不同，整张图错位。"""
    assert braille.BrailleCanvas(1, 1).rows_text() == ["⠀"]


def test_out_of_range_pixels_are_ignored_not_raised():
    c = braille.BrailleCanvas(2, 1)
    assert c.set(-1, 0) is False
    assert c.set(0, 99) is False
    assert c.set(0, 0) is True


# ── 曲线 ──────────────────────────────────────────────────────────────────
def test_plot_series_is_right_aligned_when_window_not_full():
    """窗口没填满时曲线贴右边缘——切换渲染层时视线不用重新找位置。"""
    canvas = braille.plot_series([50.0, 50.0], cols=10, rows=1, lo=0.0, hi=100.0)
    rows = canvas.rows_text()[0]
    assert rows[0] == "⠀", "左侧应留空"
    assert rows[-1] != "⠀", "最新样本应贴右边缘"


def test_flat_series_does_not_crash_on_zero_span():
    canvas = braille.plot_series([7.0] * 20, cols=10, rows=2)
    assert len(canvas.rows_text()) == 2


def test_empty_series_yields_blank_canvas():
    canvas = braille.plot_series([], cols=4, rows=2)
    assert set("".join(canvas.rows_text())) == {"⠀"}


def _lit_dots(canvas: braille.BrailleCanvas) -> int:
    """数亮起的**点**，不是数非空字符格——一格里 1 个点和 8 个点都算"非空"，
    按格数断言会把半满和全满看成一样。"""
    return sum(
        bin(ord(ch) - braille.BRAILLE_BASE).count("1")
        for ch in "".join(canvas.rows_text())
    )


def test_mirrored_halves_share_one_scale():
    """上下两半必须共用量程，否则并置就失去意义——而并置正是这张图的理由。"""
    top, bottom = braille.mirrored([100.0] * 8, [50.0] * 8, cols=4, rows_each=2)
    assert _lit_dots(top) > _lit_dots(bottom), "同一量程下 100 应比 50 填得多"


def test_mirrored_bottom_grows_downward():
    """下半幅从顶边往下长——两幅都朝同一个方向的话就不是双向图了。"""
    _, bottom = braille.mirrored([0.0] * 8, [100.0] * 8, cols=4, rows_each=2)
    rows = bottom.rows_text()
    assert rows[0] != "⠀" * 4, "下半幅应从顶边开始填"


# ── 块字符 ────────────────────────────────────────────────────────────────
def test_sparkline_width_is_exact():
    assert len(blocks.sparkline([1, 2, 3], 10)) == 10
    assert len(blocks.sparkline([], 10)) == 10
    assert blocks.sparkline([1, 2, 3], 0) == ""


def test_gauge_clamps_out_of_range_fractions():
    assert blocks.gauge(-5, 10) == blocks.EMPTY * 10
    assert blocks.gauge(99, 10) == blocks.FULL * 10


def test_segmented_widths_sum_exactly():
    """末段吸收取整误差——差一格在终端里是看得见的。"""
    for parts in ([1, 1, 1], [3, 5, 7, 11], [0.1, 0.2, 0.7]):
        out = blocks.segmented(parts, 20)
        assert sum(n for _, n in out) == 20, parts


def test_heat_glyph_keeps_intensity_when_colour_is_gone():
    """T3 掉到 T1 时颜色没了，强度必须由字形接住，否则是丢信息不是降级。"""
    glyphs = [blocks.heat_glyph(v, 0, 100) for v in (0, 33, 66, 100)]
    assert glyphs == ["░", "▒", "▓", "█"]
    assert len(set(glyphs)) == 4


def test_half_block_covers_four_combinations():
    assert blocks.half_block_column(True, True) == "█"
    assert blocks.half_block_column(True, False) == "▀"
    assert blocks.half_block_column(False, True) == "▄"
    assert blocks.half_block_column(False, False) == " "


# ── 色阶纪律 ──────────────────────────────────────────────────────────────
def test_sequential_walks_the_ramp_dark_to_bright():
    ramp = DOMAIN_RAMPS["cpu"]
    assert sequential(0, 0, 100, "cpu") == ramp[0]
    assert sequential(100, 0, 100, "cpu") == ramp[-1]
    picked = [sequential(v, 0, 100, "cpu") for v in range(0, 101, 5)]
    assert picked == sorted(picked, key=ramp.index), "档位必须随数值单调上升"


def test_sequential_clamps_and_handles_degenerate_range():
    ramp = DOMAIN_RAMPS["npu"]
    assert sequential(-50, 0, 100, "npu") == ramp[0]
    assert sequential(500, 0, 100, "npu") == ramp[-1]
    # 没有量程时返回最低档：「没量程」和「值最小」在读图上是一回事，
    # 不该突然变成最亮。
    assert sequential(42, 10, 10, "npu") == ramp[0]


def test_categorical_is_stable_per_domain():
    """同一个观测对象在任何页面都该是同一个色相。"""
    assert categorical("cpu") == categorical("cpu")
    assert len({categorical(d) for d in DOMAIN_RAMPS}) == len(DOMAIN_RAMPS)


@pytest.mark.parametrize("name,colour", sorted(SEMANTIC.items()))
def test_semantic_colours_are_refused_on_blocks(name, colour):
    """语义色只上字符与短文本。一个 90% 的利用率本身不是"错误"。"""
    with pytest.raises(ColorDisciplineError, match=name):
        sequential(50, 0, 100, steps=[colour])


def test_grayscale_fallback_is_still_monotonic():
    picked = [grayscale(v, 0, 100) for v in (0, 40, 70, 100)]
    assert len(set(picked)) == 4, "灰阶降级后仍要能分出高低"
