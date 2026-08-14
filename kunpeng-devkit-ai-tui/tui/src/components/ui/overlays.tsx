import { Fragment, type ReactNode } from "react";
import { colorProp } from "./color-props.js";
import { ActionButton } from "./primitives.js";
import { useUiEnvironment } from "./theme-context.js";
export type OverlayKind = "command" | "help" | "config" | "approval";
export interface CommandPaletteItem<Id extends string = string> {
  id: Id;
  label: string;
  detail: string;
  shortcut: string;
  disabled?: boolean;
}
function ModalFrame({
  width,
  height,
  title,
  tone = "neutral",
  children,
}: {
  width: number;
  height: number;
  title: string;
  tone?: "neutral" | "warning" | "danger";
  children: ReactNode;
}) {
  const { theme } = useUiEnvironment();
  const color =
    tone === "warning" ? theme.warning : tone === "danger" ? theme.danger : theme.borderStrong;
  return (
    <box
      position="absolute"
      zIndex={20}
      top="50%"
      left="50%"
      width={width}
      height={height}
      marginTop={-Math.floor(height / 2)}
      marginLeft={-Math.floor(width / 2)}
      {...colorProp("backgroundColor", theme.surface1)}
      border
      borderStyle="rounded"
      {...colorProp("borderColor", color)}
      paddingX={1}
      flexDirection="column"
      overflow="hidden"
    >
      <box height={2} flexShrink={0} alignItems="center">
        <text {...colorProp("fg", tone === "neutral" ? theme.foreground : color)}>
          <strong>{title}</strong>
        </text>
      </box>
      {children}
    </box>
  );
}
export function OverlayScrim({ children }: { children: ReactNode }) {
  const { theme } = useUiEnvironment();
  return (
    <box
      position="absolute"
      zIndex={19}
      top={0}
      left={0}
      width="100%"
      height="100%"
      {...colorProp("backgroundColor", theme.backgroundOuter)}
    >
      {children}
    </box>
  );
}
export function CommandPalette<Id extends string>({
  terminalWidth,
  terminalHeight,
  query,
  items,
  selected,
  onQuery,
  onSelect,
  onClose,
}: {
  terminalWidth: number;
  terminalHeight: number;
  query: string;
  items: readonly CommandPaletteItem<Id>[];
  selected: number;
  onQuery: (query: string) => void;
  onSelect: (item: CommandPaletteItem<Id>) => void;
  onClose: () => void;
}) {
  const { theme } = useUiEnvironment();
  const width = Math.max(36, Math.min(76, terminalWidth - 4));
  const height = Math.max(12, Math.min(19, terminalHeight - 4));
  return (
    <OverlayScrim>
      <ModalFrame width={width} height={height} title="COMMAND PALETTE">
        <box
          height={3}
          flexShrink={0}
          border
          borderStyle="single"
          {...colorProp("borderColor", theme.border)}
          paddingX={1}
          alignItems="center"
        >
          <text {...colorProp("fg", theme.primaryText)}>› </text>
          <input
            value={query}
            focused
            flexGrow={1}
            {...colorProp("textColor", theme.foreground)}
            placeholder="搜索命令、任务或工作区…"
            {...colorProp("placeholderColor", theme.muted)}
            {...colorProp("cursorColor", theme.primaryText)}
            onKeyDown={(key) => {
              if (key.ctrl || key.meta || key.name === "escape" || key.name === "esc") {
                key.preventDefault();
                if (key.name === "escape" || key.name === "esc") onClose();
              }
            }}
            onInput={onQuery}
            onSubmit={() =>
              items[selected] && !items[selected].disabled && onSelect(items[selected])
            }
          />
        </box>
        <box height={1} flexShrink={0}>
          <text {...colorProp("fg", theme.muted)}>SUGGESTED</text>
        </box>
        <box flexGrow={1} minHeight={1} flexDirection="column" overflow="hidden">
          {items.slice(0, Math.max(1, height - 8)).map((item, index) => (
            <box
              key={item.id}
              height={2}
              flexShrink={0}
              paddingX={1}
              {...colorProp("backgroundColor", index === selected ? theme.focus : undefined)}
              {...(!item.disabled ? { onMouseDown: () => onSelect(item) } : {})}
              flexDirection="row"
              alignItems="center"
            >
              <text
                width={18}
                wrapMode="none"
                truncate
                {...colorProp(
                  "fg",
                  item.disabled
                    ? theme.muted
                    : index === selected
                      ? theme.foreground
                      : theme.secondaryOnSurface,
                )}
              >
                {index === selected ? "▎" : " "}
                {item.label}
              </text>
              <text flexGrow={1} wrapMode="none" truncate {...colorProp("fg", theme.muted)}>
                {item.detail}
              </text>
              <text
                flexShrink={0}
                {...colorProp("fg", item.disabled ? theme.muted : theme.secondary)}
              >
                {item.shortcut}
              </text>
            </box>
          ))}
        </box>
        <box height={1} flexShrink={0}>
          <text {...colorProp("fg", theme.muted)}>↑↓ 选择 · Enter 执行 · Esc 关闭</text>
        </box>
      </ModalFrame>
    </OverlayScrim>
  );
}
export function HelpOverlay({
  terminalWidth,
  terminalHeight,
}: {
  terminalWidth: number;
  terminalHeight: number;
}) {
  const { theme } = useUiEnvironment();
  const width = Math.max(34, Math.min(68, terminalWidth - 4));
  const height = Math.max(16, Math.min(22, terminalHeight - 4));
  const rows = [
    ["Tab / Shift+Tab", "移动区域焦点"],
    ["↑ ↓ / j k", "选择列表项"],
    ["Enter", "打开、确认或下钻"],
    ["Esc", "关闭浮层、返回或中断"],
    ["Ctrl+P", "打开命令面板"],
    ["Ctrl+B", "折叠 Dock"],
    ["Ctrl+I", "切换 Inspector"],
    ["Ctrl+J", "展开 Agent Console"],
  ] as const;
  return (
    <OverlayScrim>
      <ModalFrame width={width} height={height} title="KEYBOARD HELP">
        <box flexGrow={1} minHeight={1} flexDirection="column">
          {rows.map(([key, label]) => (
            <box key={key} height={2} flexShrink={0} flexDirection="row">
              <text
                width={20}
                {...colorProp("fg", theme.foreground)}
                {...colorProp("bg", theme.surface4)}
              >
                {" "}
                {key}{" "}
              </text>
              <text {...colorProp("fg", theme.secondary)}> {label}</text>
            </box>
          ))}
        </box>
        <box height={1} flexShrink={0}>
          <text {...colorProp("fg", theme.muted)}>Esc 关闭帮助</text>
        </box>
      </ModalFrame>
    </OverlayScrim>
  );
}
export function ConfigOverlay({
  terminalWidth,
  terminalHeight,
  reason = "未检测到 aarch64 交叉编译工具链",
  fields = [
    { label: "交叉工具链", value: "/usr/bin/aarch64-linux-gnu-gcc" },
    { label: "输出目录", value: "./build-arm64" },
    { label: "并行度", value: "16" },
  ],
  selected,
  onSelect,
  onConfirm,
  onClose,
}: {
  terminalWidth: number;
  terminalHeight: number;
  reason?: string;
  fields?: readonly {
    label: string;
    value: string;
    sensitive?: boolean;
  }[];
  selected: number;
  onSelect: (index: number) => void;
  onConfirm: () => void;
  onClose: () => void;
}) {
  const { theme } = useUiEnvironment();
  const width = Math.max(38, Math.min(64, terminalWidth - 4));
  const height = Math.max(15, Math.min(19, terminalHeight - 4));
  return (
    <OverlayScrim>
      <ModalFrame width={width} height={height} title="补充配置" tone="warning">
        <text {...colorProp("fg", theme.secondary)}>为什么需要：{reason}</text>
        <box flexGrow={1} minHeight={1} marginTop={1} flexDirection="column">
          {fields.map((field, index) => (
            <Fragment key={field.label}>
              {/* biome-ignore lint/a11y/noStaticElementInteractions: OpenTUI field has arrow/j-k keyboard selection. */}
              <box
                height={3}
                flexShrink={0}
                border
                borderStyle="single"
                {...colorProp(
                  "borderColor",
                  index === selected ? theme.borderStrong : theme.border,
                )}
                {...colorProp("backgroundColor", index === selected ? theme.focus : theme.surface1)}
                paddingX={1}
                flexDirection="row"
                alignItems="center"
                onMouseDown={() => onSelect(index)}
              >
                <text width={14} {...colorProp("fg", theme.muted)}>
                  {index === selected ? "▎" : " "}
                  {field.label}
                </text>
                <text flexGrow={1} wrapMode="none" truncate {...colorProp("fg", theme.foreground)}>
                  {field.sensitive ? "••••••••" : field.value}
                </text>
              </box>
            </Fragment>
          ))}
        </box>
        <box height={3} flexShrink={0} flexDirection="row">
          <ActionButton label="Enter 保存并继续" active onPress={onConfirm} />
          <ActionButton label="Esc 稍后" onPress={onClose} />
        </box>
      </ModalFrame>
    </OverlayScrim>
  );
}
export function ApprovalOverlay({
  terminalWidth,
  terminalHeight,
  title = "即将应用当前补丁并运行 ARM64 构建。",
  scope = "src/crypto.c · src/memory.c · Makefile",
  evidence = "证据完整度 94% · 可回滚 · 不执行网络操作",
  selected,
  onSelect,
  onResolve,
}: {
  terminalWidth: number;
  terminalHeight: number;
  title?: string;
  scope?: string;
  evidence?: string;
  selected: number;
  onSelect: (index: number) => void;
  onResolve: (decision: "approve" | "review" | "reject") => void;
}) {
  const { theme } = useUiEnvironment();
  const width = Math.max(40, Math.min(70, terminalWidth - 4));
  const height = Math.max(16, Math.min(20, terminalHeight - 4));
  const actions = [
    ["A 允许应用", "approve"],
    ["R 继续审查", "review"],
    ["N 拒绝变更", "reject"],
  ] as const;
  return (
    <OverlayScrim>
      <ModalFrame width={width} height={height} title="APPLY APPROVAL" tone="warning">
        <text {...colorProp("fg", theme.foreground)}>{title}</text>
        <text {...colorProp("fg", theme.secondary)}>影响范围 {scope}</text>
        <text {...colorProp("fg", theme.secondary)}>{evidence}</text>
        <box height={1} flexShrink={0} marginTop={1}>
          <text {...colorProp("fg", theme.warning)}>⚠ 请确认变更范围后继续</text>
        </box>
        <box flexGrow={1} minHeight={1} marginTop={1} flexDirection="column">
          {actions.map(([label, decision], index) => (
            <Fragment key={decision}>
              {/* biome-ignore lint/a11y/noStaticElementInteractions: OpenTUI approval row has arrow/j-k and Enter keyboard routes. */}
              <box
                height={2}
                flexShrink={0}
                paddingX={1}
                border={index === selected ? ["left"] : false}
                {...colorProp("borderColor", theme.borderStrong)}
                {...colorProp("backgroundColor", index === selected ? theme.focus : undefined)}
                onMouseDown={() => {
                  onSelect(index);
                  onResolve(decision);
                }}
                alignItems="center"
              >
                <text
                  {...colorProp(
                    "fg",
                    decision === "reject"
                      ? theme.danger
                      : index === selected
                        ? theme.foreground
                        : theme.secondary,
                  )}
                >
                  {index === selected ? "▎" : " "}
                  {label}
                </text>
              </box>
            </Fragment>
          ))}
        </box>
        <box height={1} flexShrink={0}>
          <text {...colorProp("fg", theme.muted)}>↑↓ 选择 · Enter 确认 · Esc 取消</text>
        </box>
      </ModalFrame>
    </OverlayScrim>
  );
}
