import type { Architecture, IsoDateTime, SessionId, TaskId, TaskStatus } from "./common";

export type CapabilityStatus = "ready" | "missing" | "blocked" | "installing";

export interface DevKitCapability {
  readonly id: string;
  readonly name: string;
  readonly description: string;
  readonly status: CapabilityStatus;
  readonly reason?: string;
}

export interface RecentTask {
  readonly id: TaskId;
  readonly label: string;
  readonly status: TaskStatus;
  readonly updatedAt: IsoDateTime;
  readonly summary: string;
}

export interface WorkspaceBootstrap {
  readonly productName: "Kunpeng DevKit AI";
  readonly binaryName: "devkitai";
  readonly version: string;
  readonly sessionId: SessionId;
  readonly runtimeReady: boolean;
  readonly sourceArchitecture: Architecture;
  readonly targetArchitecture: Architecture;
  readonly capabilities: readonly DevKitCapability[];
  readonly recentTasks: readonly RecentTask[];
  readonly suggestions: readonly string[];
}

export interface InstallCapabilitiesRequest {
  readonly capabilityIds: readonly string[];
}

export interface InstallCapabilitiesResult {
  readonly capabilities: readonly DevKitCapability[];
  readonly installedCount: number;
}
