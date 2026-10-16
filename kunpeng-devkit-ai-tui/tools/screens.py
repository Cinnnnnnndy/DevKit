# -*- coding: utf-8 -*-
"""字符帧排版底座 —— 给 gen_screens.py 用。

为什么要有这一层：160 列的整屏字符帧不可能手写对齐。
一个汉字占 2 格、Braille 占 1 格、框线占 1 格，而 HTML 里这三类字符的
实际步进由字体决定（见 web/index.html 里 `.fw` 那段注释）——**排版宽度和
渲染宽度是两套账**，手写必然在某一行错开，且错开处往往在页面右边缘，
肉眼要逐行比对才看得出来。

所以这里把两件事都交给程序：
  ① 宽度按终端单元格算（CJK=2，Braille=1，其余=1），每块渲染前断言等宽；
  ② 输出 HTML 时按 `cell_class()` 给每个字形封盒子：`.fw` 用字号把 1 em 方块顶成 2 格，
     `.fw2` 把「字体只画半宽的全角标点」按宽度硬钉 2 格，`.hw` 把等宽字体不覆盖的字形
     按宽度硬钉 1 格。三类分开治，是因为它们的失效原因各不相同。

渲染结果由 check_frames.py 在真浏览器里逐行复核，不靠肉眼。

着色用 ⟦cls|text⟧ 标记，cls 直接是 web/index.html 里 `pre` 的既有 class
（ok / wn / er / pr / cm / ac / t / br / sel / s2 / g4 / o4 / v4 / a4 …），
不新造调色板。
"""

from __future__ import annotations

import html
import re
import unicodedata

# ── 字符宽度 ────────────────────────────────────────────────────────────
# Braille 在终端里占 1 格；`.fw`（2ch 字号）下 0.5em 的点阵正好落回 1 格。
BRAILLE = (0x2800, 0x28FF)
# 等宽字体不覆盖的字形。回退字体给它们的步进各不相同——**换字体就换一个值**，
# 所以不能靠调字号凑，只能在 CSS 里用 width:1ch 的行内块把它们硬钉成一格
# （见 page_css.py 的 .hw）。
#
# 这份清单不靠人记：`tools/check_frames.py` 会在真浏览器里量每个帧字符的步进，
# 凡是「按终端单元格算 1 格、实际渲染不是 1 格」的字符都会被它点名。把点名的字符
# 加到这里，再跑一次门禁——它转绿就说明清单齐了。
NARROW_GLYPHS = "⏸⏵⏹⏺①②③④⑤⟳⧉⬡✎↵"


def char_width(ch: str) -> int:
    if unicodedata.combining(ch):
        return 0
    if BRAILLE[0] <= ord(ch) <= BRAILLE[1]:
        return 1
    if ch in NARROW_GLYPHS:
        return 1
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


OPEN = re.compile(r"⟦([a-z0-9 ]+)\|")


def tokens(s: str):
    """扫出 (kind, value)：open / close / text。带栈，允许嵌套。"""
    i, depth = 0, 0
    while i < len(s):
        m = OPEN.match(s, i)
        if m:
            depth += 1
            yield "open", m.group(1)
            i = m.end()
            continue
        if s[i] == "⟧" and depth:
            depth -= 1
            yield "close", ""
            i += 1
            continue
        nxt = len(s)
        for j in range(i, len(s)):
            if s[j] == "⟧" and depth:
                nxt = j
                break
            if OPEN.match(s, j):
                nxt = j
                break
        else:
            nxt = len(s)
        if nxt == i:
            nxt = i + 1
        yield "text", s[i:nxt]
        i = nxt


def plain(s: str) -> str:
    """剥掉着色标记，只留字面。"""
    return "".join(v for k, v in tokens(s) if k == "text")


def width(s: str) -> int:
    return sum(char_width(c) for c in plain(s))


def pad(s: str, n: int, align: str = "left") -> str:
    """补到 n 格。补不下就是调用方算错了，直接炸，不做静默截断。"""
    gap = n - width(s)
    if gap < 0:
        raise ValueError(f"超出 {-gap} 格：{plain(s)!r}（限 {n}）")
    if align == "right":
        return " " * gap + s
    if align == "center":
        left = gap // 2
        return " " * left + s + " " * (gap - left)
    return s + " " * gap


