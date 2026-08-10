"""Chrome 层与 Canvas 层的组件。

每个组件都必须挂一个 :class:`devkitai.spec.ComponentSpec`——所属渲染层、
降级路径、键盘等价操作、用到的 token 四件事缺一不可（VISUAL.md §6）。
``tests/test_spec.py`` 会遍历这里的 ``__all__`` 强制检查。
"""

from .braille_chart import BrailleChart
from .core_heatmap import Annotation, CoreHeatmap
from .kernel_table import Column, KernelTable

__all__ = ["BrailleChart", "CoreHeatmap", "KernelTable", "Annotation", "Column"]
