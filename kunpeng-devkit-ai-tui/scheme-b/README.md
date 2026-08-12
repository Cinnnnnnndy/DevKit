# Kunpeng DevKit AI — 方案 B · Charm Flow

Kunpeng DevKit AI 的 **方案 B：Charm Flow**（Go + Bubble Tea v2）Launch 首屏原型。
以「任务输入 + 建议动作」为核心，Charm 式的轻量交互与状态反馈，作为后续工作台的应用骨架。

实现依据：`../spec_B.md`（视觉与交互规格）。

## 运行

```sh
go run ./cmd/devkitai          # 标准 156×48 体验
go run ./cmd/devkitai --no-animation   # 关闭入场动画（reduced motion）
NO_COLOR=1 go run ./cmd/devkitai      # 无色降级
```

推荐演示环境：True Color 终端 + JetBrains Mono / SF Mono。

## 交互

| 按键 | 行为 |
|---|---|
| 输入 | 直接描述任务（支持中文、粘贴、Home/End、单词移动） |
| `Enter` | 提交任务（空输入仅做 120ms 边框强调，不报错） |
| `↑ ↓` / `Tab` | 在输入框与建议动作之间导航（钳制，不循环） |
| `Enter`（动作选中） | Migrate / Scan 填入输入框；Resume 执行恢复占位流程 |
| `Esc` | 有内容时清空；空内容时聚焦第一个动作 |
| `Ctrl+U` | 清空输入 |
| `q` | 退出（仅无输入焦点时） |
| `Ctrl+Q` / `Ctrl+C` | 始终退出 |

## 结构

```
cmd/devkitai/            入口（--no-animation / NO_COLOR）
internal/app/            Elm 状态机：model / update / view / messages
internal/components/     brand · prompt · actions · environment · keyhelp · block
internal/theme/          色板 tokens（spec §5.1）与样式构建器
internal/layout/         响应式几何（五档 viewport，Update 与 View 共用）
testdata/golden/         viewport 黄金快照
demo.tape                VHS 演示脚本
```

## 验证

```sh
go build ./... && go vet ./...
go test ./...                    # 状态机单测 + golden + CJK 宽度
go test ./... -run TestGolden -update   # 刷新 golden 快照
vhs demo.tape                    # 录制演示（需 vhs / ttyd / ffmpeg）
```

## 规格要点

- 背景固定 `#181822`，每个 cell 都带明确背景，无默认色泄漏（§12.1 / §17.4）。
- 同一时刻只有一个紫色强调（输入框边框 或 动作轨道），Pink/Cyan 只做小面积点缀（§5.3）。
- 品牌红仅用于 Kunpeng 标识，错误用独立 danger pink（§P5）。
- 入场动画 420ms 一次性分段出现，Idle 无持续 tick（§13.1 / §17.5）。
- NO_COLOR / 256 色 / True Color 降级，状态永远伴随符号（● ▲ × spinner）（§5.4）。
