"""图元库的单测：条形族 · 坐标系 · 数字 / 数图。"""

import pytest

from devkitai.render import bars, bignum, plots
from devkitai.render.bignum import UnsupportedGlyph


# ── 八分之一格精度 ────────────────────────────────────────────────────────
def test_bar_has_sub_cell_precision():
    """10 格宽的 bar 要能分出 80 档，而不是 10 档。

    没有它的话 82% 和 85% 画出来一模一样——而"兼容性 82%"这种数字
    恰恰是拿来做判断的。
    """
    rendered = {bars.bar(v, 0, 100, 10) for v in range(0, 101)}
    assert len(rendered) > 10, "只有整格精度的话最多 11 种形态"


def test_bar_never_exceeds_its_width():
    for value in (0, 1, 49.9, 50, 99.99, 100, 1000):
        for width in (1, 5, 10, 33):
            assert len(bars.bar(value, 0, 100, width)) == width, (value, width)


def test_bar_rounds_up_to_a_full_cell_instead_of_overflowing():
    """7.99/8 进位后必须占满整格，不能画出 width+1 格。"""
    assert bars.bar(0.99999, 0, 1, 4) == "████"


def test_bar_without_track_is_left_ragged():
    """排行榜不要底槽——有底槽会把每行拉成等长，削弱长短对比。"""
    assert bars.bar(50, 0, 100, 10, track="") == "█████"
    assert bars.bar(50, 0, 100, 10).endswith("░")


def test_bar_clamps_out_of_range():
    assert bars.bar(-10, 0, 100, 6) == "░" * 6
    assert bars.bar(999, 0, 100, 6) == "█" * 6


# ── 水位 ──────────────────────────────────────────────────────────────────
def test_water_level_fills_from_the_bottom():
    rows = bars.water_level(0.5, 4)
    assert rows[0] == "░" and rows[-1] == "█", "水位从下往上涨"


def test_water_level_full_and_empty():
    assert bars.water_level(1.0, 3) == ["█"] * 3
    assert bars.water_level(0.0, 3) == ["░"] * 3


def test_water_level_row_count_matches_height():
    for h in range(1, 12):
        assert len(bars.water_level(0.37, h)) == h


# ── 排行 / 多列 / 对比 ────────────────────────────────────────────────────
def test_ranking_sorts_and_reports_the_tail():
    rows = [bars.RankRow(f"k{i}", float(i)) for i in range(15)]
    shown, more = bars.ranking(rows, 10, top=10)
    assert len(shown) == 10 and more == 5
    assert shown[0][0].label == "k14", "降序"


def test_ranking_scales_to_the_peak_not_the_sum():
    """长尾场景下用总和做分母会让所有 bar 都短到看不出差别。"""
    rows = [bars.RankRow("big", 100.0)] + [bars.RankRow(f"s{i}", 1.0) for i in range(50)]
    shown, _ = bars.ranking(rows, 10)
    assert shown[0][1] == "█" * 10, "最大值应占满"


def test_grouped_series_share_one_scale():
    """并排的唯一理由就是比较——分别归一化就白排了。"""
    out = bars.grouped([("a", [10, 20]), ("b", [5, 40])], 8)
    lengths = {name: [len(b) for b in barlist] for name, barlist in out}
    assert lengths["b"][1] > lengths["a"][1], "40 该比 20 长"
    assert lengths["a"][0] < lengths["b"][1]


def test_before_after_shares_scale_and_reports_delta():
    before, after, delta = bars.before_after(120, 70, 10)
    assert len(before) > len(after), "改善后应更短"
    assert delta == pytest.approx(-0.4167, abs=1e-3)


def test_before_after_tiny_change_looks_tiny():
    """分别归一化会让 120→70 和 120→119 画出一样的图。"""
    _, a1, _ = bars.before_after(120, 70, 20)
    _, a2, _ = bars.before_after(120, 119, 20)
    assert len(a2) > len(a1)


def test_segmented_sums_exactly():
    for parts in ([1, 1, 1], [3, 5, 7, 11], [0.1, 0.2, 0.7]):
        assert sum(bars.segmented(parts, 20)) == 20, parts


