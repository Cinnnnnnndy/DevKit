"""字符帧排版底座 —— 给 gen_screens.py 用。

为什么要有这一层：160 列的整屏字符帧不可能手写对齐。
一个汉字占 2 格、Braille 占 1 格、框线占 1 格，而 HTML 里这三类字符的
实际步进由字体决定（见 web/index.html 里 `.fw` 那段注释）——**排版宽度和
渲染宽度是两套账**，手写必然在某一行错开，且错开处往往在页面右边缘，
肉眼要逐行比对才看得出来。

所以这里把两件事都交给程序：
  ① 宽度按终端单元格算（CJK=2，Braille=1，其余=1），每块渲染前断言等宽；
  ② 输出 HTML 时给 CJK 包 `.fw`（2ch 字号 → 恰好 2 格），给 Braille 与 ⏸ 族包
     `.hw`（width:1ch 的行内块 → 恰好 1 格）。两类分开治：CJK 是 1 em 方块，
     字号法可靠；后者的步进由回退字体决定，只能硬钉宽度。

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
# 等宽字体不覆盖的字形。回退字体给它们的步进各不相同——实测 Chromium/Linux 下
# Braille 是 1.217 格、⏸ 是 0.830 格——**换字体就换一个值**，所以不能靠调字号凑，
# 只能在 CSS 里用 width:1ch 的行内块把它们硬钉成一格（见 page_css.py 的 .hw）。
HALFWIDTH_GLYPHS = "⏸⏵⏹⏺"


def char_width(ch: str) -> int:
    if unicodedata.combining(ch):
        return 0
    if BRAILLE[0] <= ord(ch) <= BRAILLE[1]:
        return 1
    if ch in HALFWIDTH_GLYPHS:
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
# CJK 一律 1 em 方块，2ch 字号后必然是 2 格——这一类可以靠字号解决。
FW = re.compile(r"[　-〿぀-ヿ㐀-䶿一-鿿！-｠]+")
# Braille 与暂停/播放族靠固定宽度的行内块解决，逐字符包，避免连排时误差累积。
HW = re.compile(f"[⠀-⣿{HALFWIDTH_GLYPHS}]")


def _wrap_special(text: str) -> str:
    text = html.escape(text, quote=False)
    text = FW.sub(lambda m: f'<span class="fw">{m.group(0)}</span>', text)
    return HW.sub(lambda m: f'<span class="hw">{m.group(0)}</span>', text)


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
            out.append(_wrap_special(value))
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
