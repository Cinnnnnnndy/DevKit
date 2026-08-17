import { useCallback, useMemo } from "react";
import { KunpengBrand } from "./brand.js";
import { colorProp } from "./color-props.js";
import { useUiEnvironment } from "./theme-context.js";
import type { TaskTabItem } from "./types.js";

function tabGlyph(status: TaskTabItem["status"], unicode: boolean): string {
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

export function TaskTabs({
  tabs,
  activeId,
  focused,
  showBrand = false,
  onSelect,
}: {
  tabs: readonly TaskTabItem[];
  activeId: string;
  focused: boolean;
  showBrand?: boolean;
  onSelect: (id: string) => void;
}) {
  const { theme, capabilities } = useUiEnvironment();

  const tabOptions = useMemo(
    () =>
      tabs.slice(0, 6).map((tab, index) => ({
        name: `${tabGlyph(tab.status, capabilities.unicode)} ${index + 1} ${tab.label}`,
        description: tab.label,
        value: tab.id,
      })),
    [tabs, capabilities.unicode],
  );

  const handleChange = useCallback(
    (index: number) => {
      const tab = tabs[index];
      if (tab) onSelect(tab.id);
    },
    [tabs, onSelect],
  );

  if (showBrand) {
    const activeTab = tabs.find((tab) => tab.id === activeId) ?? tabs[0];
    return (
      <box
        height={3}
        flexShrink={0}
        {...colorProp("backgroundColor", theme.surface2)}
        border={["bottom"]}
        {...colorProp("borderColor", focused ? theme.borderStrong : theme.borderSubtle)}
        paddingX={1}
        flexDirection="row"
        alignItems="center"
        overflow="hidden"
      >
        <box width={20} flexShrink={0}>
          <KunpengBrand available={20} />
        </box>
        {activeTab ? (
          // biome-ignore lint/a11y/noStaticElementInteractions: OpenTUI tab has a Tab/Enter keyboard route.
          <box
            flexGrow={1}
            minWidth={1}
            {...colorProp("backgroundColor", theme.selected)}
            border={["left"]}
            {...colorProp("borderColor", theme.primary)}
            paddingX={1}
            onMouseDown={() => onSelect(activeTab.id)}
          >
            <text wrapMode="none" truncate {...colorProp("fg", theme.foreground)}>
              {tabGlyph(activeTab.status, capabilities.unicode)} {activeTab.label}
            </text>
          </box>
        ) : null}
        <text flexShrink={0} {...colorProp("fg", theme.success)}>
          {" "}
          ●
        </text>
      </box>
    );
  }

  return (
    <box
      height={3}
      flexShrink={0}
      {...colorProp("backgroundColor", theme.surface2)}
      border={["bottom"]}
      {...colorProp("borderColor", focused ? theme.borderStrong : theme.borderSubtle)}
      flexDirection="row"
      alignItems="center"
      overflow="hidden"
    >
      <tab-select
        flexGrow={1}
        height={3}
        options={tabOptions}
        focused={focused}
        tabWidth={22}
        showDescription={false}
        showUnderline
        showScrollArrows
        wrapSelection
        {...colorProp("backgroundColor", theme.surface2)}
        {...colorProp("textColor", theme.muted)}
        {...colorProp("selectedBackgroundColor", theme.background)}
        {...colorProp("selectedTextColor", theme.foreground)}
        {...colorProp("focusedBackgroundColor", theme.surface3)}
        {...colorProp("focusedTextColor", theme.foreground)}
        onChange={handleChange}
      />
      <box flexShrink={0} paddingRight={1} justifyContent="center">
        <text wrapMode="none" {...colorProp("fg", theme.muted)}>
          v0.1.0 · Kunpeng ARM64 · <span {...colorProp("fg", theme.success)}>● READY</span>
        </text>
      </box>
    </box>
  );
}
