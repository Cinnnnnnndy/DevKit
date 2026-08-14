import { colorProp } from "./color-props.js";
import { useUiEnvironment } from "./theme-context.js";
export function KunpengBrand({ compact = false }: { compact?: boolean }) {
  const { theme, capabilities } = useUiEnvironment();
  const mark = capabilities.unicode ? "◢" : ">";
  if (compact)
    return (
      <text {...colorProp("fg", theme.kunpeng)}>
        <strong>{mark}</strong>
      </text>
    );
  return (
    <box height={1} flexDirection="row" flexShrink={0}>
      <text {...colorProp("fg", theme.kunpeng)}>
        <strong>{mark}</strong>
      </text>
      <text {...colorProp("fg", theme.foreground)}>
        {" "}
        <strong>KUNPENG</strong>{" "}
      </text>
      <text {...colorProp("fg", theme.foreground)} {...colorProp("bg", theme.surface4)}>
        <strong> DEVKIT AI </strong>
      </text>
    </box>
  );
}
