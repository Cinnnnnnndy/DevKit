#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给手写的字符帧补齐单元格盒子（`.fw` / `.fw2` / `.hw`）与 `data-cols`。

生成的页面（screens.html / design-input.html）由 `screens.py` 在生成那一刻就把每个字形
的盒子封好了；手写的字符帧没有这层保护，于是汉字按 1.667 格、全角标点按 0.5 格渲染，
框线右边缘整片歪掉——而这恰恰是最难用眼睛发现的那类错。

这个工具把同一条规则套上去，规则只有一处（`screens.py:cell_class`）：

  汉字                 → `.fw`   字号 2ch，1 em 方块正好 2 格
  全角标点 / 全角符号   → `.fw2`  字体只画半宽，按宽度硬钉 2 格
  等宽字体不覆盖的字形  → `.hw`   按宽度硬钉 1 格
  其余                 → 原样

只动 `<pre>` 里的文本，标签、属性、注释一概不碰；先摘掉旧的 `.fw/.fw2/.hw` 再重新封
一遍，所以可反复执行（幂等）。同时按字符宽度算出每块的最大列数写成 `data-cols`，
让 `check_frames.py` 除了「行行等宽」还能断言「等于声明的列数」——只给以 `┌` 或 `╭`
开头的整框加，片段式的图示不加（它们的行本来就不等宽）。

  python3 tools/wrap_frames.py web/interaction-spec.html web/index.html
"""

from __future__ import annotations

import html
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from screens import width, wrap_cells  # noqa: E402

PRE = re.compile(r"<pre([^>]*)>(.*?)</pre>", re.S)
OLD_BOX = re.compile(r'<span class="(?:fw2|fw|hw)">([^<]*)</span>')
TAG = re.compile(r"(<[^>]+>)")



def unwrap(inner: str) -> str:
    """摘掉旧的盒子。带子标签的直接跳过——那些要看一眼才知道该怎么封。"""
    while True:
        stripped = OLD_BOX.sub(r"\1", inner)
        if stripped == inner:
            return inner
        inner = stripped


def plain_width(line: str) -> int:
    return width(html.unescape(re.sub(r"<[^>]+>", "", line)))


def refit(inner: str) -> str:
    parts = TAG.split(unwrap(inner))
    return "".join(
        part if part.startswith("<") else wrap_cells(html.unescape(part))
        for part in parts
        if part
    )


def process(page: pathlib.Path) -> int:
    src = page.read_text(encoding="utf-8")
    touched = 0

    def one(m: re.Match) -> str:
        nonlocal touched
        attrs, inner = m.group(1), m.group(2)
        body = refit(inner)
        attrs = re.sub(r'\s*data-(?:check|cols)="[^"]*"', "", attrs)
        # 只有「每一行都等宽」的块才声明列数并纳入逐行复核：片段式的字符画（框内框、
        # 三栏并置）各行本来就不等宽，加 `data-check` 只会得到假警报。判定每次都重算，
        # 顺手清掉上一轮写歪的声明。
        lines = [ln for ln in body.split("\n") if ln.strip()]
        widths = {plain_width(ln) for ln in lines}
        if len(lines) >= 2 and len(widths) == 1:
            attrs += f' data-check="1" data-cols="{widths.pop()}"'
        if body != inner or attrs != m.group(1):
            touched += 1
        return f"<pre{attrs}>{body}</pre>"

    out = PRE.sub(one, src)
    if out != src:
        page.write_text(out, encoding="utf-8")
    return touched


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__.strip().split("\n")[-1].strip())
        return 2
    for rel in argv:
        page = pathlib.Path(rel)
        print(f"· {page}：{process(page)} 块有改动")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
