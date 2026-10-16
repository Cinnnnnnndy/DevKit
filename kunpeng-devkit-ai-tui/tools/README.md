# tools —— 字符帧与页面生成器

设计页里的整屏字符帧不手写。160 列的帧一行错半格，肉眼要逐行比对才看得出来，
所以这里把排版和校验都交给程序。

| 文件 | 作用 |
|---|---|
| `screens.py` | 排版底座：单元格宽度计算、分栏、外框、块字符 wordmark、八分之一格 bar、着色标记 → HTML；`cell_class()` 是「一个字形该用哪个盒子」的唯一判据 |
| `gen_screens.py` | 生成 [`../web/screens.html`](../web/screens.html) —— 五个典型页面，每屏 160 列宽屏帧 + 80 列窄屏帧 |
| `gen_design_input.py` | 生成 [`../web/design-input.html`](../web/design-input.html) —— 设计输入评审版单页 |
| `page_css.py` | 两份生成页共用的页面外壳样式（token 照抄 `web/index.html`） |
| `wrap_frames.py` | 给**手写**页面里的字符帧补单元格盒子与 `data-cols`（幂等，可反复跑） |
| `check_frames.py` | 门禁：在真浏览器里逐行复核渲染宽度 + 逐字复核字形步进 |
| `kpmark.py` | Kunpeng 标识处理 |

```bash
cd kunpeng-devkit-ai-tui/tools
python3 gen_screens.py          # 重新生成五屏
python3 gen_design_input.py     # 重新生成设计输入页
python3 wrap_frames.py ../web/interaction-spec.html ../web/index.html   # 手写页对齐
python3 check_frames.py         # 门禁：真浏览器里复核行宽与字形步进
```

生成的页面在生成那一刻就把盒子封好了；手写页（`interaction-spec.html`、`index.html`）
必须过一遍 `wrap_frames.py`，否则汉字按 1.667 格、全角标点按 0.5 格渲染，框线右边缘
整片歪掉——而这恰恰是最难用眼睛发现的那类错。

## 两套宽度账，都得对

**① 终端单元格账**：CJK 占 2 格、Braille 占 1 格、框线占 1 格。
`screens.py` 的 `check()` 在渲染前断言每块每行等宽，对不上直接退出。

**② 浏览器渲染账**：等宽字体只保证它自己覆盖的字符等宽。CJK、Braille、`⏸`、全角标点
都要回退到别的字体，而回退字体的步进不由我们决定——实测 macOS/Menlo 下汉字 1.667 格、
Braille 1.139 格、`⏸` 1.050 格、`⧉` 1.327 格、`，` 0.508 格，换个字体就换一个值。

按**失效原因**分三类治，判据写在 `screens.py:cell_class()` 一处：

| 类 | 字形 | 失效原因 | 治法 |
|---|---|---|---|
| `.fw` | 汉字（1 em 方块） | 步进 = 字号 | `font-size:2ch` → 恰好 2 格，一个 span 罩一串 |
| `.fw2` | 全角标点 `，。：「」（）【】；` | 字体只画半个字宽，字号法失效（`.fw` 下也只有 1.016 格） | `width:2ch` 硬钉 2 格，**逐字符**一个盒子 |
| `.hw` | Braille、`⏸⏵⏹⏺`、`①②③④⑤`、`⟳ ⧉ ⬡ ✎ ↵` | 等宽字体不覆盖，步进随回退字体漂 | `width:1ch` 硬钉 1 格，**逐字符**一个盒子 |

后两类必须逐字符封盒，否则 N 个字形挤在一个盒子里。这三条规则在
`tools/page_css.py`、`web/index.html`、`web/interaction-spec.html` 各有一份——
**改一处要三处一起改**，`check_frames.py` 会在真浏览器里量出来点名。

### 维护 `NARROW_GLYPHS`（一个闭环）

`screens.py` 的 `NARROW_GLYPHS` 不是靠人记的清单。`check_frames.py` 会量每个 `pre` 里
出现的**每一个**非 ASCII 字符，按它在页面里实际使用的写法（裸 / `.fw` / `.fw2` / `.hw`）
报出实测步进，与 `char_width()` 对不上就点名并告诉你改哪里。流程是：

1. 跑 `check_frames.py`，把点名的字形加进 `NARROW_GLYPHS`（生成器随即自动用 `.hw` 钉住）；
2. 重跑生成器 / `wrap_frames.py`；
3. 再跑门禁，转绿就说明清单齐了。

`check_frames.py` 的覆盖范围与判据：

- **逐行**：`pre[data-check]` 每行实测宽度须与该块众数一致（半格容差）；带
  `data-cols="160"` 的还要等于声明的列数——这一条抓「某一行多了一格」。
  自由排版与片段式的字符画不打 `data-check`，拿等宽去要求它们只会天天报假警。
- **逐字**：每个 `pre` 的每个非 ASCII 字形按实际写法量步进，须等于 `char_width()`。
- 浏览器查找顺序：`$CHROME` → macOS 的 Google Chrome → Playwright 预装 Chromium →
  PATH 上的 chromium/chrome；找不到就跳过并返回 0（没有浏览器的机器不该被门禁卡住）。

## 一个坑：CJK 脚本要写编码声明

`tools/*.py` 每个文件第 1–2 行都有 `# -*- coding: utf-8 -*-`，别删。CJK 内容多的脚本
用 `python3 tools/gen_screens.py` **直接执行**时，可能撞上 CPython 3.9 分词器在多字节
字符跨 8KB 读缓冲边界时的误判，报 `SyntaxError: Non-UTF-8 code starting with '\xe6'
... but no encoding declared`——而 `py_compile` / `compile()` 都正常，文件也确实是合法
UTF-8。加了编码声明就走不到那条路径。内容长度一变（添删几行）就可能复现，所以声明是
长期需要的，不是一次性的补丁。

## 着色标记

帧用 `⟦cls|text⟧` 标着色，`cls` 直接是 `web/index.html` 里 `pre` 的既有 class：

```
ok / wn / er / pr / cm / ac / t / br / sel / s2
o3–o8（accum-orange）· g3–g8（ub-green）· v3–v8（violet）· a3–a8（amber）
```

不新造调色板。数据走色阶、结论走语义色的纪律见
[`../docs/VISUAL.md`](../docs/VISUAL.md) 与设计系统页的 Colors 一节。
