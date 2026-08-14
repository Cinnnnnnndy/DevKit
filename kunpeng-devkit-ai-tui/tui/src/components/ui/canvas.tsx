import type { ReactNode } from "react";
import { colorProp } from "./color-props.js";
import { Panel } from "./primitives.js";
import { useUiEnvironment } from "./theme-context.js";
export function MigrationCanvas({ focused = false }: { focused?: boolean }) {
  const { theme, capabilities } = useUiEnvironment();
  const fill = capabilities.unicode ? "█" : "#";
  const empty = capabilities.unicode ? "░" : ".";
  return (
    <Panel id="primary-canvas" title="MIGRATION REPORT" focused={focused} flexGrow={3}>
      <text {...colorProp("fg", theme.foreground)}>
        <strong>Compatibility</strong>{" "}
        <span {...colorProp("fg", theme.secondary)}>
          {fill.repeat(8)}
          {empty.repeat(2)} 82%
        </span>
      </text>
      <text {...colorProp("fg", theme.secondary)}>
        Critical <span {...colorProp("fg", theme.danger)}>2</span> · Warning{" "}
        <span {...colorProp("fg", theme.warning)}>8</span> · Fixed{" "}
        <span {...colorProp("fg", theme.success)}>21</span>
      </text>
      <box height={1} flexShrink={0} marginTop={1}>
        <text {...colorProp("fg", theme.muted)}>ISSUES · FILE · EVIDENCE</text>
      </box>
      <text {...colorProp("fg", theme.foreground)}>
        ▎ SSE intrinsic <span {...colorProp("fg", theme.accent)}>src/crypto.c:84</span>
      </text>
      <text {...colorProp("fg", theme.foreground)}>
        {" "}
        atomic fence <span {...colorProp("fg", theme.accent)}>src/memory.c:42</span>
      </text>
      <text {...colorProp("fg", theme.foreground)}>
        {" "}
        Makefile flags <span {...colorProp("fg", theme.success)}>✓ compatible</span>
      </text>
      <box flexGrow={1} minHeight={1} />
      <text {...colorProp("fg", theme.muted)}>AI annotation: 2 changes require review</text>
    </Panel>
  );
}
export function PatchCanvas({ focused = false }: { focused?: boolean }) {
  const { theme } = useUiEnvironment();
  return (
    <Panel id="secondary-canvas" title="PATCH PREVIEW" focused={focused} flexGrow={2}>
      <text {...colorProp("fg", theme.accent)}>src/crypto.c · @@ -84,2 +84,2 @@</text>
      <text {...colorProp("fg", theme.danger)}>- _mm_pause();</text>
      <text {...colorProp("fg", theme.success)}>+ asm volatile("yield");</text>
      <box height={1} flexShrink={0} marginTop={1}>
        <text {...colorProp("fg", theme.muted)}>EVIDENCE</text>
      </box>
      <text {...colorProp("fg", theme.foreground)}>[1] Kunpeng Porting Guide §4.2</text>
      <text {...colorProp("fg", theme.foreground)}>[2] ARM ARM D5.3.1</text>
      <box flexGrow={1} minHeight={1} />
      <text {...colorProp("fg", theme.secondary)}>Enter drill down · E evidence</text>
    </Panel>
  );
}
export function Inspector({
  strip = false,
  focused = false,
}: {
  strip?: boolean;
  focused?: boolean;
}) {
  const { theme } = useUiEnvironment();
  if (strip) {
    return (
      <box
        id="inspector-strip"
        width={3}
        flexShrink={0}
        border={["left"]}
        {...colorProp("borderColor", focused ? theme.borderStrong : theme.borderSubtle)}
        {...colorProp("backgroundColor", theme.surface1)}
        alignItems="center"
      >
        <text {...colorProp("fg", theme.muted)}>I</text>
      </box>
    );
  }
  return (
    <Panel id="inspector" title="INSPECTOR" focused={focused} flexGrow={1}>
      <text {...colorProp("fg", theme.muted)}>CURRENT OBJECT</text>
      <text {...colorProp("fg", theme.foreground)}>src/crypto.c</text>
      <text {...colorProp("fg", theme.secondary)}>line 84 · confidence 94%</text>
      <box height={1} flexShrink={0} marginTop={1}>
        <text {...colorProp("fg", theme.muted)}>LINKED VIEWS</text>
      </box>
      <text {...colorProp("fg", theme.foreground)}>› Issue SSE-001</text>
      <text {...colorProp("fg", theme.foreground)}> Evidence #4471</text>
      <text {...colorProp("fg", theme.foreground)}> Patch hunk 1</text>
    </Panel>
  );
}
export function EmptyCanvas({ children }: { children?: ReactNode }) {
  const { theme } = useUiEnvironment();
  return (
    <box flexGrow={1} alignItems="center" justifyContent="center">
      <text {...colorProp("fg", theme.muted)}>{children ?? "No data"}</text>
    </box>
  );
}
