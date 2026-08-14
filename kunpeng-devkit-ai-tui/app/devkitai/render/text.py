"""按**显示宽度**而不是字符数做的对齐与截断。

这是整个项目里最容易反复踩的一个坑：Python 的 ``f"{s:<12}"`` 和 ``len(s)``
数的都是**码位**，而终端排的是**单元格**。一个汉字占 2 格，所以

    f"{'折线':<12}"   补 10 个空格，实际占 14 格 → 右边多出 2 格
    f"{'Sparkline':<12}" 补 3 个空格，实际占 12 格 → 对的

同一张表里两种标签混着用，列就是歪的。而这类 bug **只在中文标签下出现**，
纯英文界面上怎么测都测不出来——所以宁可全项目禁掉裸的 ljust / rjust / 格式化
对齐，统一走这里。
"""

from __future__ import annotations

from rich.cells import cell_len

ELLIPSIS = "…"


def pad(text: str, width: int, *, align: str = "left", fill: str = " ") -> str:
    """把 ``text`` 补到 ``width`` 个**单元格**宽。

    已经超宽时原样返回，不截断——补齐和截断是两件事，混在一起会让调用方
    分不清自己拿到的是哪一种。要截断请显式调 :func:`truncate`。
    """
    missing = width - cell_len(text)
    if missing <= 0:
        return text
    padding = fill * missing
    if align == "right":
        return padding + text
    if align == "center":
        left = missing // 2
        return fill * left + text + fill * (missing - left)
    return text + padding


def truncate(text: str, width: int, *, ellipsis: str = ELLIPSIS) -> str:
    """按单元格宽度截断，尾部加省略号。

    逐格累加而不是切片：CJK 占 2 格，直接 ``text[:width]`` 会在宽字符上
    切出半个格来——终端渲染出来是错位一格，而不是少一个字。
    """
    if width <= 0:
        return ""
    if cell_len(text) <= width:
        return text
    budget = width - cell_len(ellipsis)
    if budget <= 0:
        return ellipsis[:width]
    out: list[str] = []
    used = 0
    for ch in text:
        size = cell_len(ch)
        if used + size > budget:
            break
        out.append(ch)
        used += size
    return "".join(out) + ellipsis


def fit(text: str, width: int, *, align: str = "left") -> str:
    """截断 + 补齐，保证结果**恰好**占 ``width`` 格。

    表格列用这个：既不会因为超长把后面的列挤歪，也不会因为过短漏出底色。
    """
    return pad(truncate(text, width), width, align=align)