# ── 进度 ──────────────────────────────────────────────────────────────────
def test_unknown_progress_does_not_fake_a_bar():
    """给不出进度却画一条匀速涨的条，是在骗用户。"""
    frames = {bars.progress(None, 12, f) for f in range(10)}
    assert len(frames) > 1, "未知进度应该是动的"
    assert all(len(f) == 12 for f in frames)
    assert all(f.count("█") == 2 for f in frames), "只有一个跑动的窄块"


def test_known_progress_is_monotonic():
    widths = [bars.progress(f / 10, 10).count("█") for f in range(11)]
    assert widths == sorted(widths)


def test_spinner_cycles():
    assert len({bars.spinner(i) for i in range(10)}) == 10
    assert bars.spinner(0) == bars.spinner(10)


# ── 阈值：结论不是数据 ────────────────────────────────────────────────────
def test_threshold_returns_a_semantic_key_for_text_not_for_blocks():
    assert bars.threshold_level(30) == ""
    assert bars.threshold_level(70) == "warning"
    assert bars.threshold_level(90) == "danger"


def test_threshold_can_be_inverted_for_lower_is_worse_metrics():
    """命中率、剩余容量这类指标是越低越糟。"""
    assert bars.threshold_level(10, inverted=True) == "danger"
    assert bars.threshold_level(95, inverted=True) == ""


# ── 坐标系 ────────────────────────────────────────────────────────────────
def test_multi_series_share_one_scale():
    canvases = plots.multi_series([[0, 0, 0], [100, 100, 100]], 8, 2, lo=0, hi=100)
    lit = [sum(ch != "⠀" for ch in "".join(c.rows_text())) for c in canvases]
    assert lit[0] and lit[1]
    top_row_flat = canvases[1].rows_text()[0]
    assert top_row_flat != "⠀" * 8, "满值的那条该贴顶"


def test_scatter_places_extremes_at_the_corners():
    canvas = plots.scatter([(0.0, 0.0), (1.0, 1.0)], 4, 2,
                           x=plots.Axis(0, 1), y=plots.Axis(0, 1))
    rows = canvas.rows_text()
    assert rows[0][-1] != "⠀", "最大值应在右上"
    assert rows[-1][0] != "⠀", "最小值应在左下"


def test_scatter_survives_degenerate_axes():
    canvas = plots.scatter([(5.0, 5.0)] * 3, 4, 2)
    assert len(canvas.rows_text()) == 2


# ── 火焰图 ────────────────────────────────────────────────────────────────
def _frames():
    return [
        plots.Frame("main", 100, 0, 0),
        plots.Frame("parse", 60, 1, 0),
        plots.Frame("emit", 40, 1, 60),
        plots.Frame("tiny", 0.2, 2, 0),
    ]


def test_flame_groups_by_depth():
    rows = plots.flame(_frames(), 100)
    assert len(rows) >= 2
    assert [f.name for f, _, _ in rows[0]] == ["main"]
    assert {f.name for f, _, _ in rows[1]} == {"parse", "emit"}


def test_flame_drops_frames_too_narrow_to_draw_rather_than_inflating_them():
    """给窄帧兜底成 1 格会让它们集体虚胖，把宽帧挤走，图就假了。"""
    rows = plots.flame(_frames(), 40)
    names = {f.name for row in rows for f, _, _ in row}
    assert "tiny" not in names
    assert plots.dropped_frames(_frames(), 40) == 1


def test_flame_widths_stay_within_the_canvas():
    for width in (10, 40, 100, 200):
        for row in plots.flame(_frames(), width):
            for _, start, cells in row:
                assert 0 <= start and start + cells <= width


# ── Timeline ──────────────────────────────────────────────────────────────
def test_timeline_keeps_first_seen_lane_order():
    """按字母排会把 CPU / NPU / HBM 打散，而"谁在等谁"要靠相邻行看出来。"""
    spans = [
        plots.Span("NPU", 0, 5),
        plots.Span("CPU", 1, 3),
        plots.Span("HBM", 2, 4),
    ]
    lanes = [lane for lane, _ in plots.timeline(spans, 20)]
    assert lanes == ["NPU", "CPU", "HBM"]


