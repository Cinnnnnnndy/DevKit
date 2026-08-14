import type { ConsoleEventItem, DockFileItem, ShellPresentation } from "../components/ui/index.js";
import type { WorkspaceBootstrap } from "../domain/index.js";
import type {
  MigrationAsyncStatus,
  MigrationFlowState,
  MigrationPhase,
} from "../features/migration-flow/index.js";

export const FALLBACK_PRESENTATION: ShellPresentation = {
  workspace: "local",
  mode: "auto",
  model: "mock",
  contextPercent: 27,
  activeTaskId: "migrate-nginx",
  tasks: [
    { id: "migrate-nginx", label: "migrate nginx", status: "running", elapsed: "38s" },
    { id: "optimize-llm", label: "optimize model", status: "idle" },
    { id: "build-fix", label: "build diagnose", status: "waiting" },
  ],
  tabs: [
    { id: "migrate-nginx", label: "migrate nginx", status: "running" },
    { id: "optimize-llm", label: "optimize", status: "idle" },
  ],
  files: [
    { id: "nginx", label: "nginx/", depth: 0, kind: "folder" },
    { id: "src", label: "src/", depth: 1, kind: "folder" },
    { id: "crypto", label: "crypto.c", depth: 2, kind: "file", active: true, risk: 3 },
    { id: "memory", label: "memory.c", depth: 2, kind: "file", risk: 2 },
    { id: "conf", label: "conf/", depth: 1, kind: "folder" },
  ],
  consoleEvents: [
    { id: "scan", label: "Analyze dependency", detail: "1,204 files · 1.8s", status: "completed" },
    { id: "api", label: "Find incompatible API", detail: "3 issues · 824ms", status: "completed" },
    { id: "patch", label: "Generate patch", detail: "cpp_migrator · 2.1s", status: "completed" },
    { id: "build", label: "Build verify", detail: "3 remaining warnings", status: "warning" },
    { id: "benchmark", label: "Benchmark", detail: "queued", status: "queued" },
  ],
};

function statusFor(
  status: WorkspaceBootstrap["recentTasks"][number]["status"],
): "idle" | "running" | "completed" | "waiting" | "failed" {
  if (status === "paused") return "waiting";
  if (status === "cancelled") return "failed";
  return status;
}

export function presentationFromBootstrap(bootstrap: WorkspaceBootstrap): ShellPresentation {
  const recent = bootstrap.recentTasks.slice(0, 4);
  const tasks = recent.length
    ? recent.map((task) => ({ id: task.id, label: task.label, status: statusFor(task.status) }))
    : FALLBACK_PRESENTATION.tasks;
  const activeTaskId =
    tasks.find((task) => task.status === "running")?.id ??
    tasks[0]?.id ??
    FALLBACK_PRESENTATION.activeTaskId;
  return {
    ...FALLBACK_PRESENTATION,
    mode: bootstrap.runtimeReady ? "auto" : "review",
    model: bootstrap.binaryName,
    tasks,
    tabs: tasks.slice(0, 3),
    activeTaskId,
  };
}

function flowTaskStatus(
  phase: MigrationPhase,
  asyncStatus: MigrationAsyncStatus,
): "running" | "completed" | "waiting" | "failed" {
  if (asyncStatus === "error" || phase === "build-failed") return "failed";
  if (phase === "config") return "waiting";
  if (phase === "summary") return "completed";
  return "running";
}

function flowMode(phase: MigrationPhase): string {
  return phase === "patch-review" || phase === "diagnosis" ? "review" : "auto";
}

function flowFiles(state: MigrationFlowState): readonly DockFileItem[] {
  const reportFiles = state.report?.files ?? [];
  if (reportFiles.length === 0) {
    return [
      {
        id: "project-root",
        label: `${state.intent.sourcePath.replace(/^\.\//, "")}/`,
        depth: 0,
        kind: "folder",
      },
      { id: "project-src", label: "src/", depth: 1, kind: "folder" },
    ];
  }
  return [
    {
      id: "project-root",
      label: `${state.intent.sourcePath.replace(/^\.\//, "")}/`,
      depth: 0,
      kind: "folder",
    },
    ...reportFiles.slice(0, 8).map((file) => ({
      id: `file-${file.path}`,
      label: file.path,
      depth: 1,
      kind: "file" as const,
      active: file.path === state.selectedRiskFile?.path,
      risk: Math.max(0, Math.min(3, Math.floor(file.risk * 4))) as 0 | 1 | 2 | 3,
    })),
  ];
}

function planEventStatus(state: MigrationFlowState, index: number): ConsoleEventItem["status"] {
  if (index === 3 && state.phase === "config") return "warning";
  if (index === 3 && (state.phase === "build-failed" || state.phase === "diagnosis"))
    return "failed";
  if (index === 3 && state.phase === "build-passed") return "completed";
  if (index === 4 && state.act === 7) return "running";
  const completedThrough =
    state.act <= 2 ? -1 : state.act <= 4 ? 1 : state.act === 5 ? 2 : state.act >= 8 ? 4 : 3;
  if (index <= completedThrough) return "completed";
  return "queued";
}

function flowConsoleEvents(state: MigrationFlowState): readonly ConsoleEventItem[] {
  if (state.plan === undefined) {
    return [
      {
        id: "workspace-bootstrap",
        label: state.workspace === undefined ? "Load local workspace" : "Local runtime ready",
        detail: state.pendingOperation ?? "mock gateway · offline-first",
        status:
          state.asyncStatus === "loading"
            ? "running"
            : state.asyncStatus === "error"
              ? "failed"
              : "completed",
      },
    ];
  }
  const events = state.plan.steps.map((step, index) => ({
    id: step.id,
    label: step.title,
    detail: step.tool ?? (index === 3 ? "aarch64 build" : index === 4 ? "profiler" : "queued"),
    status: planEventStatus(state, index),
  }));
  if (state.asyncStatus === "loading" && state.pendingOperation !== undefined) {
    events.push({
      id: `pending-${state.pendingOperation}`,
      label: state.pendingOperation,
      detail: "mock request · Esc cancel",
      status: "running",
    });
  }
  return events;
}

/**
 * Maps the real ten-act controller state to the persistent Style A chrome.
 * App uses this path exclusively; FALLBACK_PRESENTATION remains a shell-only showcase fixture.
 */
export function presentationFromFlow(state: MigrationFlowState): ShellPresentation {
  const taskId = state.plan?.taskId ?? "migration-current";
  const status = flowTaskStatus(state.phase, state.asyncStatus);
  const taskLabel = state.plan?.sourcePath
    ? `migrate ${state.plan.sourcePath.replace(/^\.\//, "")}`
    : "migrate nginx";
  return {
    workspace: "local",
    mode: flowMode(state.phase),
    model: state.workspace?.binaryName ?? "devkitai",
    contextPercent: Math.min(92, 20 + state.act * 6),
    activeTaskId: taskId,
    tasks: [{ id: taskId, label: taskLabel, status }],
    tabs: [{ id: taskId, label: taskLabel, status }],
    files: flowFiles(state),
    consoleEvents: flowConsoleEvents(state),
  };
}
