# tools —— 字符帧与页面生成器

设计页里的整屏字符帧不手写。160 列的帧一行错半格，肉眼要逐行比对才看得出来，
所以这里把排版和校验都交给程序。

| 文件 | 作用 |
|---|---|
| `screens.py` | 排版底座：单元格宽度计算、分栏、外框、块字符 wordmark、八分之一格 bar、着色标记 → HTML |
| `gen_screens.py` | 生成 [`../web/screens.html`](../web/screens.html) —— 五个典型页面，每屏 160 列宽屏帧 + 80 列窄屏帧 |
| `gen_design_input.py` | 生成 [`../web/design-input.html`](../web/design-input.html) —— 设计输入评审版单页 |
| `page_css.py` | 两份生成页共用的页面外壳样式（token 照抄 `web/index.html`） |
| `check_frames.py` | 在 headless Chromium 里逐行复核渲染宽度 |
| `kpmark.py` | Kunpeng 标识处理 |

```bash
cd kunpeng-devkit-ai-tui/tools
python3 gen_screens.py          # 重新生成四屏
python3 gen_design_input.py     # 重新生成设计输入页
python3 check_frames.py         # 门禁：真浏览器里复核逐行宽度
```

## 两套宽度账，都得对

**① 终端单元格账**：CJK 占 2 格、Braille 占 1 格、框线占 1 格。
`screens.py` 的 `check()` 在渲染前断言每块每行等宽，对不上直接退出。

**② 浏览器渲染账**：等宽字体只保证它自己覆盖的字符等宽。CJK、Braille、`⏸`
都要回退到别的字体，而回退字体的步进不由我们决定——实测 Chromium/Linux 下
Braille 是 1.217 格、`⏸` 是 0.830 格，换个字体就换一个值。

两类分开治：

- **CJK** 包 `.fw`（`font-size:2ch`）。汉字是 1 em 方块，2ch 字号后必然是 2 格，
  这一类靠字号可靠。
- **Braille 与 `⏸` 族**包 `.hw`（`display:inline-block;width:1ch`）。它们的步进因
  字体而异，调字号治不了，只能把宽度硬钉成一格。

`check_frames.py` 负责验第二套账：跑一次 headless Chromium，量出每个
`pre[data-check]` 每一行的实测宽度，与该块众数比较，超过半格就非 0 退出。
自由排版的流程图不打 `data-check`——拿等宽去要求它们只会天天报假警。

装饰性字形（如原先的 `⬡`）遇到宽度不稳时直接换掉，不为一个装饰去加特例。

## 着色标记

帧用 `⟦cls|text⟧` 标着色，`cls` 直接是 `web/index.html` 里 `pre` 的既有 class：

```
ok / wn / er / pr / cm / ac / t / br / sel / s2
o3–o8（accum-orange）· g3–g8（ub-green）· v3–v8（violet）· a3–a8（amber）
```

不新造调色板。数据走色阶、结论走语义色的纪律见
[`../docs/VISUAL.md`](../docs/VISUAL.md) 与设计系统页的 Colors 一节。
