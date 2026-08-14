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
          <KunpengBrand />
        </box>
        {activeTab ? (
          <>
            {/* biome-ignore lint/a11y/noStaticElementInteractions: OpenTUI tab has a Tab/Enter keyboard route. */}
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
          </>
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
      alignItems="flex-end"
      paddingLeft={1}
      overflow="hidden"
    >
      {tabs.slice(0, 4).map((tab, index) => {
        const active = tab.id === activeId;
        return (
          // biome-ignore lint/a11y/noStaticElementInteractions: OpenTUI tab has a Tab/Enter keyboard route.
          <box
            key={tab.id}
            height={active ? 3 : 2}
            minWidth={12}
            maxWidth={24}
            paddingX={1}
            flexShrink={1}
            {...colorProp("backgroundColor", active ? theme.background : theme.surface2)}
            border={active ? ["top"] : false}
            {...colorProp("borderColor", active ? theme.primary : theme.borderSubtle)}
            alignItems="center"
            onMouseDown={() => onSelect(tab.id)}
          >
            <text
              wrapMode="none"
              truncate
              {...colorProp("fg", active ? theme.foreground : theme.muted)}
            >
              {tabGlyph(tab.status, capabilities.unicode)} {index + 1} {tab.label}
            </text>
          </box>
        );
      })}
      <box height={2} width={3} flexShrink={0} alignItems="center" justifyContent="center">
        <text {...colorProp("fg", theme.muted)}>＋</text>
      </box>
      <box height={2} flexGrow={1} minWidth={1} justifyContent="flex-end" paddingRight={1}>
        <text wrapMode="none" {...colorProp("fg", theme.muted)}>
          v0.1.0 · Kunpeng ARM64 · <span {...colorProp("fg", theme.success)}>● READY</span>
        </text>
      </box>
    </box>
  );
}
