#!/usr/bin/env python3
"""从真实标识位图重采样出 demo splash 用的半块点阵标识。

背景
----
demo.html 的开场画面用一段 <pre class="kpm"> 手描点阵当标识。手描有两个问题：
标识一改就得重描；而且描的时候容易忽略"字符格不是正方形"，画出来会被拉扁。

这个脚本把标识从 PNG 直接重采样成半块字符画，标识换了重跑一次即可。

为什么要做非等比重采样
----------------------
splash 下 .kpm 是 font-size:14px / line-height:.86，一个字符格约 8.4 x 12.0 px。
半块（▀ ▄ █）把一个字符格纵向切成两半，所以一个"点"是 8.4 宽 x 6.0 高 ——
宽是高的 1.4 倍。若按原图 1:1 取点，渲染出来就会横向拉宽 1.4 倍。

设点阵为 cols 列 x rows 文本行（= rows*2 个纵向点）：
    视觉宽 = cols * 8.4
    视觉高 = rows * 12.0
要让视觉宽高比等于原图的 44/45 = 0.978，就要
    cols / rows = 0.978 * 12.0 / 8.4 = 1.40

默认取 25 列 x 18 行（25/18 = 1.389），既贴近 1.40 又保住原来的视觉体量。
换算到点阵就是 25 宽 x 36 高，正是从 44x45 做一次非等比缩放。

用法
----
    python3 tools/kpmark.py                 # 预览：终端里打出点阵
    python3 tools/kpmark.py --write         # 写回 web/demo.html 的标记区间
    python3 tools/kpmark.py --cols 18 --rows 13 --write

只依赖标准库（zlib 解 PNG），不需要 Pillow。
"""

import argparse
import base64
import pathlib
import re
import sys
import zlib

HERE = pathlib.Path(__file__).resolve().parent
WEB = HERE.parent / "web"

# 两档羽色 —— 与 demo.html 的 --kp / --kp2 对应
RED = (0xED, 0x1C, 0x24)
GREY = (0xC9, 0xC9, 0xC9)

# splash 下的字符格尺寸（px）：font-size:14px 的等宽字宽约 0.6em，line-height:.86
CELL_W = 8.4
CELL_H = 12.0

BEGIN = "<!-- kpmark:begin 由 tools/kpmark.py 生成，勿手改 -->"
END = "<!-- kpmark:end -->"


# ── PNG 解码（标准库）─────────────────────────────────────────────

def png_rgba(data: bytes):
    """把 8 位 RGBA / 非隔行 PNG 解成 (w, h, [[(r,g,b,a), ...], ...])。"""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("不是 PNG")
    pos, idat, w = 8, bytearray(), None
    while pos < len(data):
        ln = int.from_bytes(data[pos:pos + 4], "big")
        typ = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w = int.from_bytes(body[0:4], "big")
            h = int.from_bytes(body[4:8], "big")
            depth, ctype, interlace = body[8], body[9], body[12]
            if (depth, ctype, interlace) != (8, 6, 0):
                raise ValueError(
                    f"只支持 8 位 RGBA 非隔行 PNG，当前 depth={depth} "
                    f"colour={ctype} interlace={interlace}")
        elif typ == b"IDAT":
            idat += body
        elif typ == b"IEND":
            break
        pos += 12 + ln
    if w is None:
        raise ValueError("缺少 IHDR")

    raw = zlib.decompress(bytes(idat))
    stride = w * 4
    out, prev = [], bytearray(stride)
    p = 0
    for _ in range(h):
        ft = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
        # 逐字节还原 PNG 的五种行滤波
        for i in range(stride):
            a = line[i - 4] if i >= 4 else 0
            b = prev[i]
            c = prev[i - 4] if i >= 4 else 0
            x = line[i]
            if ft == 1:
                x += a
            elif ft == 2:
                x += b
            elif ft == 3:
                x += (a + b) >> 1
            elif ft == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                x += a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
            elif ft != 0:
                raise ValueError(f"未知滤波类型 {ft}")
            line[i] = x & 0xFF
        out.append([tuple(line[i:i + 4]) for i in range(0, stride, 4)])
        prev = line
    return w, h, out


# ── 重采样与配色 ─────────────────────────────────────────────────

