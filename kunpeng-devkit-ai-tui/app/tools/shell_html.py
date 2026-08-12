"""把真实运行的 TUI 导成 ``<pre>`` 标记，替代原先的 SVG 截图。

    python -m tools.shell_html shell        # 工作台外壳
    python -m tools.shell_html degradation  # 降级路径三档并排

**为什么不再导 SVG。** Textual 的 ``save_screenshot()`` 输出矢量 SVG，每个
字符按"一个单元格"推进 x 坐标，而终端里一个汉字占 2 格。浏览器不吃这套：
CJK 字形的实际步进由字体决定，于是中文标注一律叠在一起。除此之外 SVG 还有
三个跑不掉的毛病——**选不中、复制不了、行高不可调**，而这份设计规范恰恰
在讲行高和字符对齐，用一张选不中的图去讲它是自相矛盾的。

改成 ``<pre>`` 之后由浏览器自己排字：文字可以选中复制，行距归页面的
``--row`` 管，宽度由 ``tools.fix_charart`` 掰正。而且**更小**——两张 SVG 合计
179 KB，换成标记之后不到一半。

导出的仍然是**程序跑出来的**那一份：这里走的是 Textual 自己 ``export_screenshot``
的同一条路（合成器渲染 → Rich Console），只是把出口从 ``export_svg()``
换成 ``export_html()``，颜色仍是运行时真正算出来的那一个。
"""

from __future__ import annotations

import asyncio
import io
import math
import os
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from rich.console import Console  # noqa: E402
from rich.terminal_theme import TerminalTheme  # noqa: E402

from devkitai.tiers import Capabilities  # noqa: E402
from tools.fix_charart import wrap_widths  # noqa: E402

# 终端能力的三个档位，用来并排展示降级。刻意不靠环境变量——直接构造
# Capabilities 更明确，也不会因为跑脚本的那台机器碰巧支持什么而变。
FULL = Capabilities(truecolor=True, braille=True, mouse=True, graphics=False)
NO_BRAILLE = Capabilities(truecolor=True, braille=False, mouse=True, graphics=False)
PLAIN = Capabilities(truecolor=False, braille=False, mouse=False, graphics=False)

#: 导出用的终端配色。前景 / 背景取 PTO 的 background 与 fg，其余十六色用不到——
#: 组件全部走真彩，落到这张表上的只有默认前景。
THEME = TerminalTheme(
    (16, 16, 16), (231, 231, 231),
    [(0, 0, 0)] * 8, [(255, 255, 255)] * 8,
)


#: 导出时假装成一台**能力齐全**的终端。``DevKitShell`` 在 on_mount 里调
#: :func:`devkitai.tiers.detect` 读环境变量，而 CI / 管道里既没有 ``TERM`` 也
#: 没有 ``COLORTERM``——``detect()`` 会一路压到 T1 灰阶（它就该这么保守）。
#: 结果是导出的图变成降级形态，而正文写着"T2 Braille"，图和文对不上。
#: **导出结果不该取决于跑它的那台机器**，所以这里显式钉死。
#: 必须在**建 app 之前**生效：``DevKitShell.__init__`` 就调了 ``detect()``，
#: 等到进 ``_render`` 再设已经晚了一步——那时能力已经探完并压到 T1 了。
EXPORT_ENV = {"TERM": "xterm-256color", "COLORTERM": "truecolor"}
os.environ.update(EXPORT_ENV)


async def _render(app, size: tuple[int, int]) -> str:
    """跑起来，抓当前屏，导成 HTML 片段。"""
    async with app.run_test(size=size) as pilot:
        # 必须等两帧。主题是在 on_mount 里注册的，它会触发一次整屏重绘——
        # 只等一帧的话截图赶在重绘之前，导出来是一张**空终端**：外框、标题栏
        # 都在，格子里一个字都没有。这种失败不会报错，只会安静地产出废图。
        await pilot.pause()
        await pilot.pause()
        console = Console(
            width=size[0], height=size[1], file=io.StringIO(),
            force_terminal=True, color_system="truecolor",
            record=True, legacy_windows=False, safe_box=False,
        )
        console.print(
            app.screen._compositor.render_update(
                full=True, screen_stack=app.app._background_screens, simplify=True
            )
        )
        return console.export_html(theme=THEME, code_format="{code}", inline_styles=True)


def _tidy(html: str) -> str:
    """收拾 Rich 的输出：去掉外壳、压掉纯色噪声、补上宽度修正。"""
    html = re.sub(r"</?pre[^>]*>|</?code[^>]*>", "", html).strip("\n")
    # Rich 给每一段都写 text-decoration-color，画面上看不出任何差别，纯占字节
    html = re.sub(r"\s*text-decoration-color: #[0-9a-fA-F]{6};?", "", html)
    # 和 pre.dense 自己的底色（surface-1）同色的背景没有意义；#101010 是应用底
    html = re.sub(r"\s*background-color: #(161616|101010);?", "", html)
    html = re.sub(r'style="\s*;?\s*', 'style="', html)
    html = re.sub(r';?\s*"', '"', html)
    # 只剩空 style 的 span，以及整段空白的 span，都拆掉
    html = re.sub(r'<span style="">(.*?)</span>', r"\1", html)
    html = re.sub(r'<span style="[^"]*">(\s*)</span>', r"\1", html)
    return wrap_widths(html)


