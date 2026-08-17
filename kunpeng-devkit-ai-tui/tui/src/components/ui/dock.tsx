import { KunpengBrand } from "./brand.js";
import { colorProp } from "./color-props.js";
import { SectionLabel } from "./primitives.js";
import { useUiEnvironment } from "./theme-context.js";
import type { DockFileItem, DockTaskItem } from "./types.js";

function taskGlyph(status: DockTaskItem["status"], unicode: boolean): string {
  if (!unicode)
    return status === "running"
      ? ">"
      : status === "completed"
        ? "+"
        : status === "failed"
          ? "x"
          : status === "waiting"
            ? "!"
            : "o";
  return status === "running"
    ? "▶"
    : status === "completed"
      ? "✓"
      : status === "failed"
        ? "✕"
        : status === "waiting"
          ? "⏸"
          : "○";
}
function riskBar(risk: DockFileItem["risk"], unicode: boolean): string {
  if (!risk) return "";
  return (unicode ? "█" : "#").repeat(risk);
}
export function Dock({
  width,
  collapsed,
  tasks,
  files,
  activeTaskId,
  focused,
  selectedIndex,
  onSelectTask,
  onOpenOverlay,
}: {
  width: number;
  collapsed: boolean;
  tasks: readonly DockTaskItem[];
  files: readonly DockFileItem[];
  activeTaskId: string;
  focused: boolean;
  selectedIndex: number;
  onSelectTask: (id: string) => void;
  onOpenOverlay: () => void;
}) {
  const { theme, capabilities } = useUiEnvironment();
  if (collapsed) {
    return (
      <box
        width={width}
        flexShrink={0}
        {...colorProp("backgroundColor", theme.surface2)}
        border={["right"]}
        {...colorProp("borderColor", theme.borderSubtle)}
        flexDirection="column"
        alignItems="center"
      >
        {/* 折叠态只有 3 列，低于字标最小宽度，按规则不画标识。 */}
        <box height={3} flexShrink={0} alignItems="center" justifyContent="center">
          <KunpengBrand available={width} />
        </box>
        {(["▮", "▯", "◇", "?"] as const).map((glyph, index) => (
          <box
            key={glyph}
            height={3}
            width="100%"
            alignItems="center"
            justifyContent="center"
            {...colorProp("backgroundColor", index === 0 ? theme.selected : undefined)}
            {...(index === 3 ? { onMouseDown: onOpenOverlay } : {})}
          >
            <text {...colorProp("fg", index === 0 ? theme.primaryText : theme.muted)}>
              {capabilities.unicode
                ? glyph
                : index === 0
                  ? ">T"
                  : index === 1
                    ? "P"
                    : index === 2
                      ? "M"
                      : "?"}
            </text>
          </box>
        ))}
      </box>
    );
  }
  return (
    <box
      width={width}
      flexShrink={0}
      {...colorProp("backgroundColor", theme.background)}
      border={["right"]}
      {...colorProp("borderColor", focused ? theme.borderStrong : theme.borderSubtle)}
      flexDirection="column"
      overflow="hidden"
    >
      <box
        height={3}
        flexShrink={0}
        {...colorProp("backgroundColor", theme.surface2)}
        border={["bottom"]}
        {...colorProp("borderColor", theme.borderSubtle)}
        paddingX={1}
        alignItems="center"
      >
        <KunpengBrand available={width - 2} />
      </box>
      <box flexGrow={1} minHeight={1} paddingX={1} flexDirection="column" overflow="hidden">
        <box height={1} flexShrink={0}>
          <SectionLabel count={tasks.length}>T A S K S</SectionLabel>
        </box>
        {tasks.slice(0, 4).map((task, index) => {
          const active = task.id === activeTaskId;
          const focusRow = focused && index === selectedIndex;
          const statusColor =
            task.status === "failed"
              ? theme.danger
              : task.status === "waiting"
                ? theme.warning
                : task.status === "completed"
                  ? theme.success
                  : task.status === "running"
                    ? theme.primaryText
                    : theme.muted;
          return (
            // biome-ignore lint/a11y/noStaticElementInteractions: OpenTUI task row has arrow/j-k keyboard selection.
            <box
              key={task.id}
              height={2}
              flexShrink={0}
              paddingX={1}
              {...colorProp(
                "backgroundColor",
                active || focusRow ? (focusRow ? theme.focus : theme.selected) : undefined,
              )}
              onMouseDown={() => onSelectTask(task.id)}
              flexDirection="row"
              alignItems="center"
            >
              <text {...colorProp("fg", active ? theme.primaryText : statusColor)}>
                {active || focusRow ? "▎" : " "}
                {taskGlyph(task.status, capabilities.unicode)}{" "}
              </text>
              <text
                flexGrow={1}
                wrapMode="none"
                truncate
                {...colorProp("fg", active ? theme.primaryText : theme.foregroundOnSurface)}
              >
                {task.label}
              </text>
              {task.elapsed ? <text {...colorProp("fg", theme.muted)}>{task.elapsed}</text> : null}
            </box>
          );
        })}
        <box height={1} flexShrink={0} marginTop={1}>
          <SectionLabel>PROJECT · FOLLOW</SectionLabel>
        </box>
        {files.slice(0, 8).map((file) => (
          <box
            key={file.id}
            height={1}
            flexShrink={0}
            paddingLeft={Math.min(4, file.depth + 1)}
            {...colorProp("backgroundColor", file.active ? theme.selected : undefined)}
            flexDirection="row"
          >
            <text
              flexGrow={1}
              minWidth={1}
              wrapMode="none"
              truncate
              {...colorProp(
                "fg",
                file.active
                  ? theme.primaryText
                  : file.kind === "folder"
                    ? theme.secondaryOnSurface
                    : theme.foregroundOnSurface,
              )}
            >
              {file.kind === "folder" ? (capabilities.unicode ? "▾ " : "v ") : "  "}
              {file.label}
            </text>
            {file.risk ? (
              <text
                width={4}
                flexShrink={0}
                wrapMode="none"
                {...colorProp(
                  "fg",
                  theme.memory[Math.min(theme.memory.length - 1, file.risk)] ?? theme.secondary,
                )}
              >
                {` ${riskBar(file.risk, capabilities.unicode)}`}
              </text>
            ) : null}
          </box>
        ))}
        <box height={1} flexShrink={0} marginTop={1}>
          <SectionLabel>TOOLS</SectionLabel>
        </box>
        <text {...colorProp("fg", theme.secondary)}>✓ cpp_migrator</text>
        <text {...colorProp("fg", theme.secondary)}>✓ knowledge_base</text>
      </box>
    </box>
  );
}
