"""把网页里字符画的宽度掰正，并把盒子压成矩形。

    python -m tools.fix_charart ../../index.html ../web/demo.html
    python -m tools.fix_charart --check ../web/*.html      # 只报不改

**为什么需要这个工具。** 字符画靠"每个字符占几格"对齐，而浏览器只保证等宽
字体里**它自己覆盖的字符**等宽。等宽字体基本都不含汉字，也不含点阵，浏览器
于是回退到别的字体，回退字体的步进和 Latin 步进不成整数比：

    Latin 步进 = 0.602 em（等宽字体设计值）
    汉字       = 1.000 em  →  1.661 × Latin，字符画按 2 排的
    点阵 ⣿     = 0.500 em  →  0.831 × Latin，字符画按 1 排的

一行里每出现一个汉字，后面的东西就往左挪 0.34 格，六个汉字偏两格——框线的
右边缘因此变成锯齿。**这不是谁数错了格，是 0.6 em 的 Latin 和 1 em 的方块
永远凑不出整数比**，换字体也解决不了。

解法是把这些字符的字号改成 ``2ch``。``ch`` 是当前字体里 "0" 的步进，也就是
一格，所以 ``2ch`` 就是两格；汉字是 1 em 方块，字号设成 2ch 后步进正好 2ch，
点阵是 0.5 em，同一个字号下正好落在 1ch——一条规则同时修好两类。

顺带修第二个 bug：有些手写 mockup 的框线**即使按终端格宽算也不齐**，在真
终端里同样是歪的。这里按盒子压成矩形，**只补不截**（目标列取盒内最大值，
绝不删内容）。

改完由 ``tests/test_charart.py`` 盯着——**这种歪只在中文下出现，纯英文界面上
怎么看都是对的**，靠自觉守不住。
"""

from __future__ import annotations

import pathlib
import re
import sys
import unicodedata as ud
from collections import Counter

#: 回退字体画成全角、但 Unicode 宽度是 Ambiguous、字符画按 **1 格**排的符号。
#: 这份名单是**实测出来的**（把页面里全部 764 个非 ASCII 字符逐个量了步进），
#: 不是照着 Unicode 表推的——``▲▶▸▼`` 同样是 Ambiguous，却被等宽字体自己
#: 覆盖着、步进正好 1.000，加进来反而会弄坏。
#: ``⏸`` 是 ``devkitai.tokens.STATUS_GLYPH["paused"]``，属于规范字形不能替换，
#: 只能在这里把宽度掰回来。
_HALFWIDTH_SYMBOLS = set("⏸⟳⬡")
#: 带圈数字 ①②③…：整段行为一致，按段收比一个一个补稳妥。
_HALFWIDTH_RANGES = ((0x2460, 0x24FF),)


def is_halfwidth(ch: str) -> bool:
    """回退字体画成全角，但字符画按 1 格排——要靠 ``.hw`` 掰回来。"""
    return ch in _HALFWIDTH_SYMBOLS or any(
        lo <= ord(ch) <= hi for lo, hi in _HALFWIDTH_RANGES
    )


OPEN, CLOSE = "┌╭", "└╰"
BORDER = "│┌┐└┘├┤┬┴┼╭╮╯╰"

CSS = (
    "\n/* 字符画宽度修正 —— 见 app/tools/fix_charart.py。等宽字体不含汉字与点阵，\n"
    "   回退字体的步进和 Latin 步进不成整数比（汉字 1.661×、点阵 0.831×），\n"
    "   字号改成 2ch 后正好落回 2 格和 1 格。块字符与框线本来就是 1.000×，别加。 */\n"
    "pre .fw{font-size:2ch}\n"
    "pre .hw{font-size:1ch}\n"
)


def cell_width(ch: str) -> int:
    """这个字符在终端里占几格。"""
    if is_halfwidth(ch):
        return 1
    return 2 if ud.east_asian_width(ch) in ("W", "F") else 1


def needs_fw(ch: str) -> bool:
    """靠 ``.fw`` 掰宽度的：全角（1 em）与点阵（0.5 em）。"""
    return 0x2800 <= ord(ch) <= 0x28FF or ud.east_asian_width(ch) in ("W", "F")


def _klass(ch: str) -> str | None:
    if is_halfwidth(ch):
        return "hw"
    return "fw" if needs_fw(ch) else None


def wrap_widths(inner: str) -> str:
    """给 ``<pre>`` 内容里的宽字符套上修正 span。

    幂等，但**不是靠整块短路**：只跳过已经在 ``.fw`` / ``.hw`` 里的那段文本。
    差别在于名单变了以后还能不能增量修——之前用整块短路，往名单里加了 ``⑤``
    之后，已经处理过的页面会被整块跳过，新字符永远补不上。
    """
    parts = re.split(r"(<[^>]*>)", inner)
    depth = 0  # >0 表示正处在一个修正 span 里
    for i, token in enumerate(parts):
        if i % 2:  # 奇数下标是标签
            if re.match(r'<span class="(fw|hw)"', token):
                depth += 1
            elif token == "</span>" and depth:
                depth -= 1
            continue
        if depth:
            continue
        text, out, j = parts[i], [], 0
        while j < len(text):
            k = _klass(text[j])
            m = j
            while m < len(text) and _klass(text[m]) == k:
                m += 1
            chunk = text[j:m]
            out.append(chunk if k is None else f'<span class="{k}">{chunk}</span>')
            j = m
        parts[i] = "".join(out)
    return "".join(parts)


