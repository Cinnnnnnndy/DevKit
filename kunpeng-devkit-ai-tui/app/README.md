# devkitai · 渲染底座 + Chrome 层外壳

> Kunpeng DevKit AI 原生 TUI 的第一段实现。当前有**渲染底座**与**Chrome 层外壳**，没有 Agent Runtime、没有 MCP 客户端、没有业务逻辑。

按 [`../docs/TUI-CAPABILITY.md`](../docs/TUI-CAPABILITY.md) §6 的结论：最有价值的 pattern（P21 Live Canvas、P26 AI 标注层、多核热力）**全部依赖渲染底座**，所以先跑通三个原语再往上叠场景。反过来做——先出业务 Demo 再补渲染——大概率退化成"带框线的 CLI"。

## 跑起来

```bash
pip install -e '.[dev]'
python -m devkitai            # 工作台外壳
python -m devkitai preview    # 组件预览页
pytest                        # 114 个测试
```

预览页可以**现场切换渲染层**，因为降级路径写在文档里没人会去验，能按一下就看到的才会：

```bash
DEVKITAI_NO_BRAILLE=1 python -m devkitai   # T2 → T1：曲线变 sparkline
NO_COLOR=1            python -m devkitai   # T3 → T1：热力变灰阶 + ░▒▓█
TERM=dumb             python -m devkitai   # 一路压到 T0 兼容底线
```

页面里按 `t` 也能在原生能力与两档降级之间循环。

## 结构

```
devkitai/
├── tokens.py          PTO → TUI token 直译，VISUAL.md 的可执行版本
├── tiers.py           终端能力探测 + T0–T5 降级链
├── layout.py          折叠降级链：宽度 → 布局判决（纯函数）
├── spec.py            组件评审门槛（ComponentSpec）
├── shell.py           工作台外壳，Dock 从顶通到底
├── render/            纯渲染层，不依赖 Textual
│   ├── braille.py     T2 · 2×4 点阵画布
│   ├── blocks.py      T1 · 块字符 / 半块 / 象限
│   └── ramp.py        色阶取值 + 用色纪律的运行期护栏
├── widgets/
│   ├── dock.py            Dock：竖标签条 + 面板 + ⇄ 跟随 · Chrome
│   ├── chrome.py          TabBar / 输入框 / keybar / 状态栏 · Chrome
│   ├── braille_chart.py   Braille 历史曲线 · Canvas · T2
│   ├── core_heatmap.py    多核热力网格 + NUMA + AI 标注层 · Canvas · T3
│   └── kernel_table.py    可排序 / 可筛选算子表 · Canvas · T4
├── theme/
│   ├── __init__.py    从 tokens.py 生成 Textual Theme 与 $pto-* 变量
│   └── pto.tcss       样式表，**不含任何十六进制字面量**
└── preview.py         组件预览页（VISUAL.md §6 要求的 preview gate）
```

## 三条把规范变成代码的做法

**纯渲染层与组件层分开。** `render/` 不 import Textual，所以"值怎么变成字符和颜色"可以单独测——降级行为的每一条分支都在 `tests/test_tiers.py` 里覆盖，不需要真去开一个 SSH 会话验证。

**用色纪律做成运行期护栏，不靠自觉。** `ramp.assert_block_color()` 把语义色传进色阶函数时直接抛 `ColorDisciplineError`。因为 warning 35° 与 accum-orange 25° 色相本来就近，终端里最终是靠**字形**区分的——把语义色画进色块会毁掉这层区分，而且渲染出来看不出问题。

**评审门槛做成测试。** VISUAL.md §6 要求每个组件声明"渲染层 · 降级路径 · 键盘等价 · 用到的 token"。写在文档里的门槛会被绕过，写成 `ComponentSpec` 加一个遍历所有组件的测试就不会——漏声明是测试失败，不是评审时才发现。

## 实现过程中撞到的三个坑

**含中文的字符串不能用 `len()` 算宽度。** 底栏"当前 / 峰值"每个汉字占 2 格，用 `len()` 算出来的边框短 4 格，整行折行。全部改用 `rich.cells.cell_len`。**这类 bug 只在中文标签下出现，纯英文界面上测不出来**，所以 `tests/test_widgets.py` 里那条断言特意加了一句 `assert cell_len(s) != len(s)`——保证它真的踩在 CJK 上。

**AI 标注层不能插在单元格后面。** 第一版把角标追加在被标注核的后面，结果每多一个标注那行就往右挤一格，NUMA 条跟着错位。热力网格靠的就是**位置承载拓扑**，一错位这张图就废了。标注是独立图层，所以它也占独立的一行：数据网格一个字符不动，标记在下方对齐。

**多行 Rich renderable 不要靠 `height: auto`。** auto 要先渲染一次才知道多高，而组件的渲染宽度又依赖最终布局，一来一回会多留出几行空白。高度直接写成 `rows + 2`。

## Chrome 层 vs Canvas 层

这条分界线是整套设计里最要紧的一条，所以在目录结构上也是分开的：

| 层 | 谁 | 为什么 |
|---|---|---|
| **Chrome**（结构） | Dock · TabBar · 输入框 · keybar · 状态栏 | 用户在这里做的是选择 / 导航 / 切换 / 确认，所以必须有 hover / selected / focus / disabled 四态。**字符拼不出"我现在选中的是哪一项"** |
| **Canvas**（读数） | Braille 曲线 · 热力网格 · 算子表 | 用户在这里做的是看数值 / 比大小 / 找异常，需要的是密度与对齐。64 核热力如果用 64 个 widget，密度、对齐、性能全都做不到 |

外壳结构按「左栏要从顶通到底」：Dock 从顶端一直通到状态栏，品牌标识进 Dock 头部，tab 带缩回主区。结果是**一条垂直分割贯穿全屏、一条水平分割横贯全屏，两条线各只出现一次**。全宽的只有 keybar 与状态栏——判据是「切换页签会变的东西归页签，不变的归窗口」。

## 还没做

- Agent Runtime 与 MCP 客户端（`:8000` streamableHttp）
- 命令面板（P09）——Textual 内置，接上即可
- Canvas 之间的 P22 联动：`Dock.follow()` 有了，反向（点 Canvas 定位到树）还没有
- T5 图形协议路径：能力探测有了，光栅渲染没有
- 双向面积图与 Trace 密度带（`render/braille.py` 里的 `mirrored()` 已就绪，缺组件封装）