def cut(s: str, n: int) -> str:
    """按单元格截断（只用于纯文本，不含标记）。"""
    out, acc = "", 0
    for ch in s:
        cw = char_width(ch)
        if acc + cw > n:
            break
        out += ch
        acc += cw
    return out


# ── 分栏 ────────────────────────────────────────────────────────────────
class Pane:
    """一列内容。宽度固定，行数不足由 hcat 补空。"""

    def __init__(self, w: int, lines: list[str] | None = None):
        self.w = w
        self.lines = list(lines or [])

    def add(self, *lines: str) -> "Pane":
        self.lines.extend(lines)
        return self

    def blank(self, n: int = 1) -> "Pane":
        self.lines.extend([""] * n)
        return self

    def rule(self, ch: str = "─", cls: str = "cm") -> "Pane":
        self.lines.append(f"⟦{cls}|{ch * self.w}⟧")
        return self

    def rendered(self, rows: int) -> list[str]:
        if len(self.lines) > rows:
            raise ValueError(f"栏内容 {len(self.lines)} 行 > 可用 {rows} 行")
        body = self.lines + [""] * (rows - len(self.lines))
        return [pad(x, self.w) for x in body]


def hcat(panes: list[Pane], sep: str = "│", sep_cls: str = "cm") -> list[str]:
    """并排拼栏，行数取最长的一栏。"""
    rows = max(len(p.lines) for p in panes)
    cols = [p.rendered(rows) for p in panes]
    glue = f"⟦{sep_cls}|{sep}⟧" if sep and sep_cls else sep
    return [glue.join(parts) for parts in zip(*cols)]


# ── 外框 ────────────────────────────────────────────────────────────────
class Frame:
    """整屏外框。inner = 总宽 - 2（左右框线）。"""

    def __init__(self, w: int, title: str = "", right: str = ""):
        self.w = w
        self.inner = w - 2
        self.title = title
        self.right = right
        self.lines: list[str] = []
        self.foot_left = ""
        self.foot_right = ""

    def add(self, *lines: str) -> "Frame":
        self.lines.extend(lines)
        return self

    def blank(self, n: int = 1) -> "Frame":
        self.lines.extend([""] * n)
        return self

    def sep(self, pattern: str | None = None) -> "Frame":
        """整宽分隔行，作为 ├…┤ 直接落在外框上。"""
        self.lines.append(_SEP if pattern is None else _SEP + pattern)
        return self

    def render(self) -> str:
        head = self._edge("┌", "┐", self.title, self.right)
        out = [head]
        for ln in self.lines:
            if ln.startswith(_SEP):
                spec = ln[len(_SEP) :] or "─" * self.inner
                out.append(f"⟦cm|├⟧{pad(spec, self.inner)}⟦cm|┤⟧")
            else:
                out.append(f"⟦cm|│⟧{pad(ln, self.inner)}⟦cm|│⟧")
        out.append(self._edge("└", "┘", self.foot_left, self.foot_right))
        return "\n".join(out)

    def foot(self, left: str = "", right: str = "") -> "Frame":
        self.foot_left, self.foot_right = left, right
        return self

    def _edge(self, lc: str, rc: str, left: str, right: str) -> str:
        left = f" {left} " if left else ""
        right = f" {right} " if right else ""
        fill = self.inner - width(left) - width(right)
        if fill < 0:
            raise ValueError(f"边框标题过长：{plain(left + right)!r}")
        return f"⟦cm|{lc}⟧{left}⟦cm|{'─' * fill}⟧{right}⟦cm|{rc}⟧"


_SEP = "\x00SEP\x00"


# ── 块字符 wordmark ─────────────────────────────────────────────────────
GLYPHS = {
    "D": ["█████ ", "██  ██", "██  ██", "██  ██", "█████ "],
    "E": ["██████", "██    ", "█████ ", "██    ", "██████"],
    "V": ["██  ██", "██  ██", "██  ██", " ████ ", "  ██  "],
    "K": ["██  ██", "██ ██ ", "████  ", "██ ██ ", "██  ██"],
    "I": ["██████", "  ██  ", "  ██  ", "  ██  ", "██████"],
    "T": ["██████", "  ██  ", "  ██  ", "  ██  ", "  ██  "],
    "A": [" ████ ", "██  ██", "██████", "██  ██", "██  ██"],
    "U": ["██  ██", "██  ██", "██  ██", "██  ██", " ████ "],
    "N": ["██  ██", "███ ██", "██████", "██ ███", "██  ██"],
    "P": ["█████ ", "██  ██", "█████ ", "██    ", "██    "],
    "G": [" ████ ", "██    ", "██ ███", "██  ██", " ████ "],
    " ": ["   ", "   ", "   ", "   ", "   "],
}


