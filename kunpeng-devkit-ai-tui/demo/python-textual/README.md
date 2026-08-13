# Kunpeng DevKit AI · Python Textual Demo

方案 A：基于 Python + Textual 的 Launch 页面与性能图表工作区原型。

## 安装与运行

```sh
uv sync
uv run devkitai
```

进入 Launch 页面后输入 `/chart` 打开图表工作区。

## 测试

```sh
uv run python -m unittest discover -s tests -v
```

完整实现规格见 [`../docs/spec_A.md`](../docs/spec_A.md)。
