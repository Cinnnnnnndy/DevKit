"""纯渲染层：不依赖 Textual，可单独测试、可单独复用。

把"怎么把数值变成字符和颜色"和"怎么把它挂进 UI 树"分开，是为了让
**降级行为是确定的、可测的**——终端能力探测的每一条分支都能在测试里覆盖，
不需要真的去开一个 SSH 会话。
"""

from .blocks import gauge, half_block_column, heat_glyph, segmented, sparkline
from .braille import BrailleCanvas, mirrored, plot_series
from .ramp import ColorDisciplineError, categorical, grayscale, sequential

__all__ = [
    "BrailleCanvas",
    "ColorDisciplineError",
    "categorical",
    "gauge",
    "grayscale",
    "half_block_column",
    "heat_glyph",
    "mirrored",
    "plot_series",
    "segmented",
    "sparkline",
    "sequential",
]
