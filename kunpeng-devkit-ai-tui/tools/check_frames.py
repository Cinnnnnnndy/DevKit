#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在真浏览器里复核字符帧：逐行等宽 + 逐字步进。

`screens.py` 的断言只保证「按终端单元格算」是齐的；页面上齐不齐还取决于浏览器
拿哪个回退字体去画 CJK、Braille、① ⟳ ⧉ 这些等宽字体不覆盖的字形。两套账都得对，
所以这里跑一次 headless Chrome，量两件事：

  ① 逐行等宽——每个 `pre[data-check]` 的每一行实测宽度必须一致；带 `data-cols="160"`
     的还要等于声明的列数。这一条抓「某一行多了一格」。
  ② 逐字步进——每个 `pre` 里出现的非 ASCII 字符，按它在页面里**实际使用的**写法
     （裸字符 / `.fw` / `.hw`）量一次步进，必须等于 `screens.char_width()`（汉字 2 格、
     其余 1 格）。这一条抓「这个字形现在没被钉住」：页面缺 `.fw`/`.hw` 规则、或者
     清单漏了一个字形，都会在这里点名，并告诉你去改哪一处。

  python3 tools/check_frames.py [页面…]

浏览器查找顺序：`$CHROME` → macOS 上的 Google Chrome → Playwright 预装 Chromium →
PATH 上的 chromium/chrome。找不到就跳过并返回 0：它是加固手段，不该把没有浏览器的
机器卡住。
"""

from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from screens import NARROW_GLYPHS, char_width  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_PAGES = [
    "web/screens.html",
    "web/design-input.html",
    "web/interaction-spec.html",
    "web/index.html",
]
ROW_TOLERANCE = 0.5  # 行宽：半格以内算舍入噪声
CHAR_TOLERANCE = 0.15  # 字宽：逐字量的是平均值，容差要小到能分开 1.667 与 2
MAC_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

PROBE = """
<script>
window.addEventListener('load', () => {
  const probe = document.createElement('pre');
  document.body.appendChild(probe);
  const N = 64;
  const rows = [], chars = [];
  const styleOf = cs => `position:absolute;left:-9999px;top:0;display:block;white-space:pre;
    margin:0;padding:0;border:0;font-family:${cs.fontFamily};font-size:${cs.fontSize};
    letter-spacing:${cs.letterSpacing};font-weight:${cs.fontWeight}`;
  const measure = (html, cs) => {
    probe.style.cssText = styleOf(cs);
    probe.innerHTML = html.repeat(N);
    return probe.getBoundingClientRect().width / N;
  };
  document.querySelectorAll('pre').forEach((pre, i) => {
    const cs = getComputedStyle(pre);
    const unit = measure('0', cs);
    const label = pre.getAttribute('data-label') || pre.className || '(pre)';
    if (pre.hasAttribute('data-check') || pre.hasAttribute('data-cols')) {
      rows.push({ i, label,
        cols: pre.hasAttribute('data-cols') ? +pre.getAttribute('data-cols') : null,
        widths: pre.innerHTML.split('\\n').filter(l => l.length).map(l => measure(l, cs) / unit),
      });
    }
    // 逐字：按它在页面里实际使用的写法（裸 / .fw / .hw）分组量
    const seen = new Set(), walker = document.createTreeWalker(pre, NodeFilter.SHOW_TEXT);
    let node;
    while ((node = walker.nextNode())) {
      const pinned = node.parentElement && node.parentElement.closest('.hw, .fw2, .fw');
      const how = !pinned ? '裸' : '.' + (pinned.classList.contains('hw') ? 'hw'
        : pinned.classList.contains('fw2') ? 'fw2' : 'fw');
      for (const ch of node.textContent) {
        if (ch.codePointAt(0) < 128 || ch.trim() === '') continue;
        const key = ch + '\\u0000' + how;
        if (seen.has(key)) continue;
        seen.add(key);
        const html = how === '裸' ? ch : `<span class="${how.slice(1)}">${ch}</span>`;        chars.push({ i, label, ch, how,
          w: +(measure(html, cs) / unit).toFixed(3),
          occurrences: pre.innerHTML.split(ch).length - 1 });
      }
    }
  });
  probe.remove();
  document.title = 'FRAMES' + JSON.stringify({ rows, chars });
});
</script>
"""


def find_chrome() -> str | None:
    env = pathlib.Path(__import__("os").environ.get("CHROME", ""))
    if env.is_file():
        return str(env)
    if pathlib.Path(MAC_CHROME).is_file():
        return MAC_CHROME
    for pat in ("/opt/pw-browsers/chromium-*/chrome-linux/chrome",):
        hits = sorted(pathlib.Path("/").glob(pat.lstrip("/")))
        if hits:
            return str(hits[-1])
    for name in ("chromium", "chromium-browser", "google-chrome", "chrome"):
        found = shutil.which(name)
        if found:
            return found
    return None


def measure(chrome: str, page: pathlib.Path) -> dict:
    html = page.read_text(encoding="utf-8").replace("</body>", PROBE + "</body>")
    with tempfile.TemporaryDirectory() as tmp:
        probe_file = pathlib.Path(tmp) / page.name
        probe_file.write_text(html, encoding="utf-8")
        dom = subprocess.run(
            [
                chrome, "--headless=new", "--no-sandbox", "--disable-gpu",
                "--virtual-time-budget=6000", "--dump-dom", probe_file.as_uri(),
            ],
            capture_output=True, text=True, timeout=180,
        ).stdout
    m = re.search(r"<title>FRAMES(\{.*\})</title>", dom, re.S)
    if not m:
        raise SystemExit(f"[{page.name}] 探针没跑起来——页面结构变了？")
    return json.loads(m.group(1))


def check_rows(rel: str, data: dict) -> int:
    bad = 0
    for blk in data["rows"]:
        ws = [w for w in blk["widths"] if w > 1]
        if len(ws) < 2:
            continue
        ref = max(set(round(w) for w in ws), key=lambda v: sum(round(w) == v for w in ws))
        if blk["cols"] and abs(ref - blk["cols"]) > ROW_TOLERANCE:
            print(f"✕ {rel} 第 {blk['i'] + 1} 块「{blk['label']}」：实测最宽 {ref} 格 ≠ 声明 {blk['cols']} 格")
            bad += 1
        for n, w in enumerate(blk["widths"], 1):
            if w > 1 and abs(w - ref) > ROW_TOLERANCE:
                print(f"✕ {rel} 第 {blk['i'] + 1} 块「{blk['label']}」第 {n} 行：实测 {w:.2f} 格 ≠ {ref} 格")
                bad += 1
    return bad


def check_chars(rel: str, data: dict) -> int:
    bad, seen = 0, set()
    for c in data["chars"]:
        key = (c["ch"], c["how"])
        if key in seen:
            continue
        seen.add(key)
        want = char_width(c["ch"])
        if abs(c["w"] - want) <= CHAR_TOLERANCE:
            continue
        if want == 2:
            hint = '包 <span class="fw2">（字体只画半宽的全角标点；em 方块用 <span class="fw">）'
        elif c["how"] != ".hw":
            hint = ("包 <span class=\"hw\">（把这个字形加进 tools/screens.py 的 NARROW_GLYPHS，"
                    "生成器就会自动用 .hw 钉成一格）")
        else:
            hint = "该字形连 .hw 也钉不住，得换一种盒子"
        print(
            f"✕ {rel} 「{c['ch']}」(U+{ord(c['ch']):04X}) 以 {c['how']} 出现："
            f"实测 {c['w']:.3f} 格 ≠ {want} 格 → {hint}"
        )
        bad += 1
    return bad


def main(argv: list[str]) -> int:
    chrome = find_chrome()
    if not chrome:
        print("· 未找到 Chromium，跳过渲染复核")
        return 0

    bad = 0
    for rel in argv or DEFAULT_PAGES:
        data = measure(chrome, ROOT / rel)
        n = check_rows(rel, data) + check_chars(rel, data)
        bad += n
        print(
            f"{'✕' if n else '✓'} {rel}  "
            f"{len(data['rows'])} 个受检块 · {len(data['chars'])} 处字形写法"
        )
    if bad:
        print(f"\n共 {bad} 处渲染对不上。NARROW_GLYPHS 现为：{NARROW_GLYPHS}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
