export type SemanticTone = "neutral" | "success" | "warning" | "danger" | "accent";

/** 组件在应用终端降级前使用的渲染能力。 */
export type RenderTier = "T0" | "T1" | "T2" | "T3" | "T4";

/** 可复用 UI 组件共享的同步、异步和恢复状态。 */
export type ComponentState =
  | "default"
  | "focused"
  | "selected"
  | "disabled"
  | "loading"
  | "empty"
  | "loaded"
  | "error"
  | "failed"
  | "cancelled";

export type DegradationReason =
  | "no-color"
  | "ansi16"
  | "no-unicode"
  | "no-braille"
  | "no-mouse"
  | "ssh"
  | "reduced-motion"
  | "insufficient-space";

export interface DegradationStep {
  reason: DegradationReason;
  from: RenderTier;
  to: RenderTier;
  /** 降级后仍必须保留的非颜色语义。 */
  preserves: string;
}

/** 从组件首选能力层级到兼容性下限的有序、明确降级路径。 */
export type DegradationPath = readonly DegradationStep[];

export interface ComponentContract {
  tier: RenderTier;
  states: readonly ComponentState[];
  degradation: DegradationPath;
  keyboardEquivalents: readonly string[];
  tokens: readonly string[];
}

export interface TaskTabItem {
  id: string;
  label: string;
  status: "idle" | "running" | "completed" | "waiting" | "failed";
}

export interface DockTaskItem extends TaskTabItem {
  elapsed?: string;
}

export interface DockFileItem {
  id: string;
  label: string;
  depth: number;
  kind: "folder" | "file";
  active?: boolean;
  risk?: 0 | 1 | 2 | 3;
}

export interface ConsoleEventItem {
  id: string;
  label: string;
  detail: string;
  status: "queued" | "running" | "completed" | "warning" | "failed";
}

export interface KeyBindingHint {
  key: string;
  label: string;
}

export interface ShellPresentation {
  workspace: string;
  mode: string;
  model: string;
  contextPercent: number;
  tasks: readonly DockTaskItem[];
  files: readonly DockFileItem[];
  tabs: readonly TaskTabItem[];
  activeTaskId: string;
  consoleEvents: readonly ConsoleEventItem[];
}
