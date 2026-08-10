"""Chrome 层与 Canvas 层的组件。

每个组件都必须挂一个 :class:`devkitai.spec.ComponentSpec`——所属渲染层、
降级路径、键盘等价操作、用到的 token 四件事缺一不可（VISUAL.md §6）。
``tests/test_spec.py`` 会遍历这里的 ``__all__`` 强制检查。

    Chrome 层（结构 · 真组件）   Dock · TabBar · PromptInput · KeyBar · StatusBar
    Canvas 层（读数 · 字符网格） BrailleChart · CoreHeatmap · KernelTable
"""

from .braille_chart import BrailleChart
from .chrome import KeyBar, PromptInput, StatusBar, TabBar, Task
from .core_heatmap import Annotation, CoreHeatmap
from .dock import Dock, DockItem, DockPanel, default_panels
from .kernel_table import Column, KernelTable

__all__ = [
    # Chrome 层
    "Dock",
    "TabBar",
    "PromptInput",
    "KeyBar",
    "StatusBar",
    # Canvas 层
    "BrailleChart",
    "CoreHeatmap",
    "KernelTable",
    # 数据类型
    "Annotation",
    "Column",
    "DockItem",
    "DockPanel",
    "Task",
    "default_panels",
]
