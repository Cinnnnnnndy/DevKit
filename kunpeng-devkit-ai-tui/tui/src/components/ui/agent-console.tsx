import { colorProp } from "./color-props.js";
import { useUiEnvironment } from "./theme-context.js";
import type { ConsoleEventItem } from "./types.js";

function consoleGlyph(status: ConsoleEventItem["status"], unicode: boolean): string {
  if (!unicode)
    return status === "completed"
      ? "+"
      : status === "running"
        ? ">"
        : status === "warning"
          ? "!"
          : status === "failed"
            ? "x"
            : ".";
  return status === "completed"
    ? "●"
    : status === "running"
      ? "▶"
      : status === "warning"
        ? "⚠"
        : status === "failed"
          ? "✕"
          : "○";
}
export function AgentConsole({
  events,
  height,
  focused,
  expanded,
  onToggle,
}: {
  events: readonly ConsoleEventItem[];
  height: number;
  focused: boolean;
  expanded: boolean;
  onToggle: () => void;
}) {
  const { theme, capabilities } = useUiEnvironment();
  const visibleRows = Math.max(1, (expanded ? height + 3 : height) - 2);
  return (
    // biome-ignore lint/a11y/noStaticElementInteractions: OpenTUI box has an equivalent Ctrl+J keyboard path.
    <box
      id="agent-console"
      height={expanded ? height + 3 : height}
      flexShrink={0}
      {...colorProp("backgroundColor", theme.surface1)}
      border={["top"]}
      {...colorProp("borderColor", focused ? theme.borderStrong : theme.border)}
      flexDirection="column"
      overflow="hidden"
      onMouseDown={onToggle}
    >
      <box
        height={1}
        flexShrink={0}
        paddingX={1}
        {...colorProp("backgroundColor", focused ? theme.focus : theme.surface2)}
        flexDirection="row"
        justifyContent="space-between"
      >
        <text {...colorProp("fg", focused ? theme.foreground : theme.secondaryOnSurface)}>
          {focused ? "▎" : " "}
          <strong>AGENT CONSOLE</strong>
        </text>
        <text {...colorProp("fg", theme.muted)}>Ctrl+J {expanded ? "collapse" : "expand"}</text>
      </box>
      <box flexGrow={1} minHeight={1} paddingX={1} flexDirection="column">
        {events.slice(-visibleRows).map((event) => {
          const color =
            event.status === "completed"
              ? theme.success
              : event.status === "running"
                ? theme.primaryText
                : event.status === "warning"
                  ? theme.warning
                  : event.status === "failed"
                    ? theme.danger
                    : theme.muted;
          return (
            <text key={event.id} wrapMode="none" truncate {...colorProp("fg", theme.secondary)}>
              <span {...colorProp("fg", color)}>
                {consoleGlyph(event.status, capabilities.unicode)}
              </span>{" "}
              {event.label} <span {...colorProp("fg", theme.muted)}>{event.detail}</span>
            </text>
          );
        })}
      </box>
    </box>
  );
}
