"""给页面盖一个可见的构建时间戳。

GitHub Pages 的响应头是 ``cache-control: max-age=600``，改不了；浏览器还会在
这之上按启发式再留一会儿。于是「站点到底更没更新」变成一个反复要查的问题——
而它本来应该看一眼就知道。

所以让页面自己说出它是什么时候生成的。判断依据落在页面里，就不用去比对
响应头、也不用信任缓存。

    python tools/stamp.py
"""

from __future__ import annotations

import datetime as dt
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[3]
PAGES = [ROOT / "index.html", ROOT / "kunpeng-devkit-ai-tui/web/tui-app.html"]
MARK = re.compile(r'(<span id="build-stamp">)(.*?)(</span>)', re.S)


def head() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return "unknown"


def main() -> None:
    # 盖的是**生成时刻**，不是提交时刻——提交 SHA 在写文件时还不存在，
    # 硬要塞只能塞上一个提交的，反而更容易误读。
    stamp = f"{dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC · 基于 {head()}"
    for page in PAGES:
        if not page.exists():
            continue
        text = page.read_text(encoding="utf-8")
        if not MARK.search(text):
            print(f"  跳过 {page.name}：没有 build-stamp 占位")
            continue
        page.write_text(MARK.sub(rf"\g<1>{stamp}\g<3>", text), encoding="utf-8")
        print(f"  {page.relative_to(ROOT)}  ←  {stamp}")


if __name__ == "__main__":
    main()