def crop_opaque(px, w, h, gate=8):
    """裁到不透明内容的包围盒。

    必须先裁再算比例：位图四周常有透明留白，留白的多少和标识本身无关，
    拿 44x45 当分母算出来的宽高比是错的。裁完之后内容正好贴四边，
    重采样出的点阵不会有全空的首尾行/列，比例才对得上。
    """
    xs = [x for y in range(h) for x in range(w) if px[y][x][3] >= gate]
    ys = [y for y in range(h) for x in range(w) if px[y][x][3] >= gate]
    if not xs:
        return px, w, h, (0, 0)
    x0, x1, y0, y1 = min(xs), max(xs) + 1, min(ys), max(ys) + 1
    return ([row[x0:x1] for row in px[y0:y1]], x1 - x0, y1 - y0, (x0, y0))

def resample(px, sw, sh, dw, dh):
    """面积平均缩放。alpha 作权重，避免边缘把透明像素混成脏色。"""
    dst = []
    for y in range(dh):
        y0, y1 = y * sh / dh, (y + 1) * sh / dh
        row = []
        for x in range(dw):
            x0, x1 = x * sw / dw, (x + 1) * sw / dw
            r = g = b = wsum = asum = n = 0.0
            for yy in range(int(y0), min(sh, max(int(y0) + 1, int(y1 + 0.999999)))):
                for xx in range(int(x0), min(sw, max(int(x0) + 1, int(x1 + 0.999999)))):
                    pr, pg, pb, pa = px[yy][xx]
                    a = pa / 255.0
                    r += pr * a
                    g += pg * a
                    b += pb * a
                    wsum += a
                    asum += a
                    n += 1
            if n == 0 or wsum == 0:
                row.append((0, 0, 0, 0.0))
            else:
                row.append((r / wsum, g / wsum, b / wsum, asum / n))
        dst.append(row)
    return dst


def classify(cell, alpha_gate, grey_gate):
    """把一个重采样点判成 None（空）/ 'r'（红羽）/ 'g'（灰羽）。"""
    r, g, b, a = cell
    if a < alpha_gate:
        return None
    # 红羽判据用饱和度而不是"离 RED 更近"：抗锯齿边缘会把红拉向灰，
    # 用最近色会把大量边缘点判成灰，羽毛轮廓就糊了。
    mx, mn = max(r, g, b), min(r, g, b)
    sat = 0.0 if mx == 0 else (mx - mn) / mx
    if sat >= grey_gate and r >= g and r >= b:
        return "r"
    return "g"


# ── 半块字符画 ───────────────────────────────────────────────────

CLS = {"r": "r", "g": "g"}


def render(bits, cols, rows):
    """两个纵向点合成一个字符：▀ 上半、▄ 下半、█ 全格，双色用前景+背景。"""
    lines = []
    for ry in range(rows):
        cells = []
        for cx in range(cols):
            top = bits[ry * 2][cx]
            bot = bits[ry * 2 + 1][cx]
            if top is None and bot is None:
                cells.append((None, " "))
            elif top == bot:
                cells.append((CLS[top], "█"))
            elif bot is None:
                cells.append((CLS[top], "▀"))
            elif top is None:
                cells.append((CLS[bot], "▄"))
            else:
                # 上下不同色：用上半块着前景，下半靠背景色补
                cells.append((f"{CLS[top]}{CLS[bot]}", "▀"))
        # 合并相邻同类，少产生 span
        out, i = [], 0
        while i < len(cells):
            cls, ch = cells[i]
            j = i
            buf = []
            while j < len(cells) and cells[j][0] == cls:
                buf.append(cells[j][1])
                j += 1
            text = "".join(buf)
            out.append(text if cls is None else f'<i class="{cls}">{text}</i>')
            i = j
        lines.append("".join(out).rstrip() if all(c[0] is None for c in cells) else "".join(out))
    # 不裁首尾空行：源图已裁到内容贴边，这里再裁会让实际行数少于 rows，
    # 渲染出的宽高比就跟着算错（曾经 18 行被裁成 17 行，比例从 1.39 变 1.47）。
    return lines


def plain(bits, cols, rows):
    """终端预览用的纯文本版。"""
    out = []
    for ry in range(rows):
        s = ""
        for cx in range(cols):
            t, b = bits[ry * 2][cx], bits[ry * 2 + 1][cx]
            s += {(0, 0): " ", (1, 0): "▀", (0, 1): "▄", (1, 1): "█"}[
                (t is not None, b is not None)]
        out.append(s)
    return out