#: (标题, 终端尺寸, 行距档位)。行距判据和 gallery_html.py 一致——多行拼成
#: 一张图（braille 曲线）用 tight，一行一条独立数据（热力网格每行一组核）
#: 用 chart，纯框线/文字表格用默认的 20px。
TARGETS: dict[str, tuple[str, tuple[int, int], str]] = {
    "shell": ("工作台外壳实况", (160, 44), "tight"),
    "degradation": ("降级路径三档并排", (150, 18), "tight"),
    "prim-braille": ("Braille 历史曲线单例", (62, 8), "tight"),
    "prim-heatmap": ("多核热力网格单例", (52, 10), "chart"),
    "prim-kernels": ("可排序算子表单例", (70, 10), ""),
}


def _shell_app():
    from devkitai.shell import DevKitShell

    return DevKitShell()


def _single_widget_app(build, populate=None):
    """裹一个最小的 App，只挂一个组件——给 docs/COMPONENT.md「原语画法示例」
    那节用。原来那节是手画的 ``┌cpu──kunpeng920─┐``，热力网格那个例子手画时
    漏画了边框，且这类手宽算术正是全篇一直在防的那类 bug——干脆不再手画，
    单个组件也走真实渲染。

    ``populate`` 在挂载**之后**再灌数据——KernelTable 的 ``set_rows()`` 内部
    靠 ``is_mounted`` 短路，挂载前调了也是白调。
    """
    from textual.app import App, ComposeResult

    class _Single(App):
        CSS_PATH = "../devkitai/theme/pto.tcss"

        def get_theme_variable_defaults(self):
            from devkitai.theme import pto_variables

            return pto_variables()

        def compose(self) -> ComposeResult:
            yield build()

        def on_mount(self) -> None:
            from devkitai.theme import pto_theme

            self.register_theme(pto_theme())
            self.theme = "pto"
            if populate is not None:
                populate(self.query_one(build.widget_type))

    return _Single()


def _prim_braille_app():
    from devkitai.widgets import BrailleChart

    def build():
        return BrailleChart("cpu · kunpeng-920", "cpu", rows=3, caps=FULL)

    build.widget_type = BrailleChart

    def populate(chart):
        chart.extend([50 + 42 * math.sin(i / 9) for i in range(120)])

    return _single_widget_app(build, populate)


def _prim_heatmap_app():
    from devkitai.widgets import Annotation, CoreHeatmap

    def build():
        return CoreHeatmap(64, 16, caps=FULL)

    build.widget_type = CoreHeatmap

    def populate(heat):
        heat.update_utilisation([abs(50 + 45 * math.sin(i / 5.5)) % 100 for i in range(64)])
        heat.annotate([Annotation(tuple(range(34, 39)), "warning", "疑似跨 NUMA 内存访问")])

    return _single_widget_app(build, populate)


def _prim_kernels_app():
    from devkitai.widgets import Column, KernelTable

    columns = (
        Column("name", "Kernel", width=18),
        Column("calls", "Calls", width=8, numeric=True),
        Column("avg_ms", "Avg", width=9, numeric=True, fmt=lambda v: f"{v:.1f}ms"),
        Column("total_s", "Total", width=18, bar_domain="npu", fmt=lambda v: f"{v:.1f}s"),
    )
    rows = [
        {"name": "attention_fwd", "calls": 1024, "avg_ms": 18.2, "total_s": 18.6},
        {"name": "matmul_4096", "calls": 512, "avg_ms": 12.4, "total_s": 6.3},
        {"name": "layernorm", "calls": 2048, "avg_ms": 1.8, "total_s": 3.7},
    ]

    def build():
        return KernelTable(columns, title="kernels")

    build.widget_type = KernelTable

    def populate(table):
        table.set_rows(rows)
        table.sort_by("total_s")

    return _single_widget_app(build, populate)


def _degradation_app():
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal
    from textual.widgets import Static

    from devkitai.widgets import Annotation, BrailleChart, CoreHeatmap

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
                for caps, label in ((FULL, "T3 真彩热力"), (PLAIN, "T1 灰阶 + 字形梯度")):
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

    return Degradation()


BUILDERS = {
    "shell": _shell_app,
    "degradation": _degradation_app,
    "prim-braille": _prim_braille_app,
    "prim-heatmap": _prim_heatmap_app,
    "prim-kernels": _prim_kernels_app,
}


async def main(name: str) -> None:
    title, size, density = TARGETS[name]
    body = await _render(BUILDERS[name](), size)
    cls = f"dense {density}".rstrip()
    print(f'<pre class="{cls}" aria-label="{title}">{_tidy(body)}</pre>')


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in TARGETS:
        print(f"用法：python -m tools.shell_html {{{'|'.join(TARGETS)}}}", file=sys.stderr)
        raise SystemExit(2)
    asyncio.run(main(sys.argv[1]))
