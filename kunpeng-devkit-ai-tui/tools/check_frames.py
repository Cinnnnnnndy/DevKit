#!/usr/bin/env python3
"""在真浏览器里逐行复核字符帧的渲染宽度。

screens.py 的断言只保证「按终端单元格算」是齐的；页面上齐不齐还取决于
浏览器拿哪个回退字体去画 CJK、Braille、⏸ 这些等宽字体不覆盖的字形。
两套账都得对，所以这里跑一次 headless Chromium，把每个 `pre[data-check]`
的每一行实测宽度量出来，与该块的众数比较——**对不上就退出码非 0**。

  python3 tools/check_frames.py [页面…]

依赖环境里的 Chromium（Playwright 预装路径或 PATH 上的 chromium/chrome）。
找不到浏览器时跳过并返回 0：它是加固手段，不该把没有浏览器的机器卡住。
"""

from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_PAGES = ["web/screens.html", "web/design-input.html"]
TOLERANCE = 0.5  # 单元格；半格以内算舍入噪声

PROBE = """
<script>
window.addEventListener('load', () => {
  const out = [];
  const probe = document.createElement('pre');
  document.body.appendChild(probe);
  for (const pre of document.querySelectorAll('pre[data-check]')) {
    const cs = getComputedStyle(pre);
    probe.style.cssText = `position:absolute;left:-9999px;top:0;display:inline-block;
      white-space:pre;margin:0;padding:0;font:${cs.font};font-family:${cs.fontFamily};
      font-size:${cs.fontSize};letter-spacing:${cs.letterSpacing}`;
    probe.textContent = '0'.repeat(200);
    const unit = probe.getBoundingClientRect().width / 200;
    const widths = pre.innerHTML.split('\\n').map(line => {
      probe.innerHTML = line;
      return probe.getBoundingClientRect().width / unit;
    });
    out.push({ label: pre.getAttribute('data-label') || '(pre)', widths });
    probe.innerHTML = '';
  }
  probe.remove();
  document.title = 'FRAMES' + JSON.stringify(out);
});
</script>
"""


def find_chrome() -> str | None:
    for pat in ("/opt/pw-browsers/chromium-*/chrome-linux/chrome",):
        hits = sorted(pathlib.Path("/").glob(pat.lstrip("/")))
        if hits:
            return str(hits[-1])
    for name in ("chromium", "chromium-browser", "google-chrome", "chrome"):
        found = shutil.which(name)
        if found:
            return found
    return None


def measure(chrome: str, page: pathlib.Path) -> list[dict]:
    html = page.read_text(encoding="utf-8").replace("</body>", PROBE + "</body>")
    with tempfile.TemporaryDirectory() as tmp:
        probe_file = pathlib.Path(tmp) / page.name
        probe_file.write_text(html, encoding="utf-8")
        dom = subprocess.run(
            [
                chrome, "--headless", "--no-sandbox", "--disable-gpu",
                "--virtual-time-budget=5000", "--dump-dom", probe_file.as_uri(),
            ],
            capture_output=True, text=True, timeout=180,
        ).stdout
    m = re.search(r"<title>FRAMES(\[.*?\])</title>", dom, re.S)
    if not m:
        raise SystemExit(f"[{page.name}] 探针没跑起来——页面结构变了？")
    return json.loads(m.group(1))


def main(argv: list[str]) -> int:
    chrome = find_chrome()
    if not chrome:
        print("· 未找到 Chromium，跳过渲染宽度复核")
        return 0

    bad = 0
    for rel in argv or DEFAULT_PAGES:
        page = ROOT / rel
        blocks = measure(chrome, page)
        widest = 0
        for i, blk in enumerate(blocks):
            ws = [w for w in blk["widths"] if w > 1]
            if len(ws) < 2:
                continue
            ref = max(set(round(w) for w in ws), key=lambda v: sum(round(w) == v for w in ws))
            widest = max(widest, ref)
            for n, w in enumerate(blk["widths"], 1):
                if w > 1 and abs(w - ref) > TOLERANCE:
                    print(f"✕ {rel} 第 {i + 1} 块第 {n} 行：实测 {w:.2f} 格 ≠ {ref} 格")
                    bad += 1
        print(f"{'✕' if bad else '✓'} {rel}  {len(blocks)} 块 · 最宽 {widest} 格")
    if bad:
        print(f"\n共 {bad} 行渲染宽度对不上。")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
