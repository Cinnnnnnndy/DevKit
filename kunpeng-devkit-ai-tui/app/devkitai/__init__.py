"""Kunpeng DevKit AI —— 原生 TUI 工作台。

当前进度：**Phase 0 渲染底座**。按 ``docs/TUI-CAPABILITY.md`` §6 的结论，
最有价值的 pattern（P21 Live Canvas、P26 AI 标注层、多核热力）全部依赖渲染
底座，所以先跑通三个原语再往上叠场景——反过来做大概率退化成"带框线的 CLI"。

已落地：Braille 曲线（T2）· 多核热力网格（T3）· 可排序表（T4）· PTO token
与 TCSS 变量文件 · 终端能力探测与 T0–T5 降级链。
未落地：Agent Runtime、MCP 客户端、业务场景。
"""

__version__ = "0.1.0"

from .spec import ComponentSpec
from .tiers import Capabilities, Tier, detect, resolve

__all__ = ["Capabilities", "ComponentSpec", "Tier", "detect", "resolve", "__version__"]
