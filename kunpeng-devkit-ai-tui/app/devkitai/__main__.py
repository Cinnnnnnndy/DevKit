"""``python -m devkitai [shell|preview|gallery]``。"""

import sys

PAGES = {
    "shell": ("devkitai.shell", "工作台外壳（默认）"),
    "preview": ("devkitai.preview", "组件预览页 · 可现场切换渲染层"),
    "gallery": ("devkitai.gallery", "图元画廊 · COMPONENT.md §3 的活样本"),
}


def main() -> None:
    page = sys.argv[1] if len(sys.argv) > 1 else "shell"
    if page in ("-h", "--help") or page not in PAGES:
        if page not in ("-h", "--help"):
            print(f"未知页面 {page!r}\n", file=sys.stderr)
        print("用法：python -m devkitai [page]\n")
        for name, (_, desc) in PAGES.items():
            print(f"  {name:<9} {desc}")
        raise SystemExit(0 if page in ("-h", "--help") else 2)
    module = __import__(PAGES[page][0], fromlist=["main"])
    module.main()


if __name__ == "__main__":
    main()
