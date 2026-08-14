import type { InputRenderable, KeyEvent } from "@opentui/core";
import { useKeyboard, useTerminalDimensions } from "@opentui/react";
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import {
  ApprovalOverlay,
  CommandPalette,
  type CommandPaletteItem,
  ConfigOverlay,
  HelpOverlay,
  type KeyBindingHint,
  LandingScreen,
  type OverlayKind,
  type ShellFocusRegion,
  UiProvider,
  WorkspaceShell,
} from "../components/ui/index.js";
import type { DevKitGateway, ReportExporter } from "../data/ports/index.js";
import { ChartGallery } from "../features/chart-gallery/index.js";
import { ComponentGallery } from "../features/component-gallery/index.js";
import {
  type MigrationFlowState,
  MigrationFlowView,
  useMigrationFlow,
} from "../features/migration-flow/index.js";
import { PatternGallery } from "../features/pattern-gallery/index.js";
import {
  detectTerminalCapabilities,
  layoutForWidth,
  type TerminalCapabilities,
} from "../platform/terminal/index.js";
import { presentationFromFlow } from "./presentation.js";

type AppCommandId =
  | "workspace"
  | "config"
  | "approval"
  | "charts"
  | "components"
  | "patterns"
  | "help";

const BASE_COMMANDS = [
  { id: "workspace", label: "Open workbench", detail: "打开当前迁移任务", shortcut: "Enter" },
  { id: "config", label: "Complete config", detail: "补充 ARM64 构建配置", shortcut: "C" },
  { id: "approval", label: "Review proposal", detail: "审查并确认当前补丁", shortcut: "Ctrl+A" },
  { id: "charts", label: "Chart gallery", detail: "统计图表组件画廊", shortcut: "/chart" },
  {
    id: "components",
    label: "Component gallery",
    detail: "22 个通用组件",
    shortcut: "/components",
  },
  { id: "patterns", label: "Pattern gallery", detail: "P01–P26", shortcut: "/patterns" },
  { id: "help", label: "Keyboard help", detail: "查看完整快捷键", shortcut: "F1" },
] as const satisfies readonly CommandPaletteItem<AppCommandId>[];

export type AppScreen = "landing" | "workbench" | "charts" | "components" | "patterns";

export interface AppProps {
  gateway: DevKitGateway;
  reportExporter?: ReportExporter;
  capabilities?: TerminalCapabilities;
  initialScreen?: AppScreen;
  initialPattern?: number;
  onExit?: () => void;
  onIntent?: (intent: string) => void;
}

function isEscape(key: KeyEvent): boolean {
  return (
    key.name === "escape" || key.name === "esc" || key.sequence === "\u001b" || key.raw === "\u001b"
  );
}

function keyName(key: KeyEvent): string {
  return key.name.toLowerCase();
}

function defaultConfigurationValues(
  state: MigrationFlowState,
): Readonly<Record<string, string | number>> {
  const entries: Array<[string, string | number]> = [];
  for (const field of state.configuration?.fields ?? []) {
    if (field.defaultValue !== undefined) entries.push([field.key, field.defaultValue]);
  }
  return Object.fromEntries(entries);
}

function hintsForFlow(state: MigrationFlowState, width: number): readonly KeyBindingHint[] {
  const common: readonly KeyBindingHint[] = [
    { key: "Ctrl+P", label: "Commands" },
    { key: "Tab", label: "Focus" },
  ];
  const contextual: readonly KeyBindingHint[] =
    state.asyncStatus === "loading"
      ? [{ key: "Esc", label: "Cancel" }]
      : state.asyncStatus === "cancelled" ||
          (state.asyncStatus === "error" && state.error?.retryable === true)
        ? [
            { key: "R", label: "Retry" },
            { key: "Esc", label: "Back" },
          ]
        : state.asyncStatus === "error"
          ? [{ key: "Esc", label: "Back" }]
          : state.act === 2
            ? [
                { key: "M", label: "Modify" },
                { key: "Enter", label: "Execute" },
              ]
            : state.act === 3
              ? [
                  { key: "Enter", label: "Configure" },
                  { key: "S", label: "Skip" },
                ]
              : state.act === 5
                ? [
                    { key: "A", label: "Accept" },
                    { key: "R", label: "Reject" },
                    { key: "B", label: "Build" },
                  ]
                : state.act === 10
                  ? [
                      { key: "S", label: "Export MD" },
                      { key: "J", label: "Export JSON" },
                    ]
                  : [{ key: "Enter", label: "Continue" }];
  return width < 80
    ? [...contextual, { key: "F1", label: "Help" }].slice(0, 4)
    : [...common, ...contextual, { key: "F1", label: "Help" }].slice(0, 6);
}

