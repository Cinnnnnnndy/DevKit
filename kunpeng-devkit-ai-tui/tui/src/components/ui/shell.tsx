import type { InputRenderable } from "@opentui/core";
import type { ReactNode, RefObject } from "react";
import type { ShellLayoutMetrics } from "../../platform/terminal/index.js";
import { AgentConsole } from "./agent-console.js";
import { Inspector, MigrationCanvas, PatchCanvas } from "./canvas.js";
import { colorProp } from "./color-props.js";
import { Dock } from "./dock.js";
import { Keybar, StatusBar } from "./keybar.js";
import { PromptBar } from "./prompt-bar.js";
import { TaskTabs } from "./task-tabs.js";
import { useUiEnvironment } from "./theme-context.js";
import type { KeyBindingHint, ShellPresentation } from "./types.js";
export type ShellFocusRegion = "dock" | "tabs" | "canvas" | "console" | "prompt";
export interface WorkspaceShellProps {
  presentation: ShellPresentation;
  layout: ShellLayoutMetrics;
  focus: ShellFocusRegion;
  dockTaskIndex: number;
  prompt: string;
  inputRef?: RefObject<InputRenderable | null>;
  consoleExpanded: boolean;
  inspectorVisible: boolean;
  dockForcedCollapsed: boolean;
  canvasContent?: ReactNode;
  keyHints?: readonly KeyBindingHint[];
  onFocus: (region: ShellFocusRegion) => void;
  onSelectTask: (id: string) => void;
  onPrompt: (value: string) => void;
  onSubmit: (value: string) => void;
  onToggleConsole: () => void;
  onOpenHelp: () => void;
}
const DEFAULT_HINTS: readonly KeyBindingHint[] = [
  { key: "Ctrl+P", label: "Commands" },
  { key: "Tab", label: "Focus" },
  { key: "F1", label: "Help" },
  { key: "Ctrl+B", label: "Dock" },
  { key: "Ctrl+J", label: "Console" },
];
export function WorkspaceShell({
  presentation,
  layout,
  focus,
  dockTaskIndex,
  prompt,
  inputRef,
  consoleExpanded,
  inspectorVisible,
  dockForcedCollapsed,
  canvasContent,
  keyHints = DEFAULT_HINTS,
  onFocus,
  onSelectTask,
  onPrompt,
  onSubmit,
  onToggleConsole,
  onOpenHelp,
}: WorkspaceShellProps) {
  const { theme } = useUiEnvironment();
  const noDock = layout.mode === "narrow";
  const collapsed = dockForcedCollapsed || !layout.showDockContent;
  const showInspector = inspectorVisible && layout.showInspector;
  return (
    <box
      id="workspace-shell"
      width="100%"
      height="100%"
      {...colorProp("backgroundColor", theme.background)}
      flexDirection="column"
      overflow="hidden"
    >
      <box flexGrow={1} minHeight={1} flexDirection="row" overflow="hidden">
        {noDock ? null : (
          <Dock
            width={collapsed ? 3 : layout.dockWidth}
            collapsed={collapsed}
            tasks={presentation.tasks}
            files={presentation.files}
            activeTaskId={presentation.activeTaskId}
            focused={focus === "dock"}
            selectedIndex={dockTaskIndex}
            onSelectTask={onSelectTask}
            onOpenOverlay={onOpenHelp}
          />
        )}
        <box flexGrow={1} minWidth={1} flexDirection="column" overflow="hidden">
          <TaskTabs
            tabs={presentation.tabs}
            activeId={presentation.activeTaskId}
            focused={focus === "tabs"}
            showBrand={noDock}
            onSelect={(id) => {
              onFocus("tabs");
              onSelectTask(id);
            }}
          />
          {/* biome-ignore lint/a11y/noStaticElementInteractions: OpenTUI box receives mouse focus; App provides the equivalent Tab keyboard route. */}
          <box
            flexGrow={1}
            minHeight={1}
            flexDirection="row"
            overflow="hidden"
            onMouseDown={() => onFocus("canvas")}
          >
            {canvasContent ?? (
              <>
                <MigrationCanvas focused={focus === "canvas"} />
                {layout.showSecondaryCanvas ? <PatchCanvas /> : null}
                {showInspector ? <Inspector strip={layout.inspectorStrip} /> : null}
              </>
            )}
          </box>
          <AgentConsole
            events={presentation.consoleEvents}
            height={layout.consoleHeight}
            focused={focus === "console"}
            expanded={consoleExpanded}
            onToggle={() => {
              onFocus("console");
              onToggleConsole();
            }}
          />
          <PromptBar
            value={prompt}
            focused={focus === "prompt"}
            {...(inputRef ? { inputRef } : {})}
            onInput={onPrompt}
            onSubmit={onSubmit}
            onFocus={() => onFocus("prompt")}
          />
        </box>
      </box>
      <Keybar hints={keyHints} />
      <StatusBar
        workspace={presentation.workspace}
        mode={presentation.mode}
        model={presentation.model}
        contextPercent={presentation.contextPercent}
        pending={presentation.tasks.filter((task) => task.status === "waiting").length}
      />
    </box>
  );
}