def _scan(line: str) -> list[tuple[int, int, str]]:
    """→ [(raw 下标, 单元格列, 字符)]，跳过标签与实体。"""
    out, col, i = [], 0, 0
    while i < len(line):
        if line[i] == "<":
            j = line.find(">", i)
            i = (j + 1) if j >= 0 else len(line)
            continue
        if line[i] == "&":
            j = line.find(";", i)
            if 0 < j <= i + 8:  # &lt; &amp; &#123; —— 都只占一格
                col += 1
                i = j + 1
                continue
        if line[i] in BORDER:
            out.append((i, col, line[i]))
        col += cell_width(line[i])
        i += 1
    return out


def _text_end(seg: str) -> int:
    """段尾**真正的文本**结束在哪。

    竖线前面常常紧跟着标签（``…</span> <span class="pv-dim">│``），直接看
    ``seg[-1]`` 只会看到 ``>``，于是"吃掉尾随空格"永远吃不动。这里先把尾部
    连续的标签跳过去，再定位文本。
    """
    i = len(seg)
    while i > 0 and seg[i - 1] == ">":
        k = seg.rfind("<", 0, i)
        if k < 0:
            break
        i = k
    return i


def _retarget(line: str, marks, target) -> str:
    """把每条竖线挪到目标列：右移补空格 / ─，左移吃掉已有的空格。

    补白与削减都落在**文本末尾**而不是字符串末尾，否则空格会被塞进下一个
    span 里，或者根本削不动（见 :func:`_text_end`）。
    """
    shift, out, prev = 0, [], 0
    for (pos, col, ch), t in zip(marks, target):
        need = t - (col + shift)
        seg = line[prev:pos]
        fill = "─" if ("─" in line and ch in "┐┘┤┬┴┼╮╯") else " "
        end = _text_end(seg)
        if need > 0:
            seg = seg[:end] + fill * need + seg[end:]
        elif need < 0:
            k = 0
            while k < -need and end > 0 and seg[end - 1] in " ─":
                seg = seg[: end - 1] + seg[end:]
                end -= 1
                k += 1
            need = -k
        out.append(seg)
        shift += need
        prev = pos
    return "".join(out) + line[prev:]


def square_boxes(inner: str) -> str:
    """把每个字符画盒子压成矩形。

    盒子 = 含 ``┌``/``╭`` 的行到含 ``└``/``╰`` 的行。按**边框条数**分组分别
    对齐：顶栏常常是 4 条竖线而内容行只有 3 条（两块面板并排时，内容行把 A
    的右框和 B 的左框并成了一条），强行拉到同一个形状只会更糟；但同为 4 条的
    顶栏和底栏彼此必须齐。只有一行的那一组不动——没有参照物。
    """
    lines = inner.split("\n")
    marks = [_scan(l) for l in lines]
    i = 0
    while i < len(lines):
        if not any(c in OPEN for _, _, c in marks[i]):
            i += 1
            continue
        j = i + 1
        while j < len(lines) and not any(c in CLOSE for _, _, c in marks[j]):
            j += 1
        if j >= len(lines):
            break
        region = [k for k in range(i, j + 1) if len(marks[k]) >= 2]
        by_count: dict[int, list[int]] = {}
        for k in region:
            by_count.setdefault(len(marks[k]), []).append(k)
        for ks in by_count.values():
            if len(ks) < 2:
                continue
            target = Counter(tuple(c for _, c, _ in marks[k]) for k in ks).most_common(1)[0][0]
            for k in ks:
                if tuple(c for _, c, _ in marks[k]) == target:
                    continue
                new = _retarget(lines[k], marks[k], target)
                if tuple(c for _, c, _ in _scan(new)) == target:
                    lines[k] = new
        i = j + 1
    return "\n".join(lines)


def process(html: str) -> tuple[str, int]:
    """→ (新内容, 改动的 pre 块数)。幂等：改过的再跑一次不会变。"""
    changed = 0

    def one(m: re.Match) -> str:
        nonlocal changed
        inner = square_boxes(m.group(2))
        inner = wrap_widths(inner)
        if inner != m.group(2):
            changed += 1
        return m.group(1) + inner + "</pre>"

    out = re.sub(r"(<pre[^>]*>)(.*?)</pre>", one, html, flags=re.S)
    # 只有真的存在需要掰宽度的字符才注入 CSS——没有字符画的页面不该多两条规则
    wants = any(
        needs_fw(c) or is_halfwidth(c)
        for m in re.finditer(r"<pre[^>]*>(.*?)</pre>", out, re.S)
        for c in re.sub(r"<[^>]+>", "", m.group(1))
    )
    if wants and "pre .fw{" not in out and "<style" in out:
        out = out.replace("</style>", CSS + "</style>", 1)
    return out, changed


def main(argv: list[str]) -> int:
    check = "--check" in argv
    files = [pathlib.Path(a) for a in argv if not a.startswith("-")]
    if not files:
        print(__doc__.split("\n")[2].strip(), file=sys.stderr)
        return 2
    dirty = 0
    for f in files:
        src = f.read_text(encoding="utf-8")
        out, n = process(src)
        if out == src:
            print(f"  {f}  已经是对的")
            continue
        dirty += 1
        if check:
            print(f"  {f}  ✗ {n} 个 pre 块需要修正")
        else:
            f.write_text(out, encoding="utf-8")
            print(f"  {f}  ✓ 修正 {n} 个 pre 块")
    return 1 if (check and dirty) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
