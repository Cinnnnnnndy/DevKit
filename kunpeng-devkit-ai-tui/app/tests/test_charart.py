"""网页上字符画的对齐不变式（``web/index.html``）。

字符画靠**每个字符占几格**对齐，而浏览器只保证等宽字体里**它自己覆盖的字符**
等宽。JetBrains Mono 不含汉字也不含点阵，浏览器回退到别的字体，回退字体的
步进和 Latin 步进不成整数比：

    Latin 步进 = 0.602 em（等宽字体设计值）
    汉字       = 1.000 em  →  1.661 × Latin，字符画按 2 排的
    点阵 ⣿     = 0.500 em  →  0.831 × Latin，字符画按 1 排的

于是一行里每出现一个汉字，后面的东西就往左挪 0.34 格，框线右缘变成锯齿。
页面上的解法是给这些字符套 ``<span class="fw">``（字号改成 2ch，正好把两类
都掰回整数格）。**套漏一个就歪一行**，而这种歪只在中文下出现，纯英文界面上
怎么看都是对的——所以必须由测试盯着，不能靠自觉。

这里只查源文件，不开浏览器：能查的是"该套的都套了""盒子在终端格宽下是矩形"。
真实渲染宽度另由一次性脚本用 Chromium 量过（608 行全部等于终端格宽）。
"""

from __future__ import annotations

import pathlib
import re
import unicodedata as ud

import pytest

PAGE = pathlib.Path(__file__).resolve().parents[2] / "web" / "index.html"

#: 回退字体画成全角、但字符画按 1 格排的几个符号。``⏸`` 是
#: ``tokens.STATUS_GLYPH["paused"]``，不能换成别的字符，只能在 CSS 里掰宽度。
HALFWIDTH = set("⏸⟳⬡")
OPEN, CLOSE = "┌╭", "└╰"
BORDER = "│┌┐└┘├┤┬┴┼╭╮╯╰"


def cell_width(ch: str) -> int:
    """这个字符在终端里占几格。"""
    if ch in HALFWIDTH:
        return 1
    return 2 if ud.east_asian_width(ch) in ("W", "F") else 1


def needs_fix(ch: str) -> bool:
    """等宽字体覆盖不到、必须靠 ``.fw`` 掰宽度的字符。"""
    return 0x2800 <= ord(ch) <= 0x28FF or ud.east_asian_width(ch) in ("W", "F")


@pytest.fixture(scope="module")
def page() -> str:
    return PAGE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def pre_blocks(page: str) -> list[str]:
    return [m.group(1) for m in re.finditer(r"<pre[^>]*>(.*?)</pre>", page, re.S)]


def _unwrapped(inner: str) -> list[str]:
    """挑出**没有**被 .fw / .hw 包住的宽度可疑字符。"""
    bad: list[str] = []
    depth_ok = 0
    for token in re.split(r"(<[^>]*>)", inner):
        if token.startswith("<"):
            if re.match(r'<span class="(fw|hw)"', token):
                depth_ok += 1
            elif token == "</span>" and depth_ok:
                depth_ok -= 1
            continue
        if depth_ok:
            continue
        bad += [c for c in token if needs_fix(c) or c in HALFWIDTH]
    return bad


def test_every_wide_glyph_in_char_art_is_width_corrected(pre_blocks):
    """``<pre>`` 里的汉字与点阵必须套上 .fw，⏸⟳⬡ 必须套 .hw。

    漏一个就歪一行，而且只在中文下歪——纯英文界面上测不出来。
    """
    offenders = []
    for i, inner in enumerate(pre_blocks):
        bad = _unwrapped(inner)
        if bad:
            offenders.append((i, "".join(dict.fromkeys(bad))[:24]))
    assert not offenders, f"这些 pre 里有没掰宽度的字符：{offenders}"


def _boxes(text: str):
    """按 ┌…└ 切出盒子，返回每个盒子的行。"""
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        if not any(c in OPEN for c in lines[i]):
            i += 1
            continue
        j = i + 1
        while j < len(lines) and not any(c in CLOSE for c in lines[j]):
            j += 1
        if j >= len(lines):
            return
        yield lines[i : j + 1]
        i = j + 1


def _rightmost_border(line: str) -> int | None:
    col = last = None
    col = 0
    for ch in line:
        if ch in BORDER:
            last = col
        col += cell_width(ch)
    return last


def test_every_box_is_a_rectangle(page):
    """每个字符画盒子的右边框必须落在同一列。

    这是**终端格宽**下的检查，和浏览器无关：不齐就说明源文本自己数错了格，
    在真终端里同样是歪的。切出来只有两行边框的当成示意图（树状分支、圆角
    括号那种），不算盒子。
    """
    import html as _html

    ragged = []
    for inner in re.finditer(r"<pre[^>]*>(.*?)</pre>", page, re.S):
        # 必须先反转义：&lt; 是**一个**格子，按四个字符数会把整行算宽
        text = _html.unescape(re.sub(r"<[^>]+>", "", inner.group(1)))
        for box in _boxes(text):
            cols = {c for c in (_rightmost_border(l) for l in box) if c is not None}
            if len(cols) > 1 and sum(1 for l in box if _rightmost_border(l) is not None) >= 3:
                ragged.append(sorted(cols))
    assert not ragged, f"这些盒子的右边框不在同一列：{ragged}"


@pytest.mark.parametrize("cls", ["fw", "hw"])
def test_the_css_rule_behind_the_fix_still_exists(page, cls):
    """包了 span 而 CSS 规则没了，等于没修——两边必须同时在。"""
    assert re.search(rf"pre \.{cls}\{{font-size:\dch\}}", page), f"pre .{cls} 的宽度规则不见了"