export function App({
  gateway,
  reportExporter,
  capabilities,
  initialScreen = "landing",
  initialPattern = 0,
  onExit,
  onIntent,
}: AppProps) {
  const terminal = useTerminalDimensions();
  const resolvedCapabilities = useMemo(
    () => capabilities ?? detectTerminalCapabilities(),
    [capabilities],
  );
  const layout = useMemo(() => layoutForWidth(terminal.width), [terminal.width]);
  const { state: flowState, controller: flow } = useMigrationFlow({
    gateway,
    ...(reportExporter ? { reportExporter } : {}),
  });
  const [screen, setScreen] = useState<AppScreen>(initialScreen);
  const returnScreen = useRef<AppScreen>(
    ["charts", "components", "patterns"].includes(initialScreen) ? "workbench" : initialScreen,
  );
  const [overlay, setOverlay] = useState<OverlayKind | null>(null);
  const [overlaySelection, setOverlaySelection] = useState(0);
  const [paletteQuery, setPaletteQuery] = useState("");
  const [focus, setFocus] = useState<ShellFocusRegion>("prompt");
  const [dockTaskIndex, setDockTaskIndex] = useState(0);
  const [prompt, setPrompt] = useState("");
  const [consoleExpanded, setConsoleExpanded] = useState(false);
  const [inspectorVisible, setInspectorVisible] = useState(true);
  const [dockForcedCollapsed, setDockForcedCollapsed] = useState(false);
  const inputRef = useRef<InputRenderable | null>(null);
  const autoOverlayPhase = useRef<string | null>(null);

  useLayoutEffect(() => {
    if (!overlay && focus === "prompt" && screen !== "charts") inputRef.current?.focus();
  }, [focus, overlay, screen]);

  const closeOverlay = useCallback(() => {
    setOverlay(null);
    setOverlaySelection(0);
    setPaletteQuery("");
    setFocus(screen === "landing" ? "prompt" : "canvas");
  }, [screen]);

  const openOverlay = useCallback((kind: OverlayKind) => {
    setOverlay(kind);
    setOverlaySelection(0);
    setPaletteQuery("");
  }, []);

  useEffect(() => {
    if (
      flowState.phase === "config" &&
      flowState.asyncStatus === "ready" &&
      autoOverlayPhase.current !== "config"
    ) {
      autoOverlayPhase.current = "config";
      setScreen("workbench");
      setOverlay("config");
      setOverlaySelection(0);
    }
  }, [flowState.asyncStatus, flowState.phase]);

  const commands = useMemo(
    () =>
      BASE_COMMANDS.map((item) =>
        item.id === "config"
          ? { ...item, disabled: flowState.phase !== "config" }
          : item.id === "approval"
            ? { ...item, disabled: flowState.phase !== "patch-review" }
            : item,
      ),
    [flowState.phase],
  );

  const visibleCommands = useMemo(() => {
    const query = paletteQuery.trim().toLocaleLowerCase();
    return query
      ? commands.filter((item) =>
          `${item.label} ${item.detail} ${item.shortcut}`.toLocaleLowerCase().includes(query),
        )
      : commands;
  }, [commands, paletteQuery]);

  const openGallery = useCallback(() => {
    returnScreen.current = ["charts", "components", "patterns"].includes(screen)
      ? "workbench"
      : screen;
    setOverlay(null);
    setScreen("charts");
    setFocus("canvas");
  }, [screen]);

  const openLibrary = useCallback(
    (target: "components" | "patterns") => {
      returnScreen.current = ["charts", "components", "patterns"].includes(screen)
        ? "workbench"
        : screen;
      setOverlay(null);
      setScreen(target);
      setFocus("canvas");
    },
    [screen],
  );

  const closeGallery = useCallback(() => {
    const next = returnScreen.current === "charts" ? "workbench" : returnScreen.current;
    setScreen(next);
    setFocus(next === "landing" ? "prompt" : "canvas");
  }, []);

  const chooseCommand = useCallback(
    (item: CommandPaletteItem<AppCommandId>) => {
      if (item.disabled) return;
      switch (item.id) {
        case "workspace":
          setScreen("workbench");
          closeOverlay();
          break;
        case "charts":
          openGallery();
          break;
        case "components":
        case "patterns":
          openLibrary(item.id);
          break;
        case "config":
        case "approval":
        case "help":
          openOverlay(item.id);
          break;
      }
    },
    [closeOverlay, openGallery, openLibrary, openOverlay],
  );

  const submitIntent = useCallback(
    (value: string) => {
      const intent = value.trim();
      if (!intent) return;
      if (intent.toLocaleLowerCase() === "/chart") {
        setPrompt("");
        openGallery();
        return;
      }
      if (
        intent.toLocaleLowerCase() === "/components" ||
        intent.toLocaleLowerCase() === "/patterns"
      ) {
        setPrompt("");
        openLibrary(intent.toLocaleLowerCase() === "/components" ? "components" : "patterns");
        return;
      }
      onIntent?.(intent);
      flow.setIntentDraft(intent);
      setPrompt("");
      setScreen("workbench");
      setFocus("canvas");
      void flow.submitIntent();
    },
    [flow, onIntent, openGallery, openLibrary],
  );

  const confirmConfiguration = useCallback(() => {
    const values = defaultConfigurationValues(flowState);
    closeOverlay();
    void flow.submitConfiguration(values);
  }, [closeOverlay, flow, flowState]);

  const skipConfiguration = useCallback(() => {
    closeOverlay();
    void flow.submitConfiguration({}, true);
  }, [closeOverlay, flow]);

  const resolveApproval = useCallback(
    (decision: "approve" | "review" | "reject") => {
      const patch = flowState.patchReview?.patches[flowState.selectedPatchIndex];
      closeOverlay();
      if (decision === "review" || patch === undefined) return;
      void flow.reviewPatch(patch.id, decision === "approve" ? "accepted" : "rejected").then(() => {
        const review = flow.getSnapshot().patchReview;
        const next = review?.patches.findIndex((item) => item.decision === "pending") ?? -1;
        if (next >= 0) flow.selectPatch(next);
      });
    },
    [closeOverlay, flow, flowState.patchReview, flowState.selectedPatchIndex],
  );

  const modifyPlan = useCallback(() => {
    const plan = flowState.plan;
    if (plan === undefined) return;
    const marker = "（含构建脚本）";
    void flow.updatePlan(
      plan.steps.map((step, index) => ({
        id: step.id,
        title:
          index === 1
            ? step.title.endsWith(marker)
              ? step.title.slice(0, -marker.length)
              : `${step.title}${marker}`
            : step.title,
        enabled: true,
      })),
    );
  }, [flow, flowState.plan]);

  const moveRiskSelection = useCallback(
    (delta: number) => {
      const files = flowState.report?.files ?? [];
      if (files.length === 0) return;
      const current = Math.max(
        0,
        files.findIndex((file) => file.path === flowState.selectedRiskFile?.path),
      );
      const next = (current + delta + files.length) % files.length;
      const file = files[next];
      if (file) flow.selectRiskFile(file.path);
    },
    [flow, flowState.report?.files, flowState.selectedRiskFile?.path],
  );

  const movePatchSelection = useCallback(
    (delta: number) => {
      const count = flowState.patchReview?.patches.length ?? 0;
      if (count > 0) flow.selectPatch((flowState.selectedPatchIndex + delta + count) % count);
    },
    [flow, flowState.patchReview?.patches.length, flowState.selectedPatchIndex],
  );

  const moveProfileSelection = useCallback(
    (delta: number) => {
      const profiles = flowState.profiles ?? [];
      if (profiles.length === 0) return;
      const current = Math.max(
        0,
        profiles.findIndex((profile) => profile.id === flowState.selectedProfileId),
      );
      const next = profiles[(current + delta + profiles.length) % profiles.length];
      if (next) flow.selectProfile(next.id);
    },
    [flow, flowState.profiles, flowState.selectedProfileId],
  );

  const focusOrder = useMemo<readonly ShellFocusRegion[]>(
    () =>
      layout.mode === "narrow"
        ? ["tabs", "canvas", "console", "prompt"]
        : ["dock", "tabs", "canvas", "console", "prompt"],
    [layout.mode],
  );

  useKeyboard((key) => {
    const name = keyName(key);
    const escapePressed = isEscape(key);
    if (key.ctrl && name === "c") {
      key.preventDefault();
      onExit?.();
      return;
    }
    if (overlay) {
      if (escapePressed) {
        key.preventDefault();
        closeOverlay();
        return;
      }
      if (name === "down" || name === "j" || name === "up" || name === "k") {
        key.preventDefault();
        const count =
          overlay === "command"
            ? Math.max(1, visibleCommands.length)
            : overlay === "config" || overlay === "approval"
              ? 3
              : 1;
        const delta = name === "down" || name === "j" ? 1 : -1;
        setOverlaySelection((value) => (value + delta + count) % count);
        return;
      }
      if (overlay === "config" && name === "s") {
        key.preventDefault();
        skipConfiguration();
        return;
      }
      if (overlay === "approval" && (name === "a" || name === "r" || name === "n")) {
        key.preventDefault();
        resolveApproval(name === "a" ? "approve" : name === "r" ? "review" : "reject");
        return;
      }
      if (name === "enter" || name === "return") {
        key.preventDefault();
        if (overlay === "command") {
          const command = visibleCommands[overlaySelection];
          if (command) chooseCommand(command);
        } else if (overlay === "config") {
          confirmConfiguration();
        } else if (overlay === "approval") {
          const decisions = ["approve", "review", "reject"] as const;
          resolveApproval(decisions[overlaySelection] ?? "review");
        } else {
          closeOverlay();
        }
      }
      return;
    }
    if (key.ctrl && name === "p") {
      key.preventDefault();
      openOverlay("command");
      return;
    }
    if (name === "f1" || (!key.ctrl && !key.meta && !key.option && key.sequence === "?")) {
      key.preventDefault();
      openOverlay("help");
      return;
    }
    if (screen === "charts" || screen === "components" || screen === "patterns") {
      if (escapePressed) {
        key.preventDefault();
        closeGallery();
      }
      return;
    }
    if (key.ctrl && name === "b" && screen === "workbench") {
      key.preventDefault();
      setDockForcedCollapsed((value) => !value);
      return;
    }
    if (key.ctrl && name === "i" && screen === "workbench") {
      key.preventDefault();
      setInspectorVisible((value) => !value);
      return;
    }
    if (key.ctrl && name === "j" && screen === "workbench") {
      key.preventDefault();
      setConsoleExpanded((value) => !value);
      setFocus("console");
      return;
    }
    if (key.ctrl && name === "a" && flowState.phase === "patch-review") {
      key.preventDefault();
      openOverlay("approval");
      return;
    }
    if (name === "tab" && screen === "workbench") {
      key.preventDefault();
      const current = Math.max(0, focusOrder.indexOf(focus));
      const delta = key.shift ? -1 : 1;
      setFocus(focusOrder[(current + delta + focusOrder.length) % focusOrder.length] ?? "prompt");
      return;
    }
    if (
      screen === "workbench" &&
      focus === "dock" &&
      (name === "down" || name === "j" || name === "up" || name === "k")
    ) {
      key.preventDefault();
      setDockTaskIndex(0);
      return;
    }
    if (escapePressed) {
      key.preventDefault();
      if (flowState.asyncStatus === "loading") {
        flow.cancelCurrent();
      } else if (screen === "workbench") {
        setScreen("landing");
        setFocus("prompt");
      } else {
        onExit?.();
      }
      return;
    }
    const canRetry =
      flowState.asyncStatus === "cancelled" ||
      (flowState.asyncStatus === "error" && flowState.error?.retryable === true);
    if (canRetry && name === "r") {
      key.preventDefault();
      void flow.retry();
      return;
    }
    if (flowState.asyncStatus === "error" || flowState.asyncStatus === "cancelled") return;
    if (screen !== "workbench" || focus !== "canvas" || flowState.asyncStatus === "loading") return;

    const isEnter = name === "enter" || name === "return";
    if (flowState.act === 1 && isEnter) {
      key.preventDefault();
      void flow.submitIntent();
    } else if (flowState.act === 2 && (isEnter || name === "e")) {
      key.preventDefault();
      void flow.executePlan();
    } else if (flowState.act === 2 && name === "m") {
      key.preventDefault();
      modifyPlan();
    } else if (flowState.act === 3 && isEnter) {
      key.preventDefault();
      openOverlay("config");
    } else if (flowState.act === 3 && name === "s") {
      key.preventDefault();
      void flow.submitConfiguration({}, true);
    } else if (
      flowState.act === 4 &&
      (name === "down" || name === "j" || name === "up" || name === "k")
    ) {
      key.preventDefault();
      moveRiskSelection(name === "down" || name === "j" ? 1 : -1);
    } else if (flowState.act === 4 && isEnter) {
      key.preventDefault();
      void flow.openPatchReview();
    } else if (
      flowState.act === 5 &&
      (name === "down" || name === "j" || name === "up" || name === "k" || name === "space")
    ) {
      key.preventDefault();
      movePatchSelection(name === "up" || name === "k" ? -1 : 1);
    } else if (flowState.act === 5 && name === "a") {
      key.preventDefault();
      openOverlay("approval");
    } else if (flowState.act === 5 && name === "r") {
      const patch = flowState.patchReview?.patches[flowState.selectedPatchIndex];
      if (patch) {
        key.preventDefault();
        void flow.reviewPatch(patch.id, "rejected");
      }
    } else if (flowState.act === 5 && name === "b") {
      key.preventDefault();
      void flow.runInitialBuild();
    } else if (flowState.act === 6 && isEnter) {
      key.preventDefault();
      if (flowState.phase === "build-failed") void flow.diagnoseBuild();
      else if (flowState.phase === "diagnosis") void flow.applyFixAndRetryBuild();
      else if (flowState.phase === "build-passed") void flow.collectBaseline();
    } else if (flowState.act === 7 && isEnter) {
      key.preventDefault();
      void flow.compareTuningPlans();
    } else if (flowState.act === 8 && (isEnter || name === "a")) {
      key.preventDefault();
      if (flowState.tuningApplication === undefined) {
        const recommended = flowState.tuning?.plans.find((plan) => plan.recommended);
        if (recommended) void flow.applyTuningPlan(recommended.id);
      } else {
        void flow.openProfiles();
      }
    } else if (flowState.act === 8 && name === "n") {
      key.preventDefault();
      void flow.openProfiles();
    } else if (
      flowState.act === 9 &&
      (name === "down" || name === "j" || name === "up" || name === "k")
    ) {
      key.preventDefault();
      moveProfileSelection(name === "down" || name === "j" ? 1 : -1);
    } else if (flowState.act === 9 && isEnter) {
      key.preventDefault();
      if (flowState.profileResult === undefined) void flow.runSelectedProfile();
      else void flow.finishSession();
    } else if (flowState.act === 10 && name === "s") {
      key.preventDefault();
      void flow.exportSummary("markdown", "reports/nginx-migration.md");
    } else if (flowState.act === 10 && name === "j") {
      key.preventDefault();
      void flow.exportSummary("json", "reports/nginx-migration.json");
    }
  });

  const presentation = useMemo(() => presentationFromFlow(flowState), [flowState]);
  const effectiveDockWidth =
    layout.mode === "narrow"
      ? 0
      : dockForcedCollapsed || !layout.showDockContent
        ? 3
        : layout.dockWidth;
  const effectiveConsoleHeight = layout.consoleHeight + (consoleExpanded ? 3 : 0);
  const canvasWidth = Math.max(1, terminal.width - effectiveDockWidth);
  const canvasHeight = Math.max(1, terminal.height - effectiveConsoleHeight - 8);
  const statusMessage =
    flowState.asyncStatus === "error"
      ? flowState.error?.retryable
        ? `${flowState.error.message} · R 重试`
        : `${flowState.error?.message ?? "Operation failed"} · Esc 返回`
      : flowState.asyncStatus === "loading"
        ? "Loading local workspace…"
        : flowState.asyncStatus === "cancelled"
          ? "Operation cancelled · R 重试"
          : undefined;

  return (
    <UiProvider capabilities={resolvedCapabilities}>
      <box width="100%" height="100%" position="relative">
        {screen === "landing" ? (
          <LandingScreen
            width={terminal.width}
            height={terminal.height}
            value={prompt}
            inputRef={inputRef}
            focused={focus === "prompt" && !overlay}
            {...(statusMessage ? { statusMessage } : {})}
            onInput={setPrompt}
            onSubmit={submitIntent}
            onFocus={() => setFocus("prompt")}
          />
        ) : screen === "charts" ? (
          <ChartGallery
            width={terminal.width}
            height={terminal.height}
            capabilities={resolvedCapabilities}
            onExit={closeGallery}
          />
        ) : screen === "components" ? (
          <ComponentGallery width={terminal.width} height={terminal.height} onExit={closeGallery} />
        ) : screen === "patterns" ? (
          <PatternGallery
            width={terminal.width}
            height={terminal.height}
            initialSelected={initialPattern}
            onExit={closeGallery}
          />
        ) : (
          <WorkspaceShell
            presentation={presentation}
            layout={layout}
            focus={focus}
            dockTaskIndex={dockTaskIndex}
            prompt={prompt}
            inputRef={inputRef}
            consoleExpanded={consoleExpanded}
            inspectorVisible={inspectorVisible}
            dockForcedCollapsed={dockForcedCollapsed}
            canvasContent={
              <MigrationFlowView
                state={flowState}
                actions={flow}
                width={canvasWidth}
                height={canvasHeight}
              />
            }
            keyHints={hintsForFlow(flowState, terminal.width)}
            onFocus={setFocus}
            onSelectTask={() => setDockTaskIndex(0)}
            onPrompt={setPrompt}
            onSubmit={submitIntent}
            onToggleConsole={() => setConsoleExpanded((value) => !value)}
            onOpenHelp={() => openOverlay("help")}
          />
        )}
        {overlay === "command" ? (
          <CommandPalette
            terminalWidth={terminal.width}
            terminalHeight={terminal.height}
            query={paletteQuery}
            items={visibleCommands}
            selected={Math.min(overlaySelection, Math.max(0, visibleCommands.length - 1))}
            onQuery={(value) => {
              setPaletteQuery(value);
              setOverlaySelection(0);
            }}
            onSelect={chooseCommand}
            onClose={closeOverlay}
          />
        ) : null}
        {overlay === "help" ? (
          <HelpOverlay terminalWidth={terminal.width} terminalHeight={terminal.height} />
        ) : null}
        {overlay === "config" ? (
          <ConfigOverlay
            terminalWidth={terminal.width}
            terminalHeight={terminal.height}
            reason={flowState.configuration?.reason ?? "等待当前步骤的配置要求"}
            fields={
              flowState.configuration?.fields.map((field) => ({
                label: field.label,
                value: String(field.defaultValue ?? field.hint ?? ""),
                sensitive: field.sensitive,
              })) ?? []
            }
            selected={overlaySelection}
            onSelect={setOverlaySelection}
            onConfirm={confirmConfiguration}
            onClose={closeOverlay}
          />
        ) : null}
        {overlay === "approval" ? (
          <ApprovalOverlay
            terminalWidth={terminal.width}
            terminalHeight={terminal.height}
            title={`即将${
              flowState.patchReview?.patches[flowState.selectedPatchIndex]?.decision === "pending"
                ? "审查并应用"
                : "重新审查"
            }当前补丁。`}
            scope={
              flowState.patchReview?.patches[flowState.selectedPatchIndex]?.file ?? "当前迁移任务"
            }
            evidence={`${
              flowState.patchReview?.patches[flowState.selectedPatchIndex]?.evidence.length ?? 0
            } 条证据 · 可回滚 · 不执行网络操作`}
            selected={overlaySelection}
            onSelect={setOverlaySelection}
            onResolve={resolveApproval}
          />
        ) : null}
      </box>
    </UiProvider>
  );
}