def test_timeline_spans_never_collapse_to_zero_width():
    spans = [plots.Span("CPU", 0, 100), plots.Span("CPU", 50, 50.01)]
    for _, cells in plots.timeline(spans, 30):
        assert all(w >= 1 for _, _, w in cells)


# ── 像素数字 ──────────────────────────────────────────────────────────────
def test_big_digits_are_five_rows_and_distinguishable():
    rendered = {d: tuple(bignum.big(d)) for d in "0123456789"}
    assert all(len(v) == bignum.ROWS for v in rendered.values())
    assert len(set(rendered.values())) == 10, "十个数字必须两两不同"


def test_big_width_matches_the_declared_width():
    for text in ("0", "42", "12.5", "99%"):
        assert all(len(row) == bignum.width_of(text) for row in bignum.big(text))


def test_big_refuses_letters_instead_of_silently_dropping_them():
    """静默降级会把 "12.3GB" 渲染成 "12.3"——丢了单位的数字比没有数字更糟。"""
    with pytest.raises(UnsupportedGlyph, match="正文永不像素化"):
        bignum.big("12GB")


# ── 数图 ──────────────────────────────────────────────────────────────────
def test_stat_reads_improvement_against_the_metric_direction():
    faster = bignum.Stat("P99", 12, "ms", delta=-0.33, higher_is_better=False)
    assert faster.improved is True
    slower = bignum.Stat("QPS", 42, delta=-0.1, higher_is_better=True)
    assert slower.improved is False


def test_stat_without_a_baseline_draws_no_conclusion():
    """没有基线就不下结论——这是 tile 上唯一该出现语义色的地方。"""
    assert bignum.Stat("QPS", 61).improved is None
    assert bignum.Stat("QPS", 61, delta=0).improved is None


def test_stat_capacity_bar_only_when_there_is_a_capacity():
    assert bignum.Stat("Mem", 38.2).capacity_bar(10) == ""
    assert len(bignum.Stat("Mem", 38.2, capacity=64).capacity_bar(10)) == 10


def test_stat_value_text_trims_noise_zeros():
    assert bignum.Stat("x", 61.0).value_text() == "61"
    assert bignum.Stat("x", 12.5).value_text() == "12.5"


# ── 按单元格宽度对齐 ──────────────────────────────────────────────────────
from devkitai.render import text as rtext  # noqa: E402
from rich.cells import cell_len  # noqa: E402


@pytest.mark.parametrize("label", ["折线", "Sparkline", "泳道 CPU", "像素数字", "a"])
def test_fit_produces_exact_cell_width(label):
    """f"{s:<12}" 数的是码位，终端排的是单元格——混用两种标签列就歪了。"""
    assert cell_len(rtext.fit(label, 12)) == 12


def test_naive_ljust_would_have_been_wrong_for_cjk():
    """这条断言是为了证明上面那个测试不是白测的。"""
    assert cell_len("折线".ljust(12)) == 14
    assert cell_len(rtext.fit("折线", 12)) == 12


def test_truncate_never_splits_a_wide_character():
    """直接切片会在宽字符上切出半个格——终端渲染出来是错位而不是少一个字。"""
    out = rtext.truncate("鲲鹏迁移诊断调优", 7)
    assert cell_len(out) <= 7
    assert out.endswith("…")


def test_truncate_leaves_short_text_alone():
    assert rtext.truncate("abc", 10) == "abc"


def test_pad_does_not_truncate():
    """补齐和截断是两件事，混在一起调用方会分不清拿到的是哪一种。"""
    assert rtext.pad("abcdefghij", 3) == "abcdefghij"


def test_pad_alignment_modes():
    assert rtext.pad("x", 5) == "x    "
    assert rtext.pad("x", 5, align="right") == "    x"
    assert rtext.pad("x", 5, align="center") == "  x  "