# ── 取源图 ───────────────────────────────────────────────────────

def load_source(src: pathlib.Path, cls: str) -> bytes:
    if src.suffix.lower() == ".png":
        return src.read_bytes()
    html = src.read_text(encoding="utf-8")
    pats = [
        rf'class="{cls}"[^>]*src="data:image/png;base64,([A-Za-z0-9+/=]+)"',
        rf'src="data:image/png;base64,([A-Za-z0-9+/=]+)"[^>]*class="{cls}"',
    ]
    for p in pats:
        m = re.search(p, html)
        if m:
            return base64.b64decode(m.group(1))
    raise SystemExit(f"在 {src} 里找不到 class=\"{cls}\" 的内嵌 PNG")


def main():
    ap = argparse.ArgumentParser(description="从标识位图重采样半块点阵")
    ap.add_argument("--src", default=str(WEB / "index.html"),
                    help="源：PNG 文件，或内嵌该 PNG 的 HTML（默认 web/index.html）")
    ap.add_argument("--cls", default="kpmark", help="在 HTML 中查找的 class 名")
    ap.add_argument("--cols", type=int, default=25, help="点阵列数")
    ap.add_argument("--rows", type=int, default=18, help="文本行数（纵向点数为其两倍）")
    ap.add_argument("--alpha", type=float, default=0.42, help="透明度阈值，低于此判为空")
    ap.add_argument("--sat", type=float, default=0.34, help="饱和度阈值，高于此判为红羽")
    ap.add_argument("--target", default=str(WEB / "demo.html"), help="--write 时写回的文件")
    ap.add_argument("--write", action="store_true", help="写回 target 的 kpmark 标记区间")
    args = ap.parse_args()

    data = load_source(pathlib.Path(args.src), args.cls)
    fw, fh, full = png_rgba(data)
    px, sw, sh, off = crop_opaque(full, fw, fh)

    ideal = (sw / sh) * CELL_H / CELL_W  # cols/rows 的理想值
    got = args.cols / args.rows
    print(f"源图 {fw}x{fh} → 裁到内容 {sw}x{sh} (偏移 {off})  宽高比 {sw/sh:.3f}",
          file=sys.stderr)
    print(f"字符格 {CELL_W}x{CELL_H}px  cols/rows 理想 {ideal:.2f}  实取 {got:.2f}",
          file=sys.stderr)
    vis = (args.cols * CELL_W) / (args.rows * CELL_H)
    print(f"渲染后视觉宽高比 {vis:.3f}（内容 {sw/sh:.3f}，偏差 {abs(vis-sw/sh)/(sw/sh)*100:.1f}%）",
          file=sys.stderr)

    small = resample(px, sw, sh, args.cols, args.rows * 2)
    bits = [[classify(c, args.alpha, args.sat) for c in row] for row in small]

    if not args.write:
        for ln in plain(bits, args.cols, args.rows):
            print(ln)
        n_r = sum(c == "r" for row in bits for c in row)
        n_g = sum(c == "g" for row in bits for c in row)
        print(f"\n红 {n_r} 点 · 灰 {n_g} 点 · 空 "
              f"{args.cols*args.rows*2-n_r-n_g} 点", file=sys.stderr)
        return

    lines = render(bits, args.cols, args.rows)
    block = BEGIN + "\n<pre class=\"kpm\" aria-label=\"Kunpeng DevKit AI\">" + \
        "\n".join(lines) + "</pre>\n" + END

    tgt = pathlib.Path(args.target)
    html = tgt.read_text(encoding="utf-8")
    if BEGIN in html and END in html:
        head = html[:html.index(BEGIN)]
        tail = html[html.index(END) + len(END):]
        tgt.write_text(head + block + tail, encoding="utf-8")
        print(f"已更新 {tgt}", file=sys.stderr)
    else:
        raise SystemExit(
            f"{tgt} 里没有 kpmark 标记区间。请先把现有 <pre class=\"kpm\">…</pre> "
            f"用下面两行包起来：\n  {BEGIN}\n  {END}")


if __name__ == "__main__":
    main()
