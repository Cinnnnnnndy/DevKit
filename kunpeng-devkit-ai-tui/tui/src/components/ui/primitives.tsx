import type { ReactNode } from "react";
import { colorProp } from "./color-props.js";
import { useUiEnvironment } from "./theme-context.js";
import type { SemanticTone } from "./types.js";
export function SectionLabel({ children, count }: { children: ReactNode; count?: number }) {
  const { theme } = useUiEnvironment();
  return (
    <box height={1} flexShrink={0} flexDirection="row" justifyContent="space-between">
      <text {...colorProp("fg", theme.mutedOnSurface)}>
        <strong>{children}</strong>
      </text>
      {count === undefined ? null : <text {...colorProp("fg", theme.secondary)}>{count}</text>}
    </box>
  );
}
export function KeyHint({ keyName, label }: { keyName: string; label: string }) {
  const { theme } = useUiEnvironment();
  return (
    <box height={1} flexDirection="row" flexShrink={0}>
      <text {...colorProp("fg", theme.foreground)} {...colorProp("bg", theme.surface4)}>
        {" "}
        {keyName}{" "}
      </text>
      <text {...colorProp("fg", theme.secondary)}> {label}</text>
    </box>
  );
}
export function StatusGlyph({ tone, children }: { tone: SemanticTone; children: ReactNode }) {
  const { theme } = useUiEnvironment();
  const color =
    tone === "success"
      ? theme.success
      : tone === "warning"
        ? theme.warning
        : tone === "danger"
          ? theme.danger
          : tone === "accent"
            ? theme.accent
            : theme.secondary;
  return <text {...colorProp("fg", color)}>{children}</text>;
}
export function ActionButton({
  label,
  active = false,
  disabled = false,
  danger = false,
  onPress,
  width,
}: {
  label: string;
  active?: boolean;
  disabled?: boolean;
  danger?: boolean;
  onPress?: () => void;
  width?: number;
}) {
  const { theme, capabilities } = useUiEnvironment();
  const foreground = disabled
    ? theme.muted
    : danger
      ? theme.danger
      : active
        ? theme.foreground
        : theme.secondaryOnSurface;
  return (
    <box
      height={3}
      {...(width === undefined ? {} : { width })}
      flexShrink={0}
      border
      borderStyle="single"
      {...colorProp("borderColor", active ? theme.borderStrong : theme.border)}
      {...colorProp("backgroundColor", active ? theme.focus : theme.surface1)}
      paddingX={1}
      alignItems="center"
      {...(!disabled && onPress ? { onMouseDown: onPress } : {})}
    >
      <text {...colorProp("fg", foreground)}>
        {active ? (capabilities.unicode ? "▎" : "|") : " "}
        {label}
      </text>
    </box>
  );
}
export function Panel({
  id,
  title,
  focused = false,
  children,
  flexGrow = 1,
  width,
}: {
  id?: string;
  title: string;
  focused?: boolean;
  children: ReactNode;
  flexGrow?: number;
  width?: number;
}) {
  const { theme, capabilities } = useUiEnvironment();
  return (
    <box
      {...(id === undefined ? {} : { id })}
      flexGrow={flexGrow}
      {...(width === undefined ? {} : { width })}
      minWidth={1}
      border
      borderStyle="single"
      {...colorProp("borderColor", focused ? theme.borderStrong : theme.borderSubtle)}
      {...colorProp("backgroundColor", theme.background)}
      flexDirection="column"
      overflow="hidden"
    >
      <box
        height={1}
        flexShrink={0}
        paddingX={1}
        {...colorProp("backgroundColor", focused ? theme.focus : theme.surface1)}
      >
        <text {...colorProp("fg", focused ? theme.foreground : theme.secondaryOnSurface)}>
          {focused ? (capabilities.unicode ? "▎" : "|") : " "}
          <strong>{title}</strong>
        </text>
      </box>
      <box flexGrow={1} minHeight={1} paddingX={1} flexDirection="column" overflow="hidden">
        {children}
      </box>
    </box>
  );
}