def wordmark(text: str, cls: str = "br") -> list[str]:
    rows = ["" for _ in range(5)]
    for ch in text:
        g = GLYPHS[ch.upper()]
        for i in range(5):
            rows[i] += g[i] + " "
    return [f"⟦{cls}|{r.rstrip()}⟧" if r.strip() else "" for r in rows]


# ── 水平 bar（八分之一格精度）────────────────────────────────────────────
EIGHTHS = "▏▎▍▌▋▊▉█"


def bar(ratio: float, cells: int, fill_cls: str, rest_cls: str = "cm") -> str:
    ratio = max(0.0, min(1.0, ratio))
    units = round(ratio * cells * 8)
    full, rem = divmod(units, 8)
    head = "█" * full + (EIGHTHS[rem - 1] if rem else "")
    tail = "░" * (cells - width(head))
    out = f"⟦{fill_cls}|{head}⟧" if head else ""
    if tail:
        out += f"⟦{rest_cls}|{tail}⟧"
    return out


# ── 输出 HTML ───────────────────────────────────────────────────────────
def cell_class(ch: str) -> str:
    """这个字形该用哪个盒子钉住它的格子；返回 "" 表示字体自己就画对了。

    判据是「字体实际给了它多宽」，不是 Unicode 说的多宽 —— 两者在 CJK 标点上分了岔：
    汉字是 1 em 方块，字号抬到 2ch 就是实打实的 2 格；而 `，。：「」（）` 这类全角标点，
    回退字体只画半个字宽（实测 `.fw` 下 1.016 格、裸排 0.5 格），**字号法在这里失效**，
    只能按宽度硬钉。
    """
    if BRAILLE[0] <= ord(ch) <= BRAILLE[1] or ch in NARROW_GLYPHS:
        return "hw"
    if unicodedata.east_asian_width(ch) in ("W", "F"):
        return "fw2" if unicodedata.category(ch)[0] in "PS" else "fw"
    return ""


def _flush_box(chars: list[str], cls: str) -> str:
    if not cls:
        return "".join(chars)
    if cls == "fw":
        # 字号法：一个 span 罩住一串汉字，步进跟着字号走，连排不会累积误差。
        return f'<span class="fw">{"".join(chars)}</span>'
    # 宽度法：必须逐字符一个盒子，否则 N 个字形挤在 1ch（或 2ch）里。
    return "".join(f'<span class="{cls}">{c}</span>' for c in chars)


def wrap_cells(text: str) -> str:
    """把一行纯文本按单元格宽度封好盒子，顺带做 HTML 转义。"""
    text = html.escape(text, quote=False)
    out: list[str] = []
    buf: list[str] = []
    buf_cls: str | None = None
    for ch in text:
        cls = cell_class(ch)
        if cls != buf_cls:
            if buf:
                out.append(_flush_box(buf, buf_cls or ""))
            buf, buf_cls = [], cls
        buf.append(ch)
    if buf:
        out.append(_flush_box(buf, buf_cls or ""))
    return "".join(out)


def to_html(src: str) -> str:
    """把 ⟦cls|text⟧ 标记的字符帧转成着色 HTML。"""
    out: list[str] = []
    depth = 0
    for kind, value in tokens(src):
        if kind == "open":
            out.append(f'<span class="{value}">')
            depth += 1
        elif kind == "close":
            out.append("</span>")
            depth -= 1
        else:
            out.append(wrap_cells(value))
    return "".join(out) + "</span>" * max(0, depth)


def check(block: str, expect: int, label: str) -> str:
    """渲染前的等宽断言 —— 排版错位在这里炸，而不是留给读者用眼睛找。"""
    for n, line in enumerate(block.split("\n"), 1):
        got = width(line)
        if got != expect:
            raise SystemExit(
                f"[{label}] 第 {n} 行宽 {got} ≠ {expect}\n  {plain(line)}"
            )
    return block
