import type { InputRenderable } from "@opentui/core";
import { type RefObject, useRef } from "react";
import { colorProp } from "./color-props.js";
import { useUiEnvironment } from "./theme-context.js";
export function PromptBar({
  value,
  focused,
  placeholder = "描述你想做什么，或用 / 调用命令",
  shortcutLabel = "Ctrl+P",
  inputRef,
  onInput,
  onSubmit,
  onFocus,
}: {
  value: string;
  focused: boolean;
  placeholder?: string;
  shortcutLabel?: string;
  inputRef?: RefObject<InputRenderable | null>;
  onInput: (value: string) => void;
  onSubmit: (value: string) => void;
  onFocus: () => void;
}) {
  const fallbackRef = useRef<InputRenderable | null>(null);
  const ref = inputRef ?? fallbackRef;
  const { theme, capabilities } = useUiEnvironment();
  const promptGlyph = capabilities.unicode ? "❯" : ">";
  const [shortcutKey, ...shortcutDetailParts] = shortcutLabel.split(" ");
  const shortcutDetail = shortcutDetailParts.join(" ");
  return (
    // biome-ignore lint/a11y/noStaticElementInteractions: OpenTUI 输入框可通过 Tab 和单击获得焦点。
    <box
      id="session-input"
      height={3}
      flexShrink={0}
      {...colorProp("backgroundColor", theme.surface1)}
      border
      borderStyle="single"
      {...colorProp("borderColor", focused ? theme.selected : theme.border)}
      paddingX={1}
      flexDirection="row"
      alignItems="center"
      onMouseDown={() => {
        onFocus();
        ref.current?.focus();
      }}
    >
      <text {...colorProp("fg", theme.primaryText)}>{promptGlyph} </text>
      <input
        ref={ref}
        value={value}
        focused={focused}
        flexGrow={1}
        {...colorProp("textColor", theme.foreground)}
        placeholder={placeholder}
        {...colorProp("placeholderColor", theme.muted)}
        {...colorProp("cursorColor", theme.primaryText)}
        onInput={onInput}
        onSubmit={(submittedValue) =>
          onSubmit(typeof submittedValue === "string" ? submittedValue : value)
        }
      />
      {shortcutKey ? (
        <text>
          <span {...colorProp("fg", theme.secondaryOnSurface)} {...colorProp("bg", theme.surface4)}>
            {" "}
            {shortcutKey}{" "}
          </span>
          {shortcutDetail ? (
            <span {...colorProp("fg", theme.disabled)}> {shortcutDetail}</span>
          ) : null}
        </text>
      ) : null}
    </box>
  );
}
