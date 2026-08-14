import { colorProp } from "./color-props.js";
import { KeyHint } from "./primitives.js";
import { useUiEnvironment } from "./theme-context.js";
import type { KeyBindingHint } from "./types.js";
export function Keybar({ hints }: { hints: readonly KeyBindingHint[] }) {
  const { theme } = useUiEnvironment();
  return (
    <box
      id="keybar"
      height={1}
      flexShrink={0}
      {...colorProp("backgroundColor", theme.background)}
      paddingX={1}
      flexDirection="row"
      gap={1}
      overflow="hidden"
    >
      {hints.map((hint) => (
        <KeyHint key={`${hint.key}-${hint.label}`} keyName={hint.key} label={hint.label} />
      ))}
    </box>
  );
}
export function StatusBar({
  workspace,
  mode,
  model,
  contextPercent,
  pending = 0,
}: {
  workspace: string;
  mode: string;
  model: string;
  contextPercent: number;
  pending?: number;
}) {
  const { theme } = useUiEnvironment();
  const safeContext = Math.max(0, Math.min(100, Math.round(contextPercent)));
  return (
    <box
      id="statusbar"
      height={1}
      flexShrink={0}
      {...colorProp("backgroundColor", theme.surface2)}
      paddingX={1}
      flexDirection="row"
      overflow="hidden"
    >
      <text {...colorProp("fg", theme.foreground)} {...colorProp("bg", theme.surface4)}>
        {" "}
        {workspace}{" "}
      </text>
      <text {...colorProp("fg", theme.secondary)}>
        {" "}
        mode:{mode} │ model:{model} │ ctx:{safeContext}%
      </text>
      {safeContext >= 85 ? <text {...colorProp("fg", theme.warning)}> ⚠</text> : null}
      <box flexGrow={1} />
      {pending > 0 ? (
        <text {...colorProp("fg", theme.warning)}>⏸ {pending} waiting</text>
      ) : (
        <text {...colorProp("fg", theme.success)}>● ready</text>
      )}
    </box>
  );
}
