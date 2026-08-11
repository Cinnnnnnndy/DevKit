"""把真实运行的 TUI 导出成 SVG，供网页嵌入。

    python tools/screenshots.py

**这些图不是重画的 mockup，是程序跑起来之后的真实输出。** Textual 的
``save_screenshot()`` 导出矢量 SVG——每个字符仍然是文本，颜色是运行时真正
算出来的那一个，所以网页上看到的和终端里看到的是同一份渲染结果。

这件事值得单独做一个脚本，而不是手工截图，原因有两条：

* **会漂。** 手工截图一旦落地就和代码脱钩，改了组件不改图，图就开始撒谎。
  脚本化之后重跑一次就全同步了。
* **降级路径需要并排看。** 同一个组件在 T2 / T1 / T0 下长什么样，是这套
  设计里最需要被看到、也最难用文字讲清的东西——三张并排一放就不用讲了。
"""

from __future__ import annotations

import asyncio
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from devkitai.tiers import Capabilities  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[3] / "kunpeng-devkit-ai-tui/web/assets/tui"

# 终端能力的三个档位，用来并排展示降级。刻意不靠环境变量——直接构造
# Capabilities 更明确，也不会因为跑脚本的那台机器碰巧支持什么而变。
FULL = Capabilities(truecolor=True, braille=True, mouse=True, graphics=False)
NO_BRAILLE = Capabilities(truecolor=True, braille=False, mouse=True, graphics=False)
PLAIN = Capabilities(truecolor=False, braille=False, mouse=False, graphics=False)


async def shot(app, path: pathlib.Path, size: tuple[int, int]) -> None:
    async with app.run_test(size=size) as pilot:
        # 必须等两帧。主题是在 on_mount 里注册的，它会触发一次整屏重绘——
        # 只等一帧的话截图赶在重绘之前，导出来是一张**空终端**：外框、标题栏
        # 都在，格子里一个字都没有。这种失败不会报错，只会安静地产出废图。
        await pilot.pause()
        await pilot.pause()
        app.save_screenshot(str(path))
    # Textual 只写 viewBox，不写 width/height。作为 <img> 引用时浏览器就拿不到
    # 固有尺寸，height:auto 算出来是 0——图在页面上完全看不见，且不报错。
    _add_intrinsic_size(path)
    print(f"  {path.name:<22} {path.stat().st_size // 1024:>4} KB  {size[0]}×{size[1]}")


def _add_intrinsic_size(path: pathlib.Path) -> None:
    """从 viewBox 补出 width / height，让 <img> 能算出固有尺寸。"""
    import re

    svg = path.read_text(encoding="utf-8")
    if re.search(r'<svg[^>]*\swidth=', svg):
        return
    m = re.search(r'<svg[^>]*viewBox="0 0 ([\d.]+) ([\d.]+)"', svg)
    if not m:
        return
    path.write_text(
        svg.replace('<svg class="rich-terminal"',
                    f'<svg class="rich-terminal" width="{m.group(1)}" height="{m.group(2)}"', 1),
        encoding="utf-8")


async def main() -> None:
    from devkitai.gallery import GalleryApp
    from devkitai.shell import DevKitShell
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal
    from textual.widgets import Static

    from devkitai.widgets import Annotation, BrailleChart, CoreHeatmap

    OUT.mkdir(parents=True, exist_ok=True)
    print(f"导出到 {OUT}")

    await shot(DevKitShell(), OUT / "shell.svg", (160, 44))
    await shot(GalleryApp(), OUT / "gallery.svg", (100, 82))

    class Degradation(App):
        """同一份数据、同一个组件，在三档终端能力下并排。"""

        CSS_PATH = "../devkitai/theme/pto.tcss"
        CSS = """
        Horizontal { height: auto; }
        .col { width: 1fr; padding: 0 1; }
        .cap { height: 1; color: $pto-fg-muted; }
        """

        def get_theme_variable_defaults(self):
            from devkitai.theme import pto_variables

            return pto_variables()

        def compose(self) -> ComposeResult:
            with Horizontal():
                for caps, label in ((FULL, "T2 Braille · 原生"),
                                    (NO_BRAILLE, "T1 块字符 · 缺 Braille 字形"),
                                    (PLAIN, "T0 文本 · NO_COLOR / dumb")):
                    with Horizontal(classes="col"):
                        yield BrailleChart(label, "cpu", rows=3, caps=caps)
            with Horizontal():
                for caps, label in ((FULL, "T3 真彩热力"),
                                    (PLAIN, "T1 灰阶 + 字形梯度")):
                    with Horizontal(classes="col"):
                        yield CoreHeatmap(32, 16, caps=caps)
            yield Static("", classes="cap")

        def on_mount(self) -> None:
            from devkitai.theme import pto_theme

            self.register_theme(pto_theme())
            self.theme = "pto"
            data = [50 + 42 * math.sin(i / 9) for i in range(160)]
            for chart in self.query(BrailleChart):
                chart.extend(data)
            util = [abs(50 + 45 * math.sin(i / 5.5)) % 100 for i in range(32)]
            for heat in self.query(CoreHeatmap):
                heat.update_utilisation(util)
                heat.annotate([Annotation((18, 19, 20), "warning", "疑似跨 NUMA 访问")])

    await shot(Degradation(), OUT / "degradation.svg", (150, 18))


if __name__ == "__main__":
    asyncio.run(main())
