# Kunpeng DevKit AI · TUI Demo

此目录集中存放本地开发新增的两个可运行 TUI 探索方案，避免与上层产品设计规范、Web 原型和原始素材混放。

## 方案 A：Python + Textual

目录：[`python-textual/`](python-textual/)

```sh
cd python-textual
uv sync
uv run devkitai
```

启动后输入 `/chart` 打开性能图表工作区。实现规格见 [`docs/spec_A.md`](docs/spec_A.md)。

## 方案 B：Go + Charmbracelet

目录：[`go-charmbracelet/`](go-charmbracelet/)

```sh
cd go-charmbracelet
go run ./cmd/devkitai
```

实现规格见 [`docs/spec_B.md`](docs/spec_B.md)。

## 验证

```sh
# Python
cd python-textual
uv run python -m unittest discover -s tests -v

# Go
cd ../go-charmbracelet
go test ./...
```
