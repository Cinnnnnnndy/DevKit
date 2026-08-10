"""纯渲染层：不依赖 Textual，可单独测试、可单独复用。

把"怎么把数值变成字符和颜色"和"怎么把它挂进 UI 树"分开，是为了让
**降级行为是确定的、可测的**——终端能力探测的每一条分支都能在测试里覆盖，
不需要真的去开一个 SSH 会话。

图元清单（对应 ``docs/COMPONENT.md`` §3）：

    条形族   bars.bar · ranking · grouped · before_after · segmented
    水位     bars.water_level                   竖槽，"还剩多少"
    进度     bars.progress · spinner            未知进度不画假进度条
    曲线     braille.plot_series · plots.multi_series
    面积     braille.plot_series(area=True) · braille.mirrored
    散点     plots.scatter
    火焰图   plots.flame                        过窄的帧宁可不画
    泳道     plots.timeline
    热力     blocks.heat_glyph + ramp.sequential
    数字     bignum.big                         仅数字，正文永不像素化
    数图     bignum.Stat                        值 + 变化 + 走势
"""

from .bars import (
    HBAR,
    VBAR,
    RankRow,
    bar,
    before_after,
    grouped,
    progress,
    ranking,
    segmented,
    spinner,
    threshold_level,
    water_level,
)
from .bignum import Stat, UnsupportedGlyph, big, width_of
from .blocks import gauge, half_block_column, heat_glyph, sparkline
from .braille import BrailleCanvas, mirrored, plot_series
from .plots import Axis, Frame, Span, dropped_frames, flame, multi_series, scatter, timeline
from .ramp import ColorDisciplineError, categorical, grayscale, sequential
from .text import fit, pad, truncate

__all__ = [
    # 画布
    "BrailleCanvas",
    "plot_series",
    "mirrored",
    # 条形族
    "HBAR",
    "VBAR",
    "bar",
    "ranking",
    "RankRow",
    "grouped",
    "before_after",
    "segmented",
    "water_level",
    "gauge",
    # 进度
    "progress",
    "spinner",
    # 坐标系
    "Axis",
    "multi_series",
    "scatter",
    "flame",
    "Frame",
    "dropped_frames",
    "timeline",
    "Span",
    # 块字符
    "sparkline",
    "heat_glyph",
    "half_block_column",
    # 数字 / 数图
    "big",
    "width_of",
    "Stat",
    "UnsupportedGlyph",
    # 色阶与纪律
    "sequential",
    "categorical",
    "grayscale",
    "threshold_level",
    "ColorDisciplineError",
    # 按显示宽度对齐（禁用裸 ljust/rjust）
    "fit",
    "pad",
    "truncate",
]
